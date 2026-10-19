"""
Precomputed candidate pool scorer for SemiScope (Phase 5).
Computes property predictions and use-case compatibility scores across all 21,562 candidate materials
to enable instantaneous (<100ms) Mode 1 candidate retrieval.
"""

import sys
import time
from pathlib import Path
from typing import List, Dict, Optional, Any
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import (
    DATA_DIR,
    POOL_FILE,
    POOL_CSV,
    SEMICONDUCTOR_POOL_FILE,
    SEMICONDUCTOR_POOL_CSV,
    MAGPIE_FEATURES
)
from src.scoring import load_model, get_candidate_pool
from src.registry import REGISTRY

# Primary semiconductor scored catalog (4,604 verified materials)
SCORED_SEMICONDUCTOR_PARQUET = DATA_DIR / "semiconductor_scored.parquet"
SCORED_SEMICONDUCTOR_CSV = DATA_DIR / "semiconductor_scored.csv"

# Archived full pool scored files (21,562 materials)
SCORED_POOL_PARQUET = DATA_DIR / "pool_scored.parquet"
SCORED_POOL_CSV = DATA_DIR / "pool_scored.csv"


def precompute_scored_pool(use_full_pool: bool = False) -> pd.DataFrame:
    """
    Computes band-gap predictions and technological suitability scores across
    the candidate materials catalog. Defaults to the canonical 4,604 semiconductor catalog.
    """
    catalog_name = "full 21.5k candidate pool" if use_full_pool else "canonical 4,604 semiconductor catalog"
    print(f"Loading {catalog_name}...")
    pool = get_candidate_pool(use_full_pool=use_full_pool).copy()
    X = pool[MAGPIE_FEATURES].values

    print(f"Candidate catalog loaded: {len(pool)} materials. Resolving properties...")
    t0 = time.time()

    # 1. Resolve properties (measured ground truth wins; else model prediction)
    # Band gap is primary; optional models resolved if present in catalog
    models_to_run = ["bandgap", "tc", "enthalpy", "zt"] if use_full_pool else ["bandgap"]
    for prop in models_to_run:
        model, _ = load_model(prop)
        pred_col = f"pred_{prop}"
        resolved_col = f"resolved_{prop}"
        tag_col = f"tag_{prop}"

        preds = model.predict(X)
        pool[pred_col] = preds

        measured_col = f"measured_{prop}"
        has_measured = pool[measured_col].notna() if measured_col in pool.columns else pd.Series(False, index=pool.index)

        if measured_col in pool.columns:
            pool[resolved_col] = np.where(has_measured, pool[measured_col], preds)
        else:
            pool[resolved_col] = preds

        pool[tag_col] = np.where(has_measured, "measured", "predicted")

    print(f"Properties resolved in {time.time() - t0:.2f}s. Evaluating use-case criteria...")

    # 2. Score use cases in registry (active use cases for semiconductor catalog)
    for uc_id, uc in REGISTRY.items():
        if not use_full_pool and not uc.active:
            continue

        criteria_scores = []
        is_all_measured = pd.Series(True, index=pool.index)

        for crit in uc.criteria:
            prop_key = crit.property_key
            if f"resolved_{prop_key}" not in pool.columns:
                continue

            vals = pool[f"resolved_{prop_key}"].values
            
            # Vectorized desirability calculation
            ftype = crit.function_type
            p = crit.params

            if ftype == "gaussian":
                x_opt = p["x_opt"]
                sigma = p["sigma"]
                x_min = p.get("x_min", -np.inf)
                x_max = p.get("x_max", np.inf)
                diff = (vals - x_opt) / sigma
                raw_gauss = np.exp(-0.5 * (diff ** 2))
                c_score = np.where((vals <= x_min) | (vals >= x_max) | np.isnan(vals), 0.0, raw_gauss)
            elif ftype == "trapezoid":
                x0, x1, x2, x3 = p["x0"], p["x1"], p["x2"], p["x3"]
                c_score = np.piecewise(
                    vals,
                    [vals <= x0, (vals > x0) & (vals < x1), (vals >= x1) & (vals <= x2), (vals > x2) & (vals < x3), vals >= x3],
                    [0.0, lambda v: (v - x0) / (x1 - x0), 1.0, lambda v: (x3 - v) / (x3 - x2), 0.0]
                )
            elif ftype == "peak":
                x0, x_opt, x1 = p["x0"], p["x_opt"], p["x1"]
                c_score = np.piecewise(
                    vals,
                    [vals <= x0, (vals > x0) & (vals <= x_opt), (vals > x_opt) & (vals < x1), vals >= x1],
                    [0.0, lambda v: (v - x0) / (x_opt - x0), lambda v: (x1 - v) / (x1 - x_opt), 0.0]
                )
            elif ftype == "ramp_up":
                xmin, xmax = p["x_min"], p["x_max"]
                c_score = np.clip((vals - xmin) / (xmax - xmin), 0.0, 1.0)
            elif ftype == "ramp_down":
                xmin, xmax = p["x_min"], p["x_max"]
                c_score = np.clip((xmax - vals) / (xmax - xmin), 0.0, 1.0)
            else:
                c_score = np.zeros_like(vals)

            criteria_scores.append(c_score)
            is_all_measured = is_all_measured & (pool[f"tag_{prop_key}"] == "measured")

        if not criteria_scores:
            continue

        # Multi-property combination via geometric mean
        if len(criteria_scores) == 1:
            overall_score = criteria_scores[0]
        else:
            stacked = np.stack(criteria_scores, axis=0)
            overall_score = np.exp(np.mean(np.log(np.maximum(stacked, 1e-6)), axis=0))

        # Store full unrounded float for scientific ranking and precision
        pool[f"score_{uc_id}"] = overall_score.astype(float)
        pool[f"tag_{uc_id}"] = np.where(is_all_measured, "measured", "predicted")

    print(f"Scoring complete in {time.time() - t0:.2f}s!")

    # 3. Export scored candidate catalog
    target_parquet = SCORED_POOL_PARQUET if use_full_pool else SCORED_SEMICONDUCTOR_PARQUET
    target_csv = SCORED_POOL_CSV if use_full_pool else SCORED_SEMICONDUCTOR_CSV

    try:
        pool.to_parquet(target_parquet, index=False)
        print(f"Saved scored catalog to {target_parquet}")
    except Exception as e:
        print(f"Parquet export failed ({e})")

    pool.to_csv(target_csv, index=False)
    print(f"Saved scored catalog to {target_csv}")

    return pool


def recommend_materials(
    use_case_id: str,
    top_n: int = 15,
    measured_only: bool = False,
    use_full_pool: bool = False
) -> List[Dict]:
    """
    Mode 1: Use Case -> Top N Materials.
    Fast candidate retrieval querying the precomputed semiconductor catalog in <10ms.
    Ranks by unrounded internal score. Identifies exact and display ties explicitly.
    """
    target_parquet = SCORED_POOL_PARQUET if use_full_pool else SCORED_SEMICONDUCTOR_PARQUET
    target_csv = SCORED_POOL_CSV if use_full_pool else SCORED_SEMICONDUCTOR_CSV

    if not target_parquet.exists() and not target_csv.exists():
        precompute_scored_pool(use_full_pool=use_full_pool)

    if target_parquet.exists():
        try:
            pool = pd.read_parquet(target_parquet)
        except Exception:
            pool = pd.read_csv(target_csv)
    else:
        pool = pd.read_csv(target_csv)

    score_col = f"score_{use_case_id}"
    tag_col = f"tag_{use_case_id}"

    if score_col not in pool.columns:
        raise ValueError(f"Use case '{use_case_id}' not found in precomputed catalog.")

    subset = pool.copy()
    if measured_only:
        subset = subset[subset[tag_col] == "measured"]

    # Rank strictly by the unrounded internal score descending
    # Ties in the catalog with identical band gaps produce mathematically identical scores
    top_df = subset.sort_values(by=score_col, ascending=False).head(top_n).copy()

    # Precalculate score occurrences across the full subset to detect ties
    # Rounding to 4 decimal places for scientific tie diagnostics
    subset_rounded_counts = subset[score_col].round(4).value_counts().to_dict()

    results = []
    # Dense rank calculation (shared rank for identical scores)
    current_rank = 1
    prev_unrounded_score = None

    for i, (_, row) in enumerate(top_df.iterrows()):
        unrounded = float(row[score_col])
        rounded_4dp = round(unrounded, 4)
        is_tied = (subset_rounded_counts.get(rounded_4dp, 0) > 1)
        tie_count = subset_rounded_counts.get(rounded_4dp, 1)

        # Dense ranking: candidates with identical scores share the exact same rank
        if prev_unrounded_score is not None and not np.isclose(unrounded, prev_unrounded_score, atol=1e-6):
            current_rank = i + 1
        elif prev_unrounded_score is None:
            current_rank = 1

        prev_unrounded_score = unrounded

        results.append({
            "rank": current_rank,
            "formula": row["formula"],
            "chem_sys": row["chem_sys"],
            "score": unrounded,
            "score_display": round(unrounded, 4),
            "is_tied": is_tied,
            "tie_count": tie_count,
            "tag": row[tag_col],
            "resolved_bandgap": float(row["resolved_bandgap"]) if "resolved_bandgap" in row and pd.notna(row["resolved_bandgap"]) else None,
            "resolved_tc": float(row["resolved_tc"]) if "resolved_tc" in row and pd.notna(row["resolved_tc"]) else None,
            "resolved_enthalpy": float(row["resolved_enthalpy"]) if "resolved_enthalpy" in row and pd.notna(row["resolved_enthalpy"]) else None,
            "resolved_zt": float(row["resolved_zt"]) if "resolved_zt" in row and pd.notna(row["resolved_zt"]) else None
        })

    return results


if __name__ == "__main__":
    precompute_scored_pool(use_full_pool=False)
    print("\n--- Top 5 Semiconductor Candidates for Solar Photovoltaics ---")
    for r in recommend_materials("solar", top_n=5, use_full_pool=False):
        print(f"  {r['formula']:15s} | Score: {r['score']:.3f} | Tag: {r['tag']} | Eg: {r['resolved_bandgap']:.2f} eV")

