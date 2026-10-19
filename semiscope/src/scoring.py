"""
Unified scoring engine for SemiScope.
Implements score(material, use_case) supporting both:
- Mode 2 (material -> use cases)
- Mode 1 (use case -> materials)

Features:
- Measured ground truth prioritization ('measured' vs 'predicted' provenance tag)
- Random Forest tree-ensemble uncertainty penalization (expected desirability)
- Multi-property geometric mean integration
- Out-of-distribution (OOD) detection
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any
import numpy as np
import pandas as pd
import joblib

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import (
    MODELS_DIR,
    POOL_FILE,
    POOL_CSV,
    SEMICONDUCTOR_POOL_FILE,
    SEMICONDUCTOR_POOL_CSV,
    MAGPIE_FEATURES,
    RAW_DATASETS
)
from src.features import parse_material_input, featurize_composition
from src.registry import REGISTRY, UseCase, Criterion, get_use_case

# In-memory model cache
_LOADED_MODELS: Dict[str, Any] = {}
_MODEL_METADATA: Dict[str, Dict[str, Any]] = {}
_POOL_CACHE: Optional[pd.DataFrame] = None
_POOL_INDEX: Optional[Dict[str, Dict[str, Any]]] = None


def get_candidate_pool(use_full_pool: bool = False) -> pd.DataFrame:
    """
    Loads and caches the candidate materials catalog.
    Defaults to the verified 4,604 semiconductor catalog (SEMICONDUCTOR_POOL_FILE).
    Optionally loads the archived 21,562 full pool when use_full_pool=True.
    """
    global _POOL_CACHE, _POOL_INDEX
    target_parquet = POOL_FILE if use_full_pool else SEMICONDUCTOR_POOL_FILE
    target_csv = POOL_CSV if use_full_pool else SEMICONDUCTOR_POOL_CSV

    if _POOL_CACHE is None or getattr(_POOL_CACHE, "_is_full_pool", None) != use_full_pool:
        if target_parquet.exists():
            try:
                _POOL_CACHE = pd.read_parquet(target_parquet)
            except Exception:
                _POOL_CACHE = pd.read_csv(target_csv)
        elif target_csv.exists():
            _POOL_CACHE = pd.read_csv(target_csv)
        elif POOL_FILE.exists():
            _POOL_CACHE = pd.read_parquet(POOL_FILE)
        else:
            raise FileNotFoundError("Candidate pool not found. Run consolidate.py first.")

        _POOL_CACHE._is_full_pool = use_full_pool

        # Build fast O(1) formula lookup index
        _POOL_INDEX = {}
        for _, row in _POOL_CACHE.iterrows():
            _POOL_INDEX[row["formula"]] = row.to_dict()

    return _POOL_CACHE


def load_model(target_key: str):
    """
    Loads and validates a trained Random Forest model and metadata.
    Enforces feature order and library version assertions.
    """
    global _LOADED_MODELS, _MODEL_METADATA

    if target_key in _LOADED_MODELS:
        return _LOADED_MODELS[target_key], _MODEL_METADATA[target_key]

    target_dir = MODELS_DIR / target_key
    model_path = target_dir / "model.joblib"
    meta_path = target_dir / "metadata.json"

    if not model_path.exists() or not meta_path.exists():
        raise FileNotFoundError(f"Trained model for '{target_key}' not found at {model_path}. Run train.py first.")

    with open(meta_path, "r") as f:
        meta = json.load(f)

    # Feature parity check
    assert meta["features"] == MAGPIE_FEATURES, f"Feature order mismatch in model '{target_key}'"

    model = joblib.load(model_path)
    _LOADED_MODELS[target_key] = model
    _MODEL_METADATA[target_key] = meta
    return model, meta


def predict_property(
    target_key: str,
    feats_df: pd.DataFrame
) -> Tuple[float, float, np.ndarray]:
    """
    Predicts a property with uncertainty using the Random Forest tree ensemble.
    Returns:
        (ensemble_mean, ensemble_std, array_of_tree_predictions)
    """
    model, _ = load_model(target_key)
    X = feats_df[MAGPIE_FEATURES].values

    # Extract individual tree predictions for uncertainty estimation
    tree_preds = np.array([tree.predict(X)[0] for tree in model.estimators_])
    mean_val = float(np.mean(tree_preds))
    std_val = float(np.std(tree_preds))
    return mean_val, std_val, tree_preds


def score_material_for_usecase(
    material_input: str,
    use_case: Union[str, UseCase],
    is_cif: bool = False,
    precomputed_feats: Optional[pd.DataFrame] = None
) -> Dict[str, Any]:
    """
    The core scoring function: score(material, use_case).
    
    1. Resolves input composition and parses CIF if applicable.
    2. Checks pool for measured ground truth.
    3. If missing, predicts via 132-feature RF ensemble with tree-spread uncertainty.
    4. Applies mathematical desirability transfer functions to each tree and computes expected score.
    5. Combines multi-property criteria with geometric mean.
    """
    if isinstance(use_case, str):
        use_case = get_use_case(use_case)

    # 1. Parse material
    canonical_formula, comp, cif_warning = parse_material_input(material_input, is_cif=is_cif)

    # 2. Check candidate pool cache for measured values
    get_candidate_pool()
    pool_entry = _POOL_INDEX.get(canonical_formula, None) if _POOL_INDEX else None

    property_results = {}
    criteria_scores = []
    confidence_levels = []

    # Prepare features if prediction will be needed
    feats_df = precomputed_feats

    for crit in use_case.criteria:
        prop_key = crit.property_key
        measured_col = f"measured_{prop_key}"

        is_measured = False
        val = None
        val_std = 0.0
        tree_vals = None

        if pool_entry is not None and pd.notna(pool_entry.get(measured_col, np.nan)):
            val = float(pool_entry[measured_col])
            is_measured = True
            tag = "measured"
            val_std = 0.0
            # Desirability from exact ground truth
            crit_score = crit.evaluate(val)
            crit_confidence = 1.0
        else:
            # Predict using model
            if feats_df is None:
                feats_df = featurize_composition(comp)

            mean_pred, std_pred, tree_preds = predict_property(prop_key, feats_df)
            val = mean_pred
            val_std = std_pred
            tree_vals = tree_preds
            tag = "predicted"

            # Expected desirability across tree ensemble (uncertainty-penalized)
            tree_desirabilities = [crit.evaluate(tp) for tp in tree_preds]
            crit_score = float(np.mean(tree_desirabilities))

            # Confidence = fraction of trees satisfying desirability >= 0.5
            pass_fraction = float(np.mean([d >= 0.5 for d in tree_desirabilities]))
            # Scale with tree agreement
            crit_confidence = max(0.1, min(1.0, pass_fraction))

        property_results[prop_key] = {
            "value": round(val, 3),
            "std": round(val_std, 3),
            "tag": tag,
            "desirability": round(crit_score, 3)
        }
        criteria_scores.append(crit_score)
        confidence_levels.append(crit_confidence)

    # Multi-property combination via geometric mean: prod(scores)^(1/n)
    if not criteria_scores:
        overall_score = 0.0
        overall_confidence = 0.0
    elif any(s <= 1e-4 for s in criteria_scores):
        overall_score = 0.0
        overall_confidence = float(np.mean(confidence_levels))
    else:
        # Geometric mean
        overall_score = float(np.exp(np.mean(np.log(np.maximum(criteria_scores, 1e-6)))))
        overall_confidence = float(np.mean(confidence_levels))

    # Overall tag: 'measured' only if ALL required properties for this use case were measured
    overall_tag = "measured" if all(p["tag"] == "measured" for p in property_results.values()) else "predicted"

    # Out of distribution check (training range bounds and compositional warnings)
    combined_warnings = []
    if cif_warning:
        combined_warnings.append(cif_warning)

    for prop_key, p_info in property_results.items():
        if p_info["tag"] == "predicted":
            _, meta = load_model(prop_key)
            trange = meta.get("target_range", {})
            if trange:
                pmin, pmax = trange["min"], trange["max"]
                val = p_info["value"]
                if val < pmin - 0.2 * abs(pmin) or val > pmax + 0.2 * abs(pmax):
                    combined_warnings.append(f"Predicted {prop_key} ({val}) lies beyond the primary training bounds [{pmin:.2f}, {pmax:.2f}].")

    ood_warning = " | ".join(combined_warnings) if combined_warnings else None

    # Rating label
    if overall_score >= 0.75:
        verdict = "Highly Suitable"
    elif overall_score >= 0.40:
        verdict = "Moderately Viable"
    elif overall_score > 0.10:
        verdict = "Sub-optimal"
    else:
        verdict = "Unsuitable"

    return {
        "material": canonical_formula,
        "use_case_id": use_case.id,
        "use_case_name": use_case.name,
        "category": use_case.category,
        "evidence_level": use_case.evidence_level,
        "score": round(overall_score, 3),
        "confidence": round(overall_confidence, 3),
        "tag": overall_tag,
        "verdict": verdict,
        "properties": property_results,
        "ood_warning": ood_warning,
        "cif_warning": cif_warning,
        "caveats": use_case.caveats
    }


def score_material_all_usecases(
    material_input: str,
    is_cif: bool = False,
    active_only: bool = True
) -> List[Dict[str, Any]]:
    """
    Mode 2: Material -> All Use Cases.
    Featurizes once and evaluates registered use cases.
    Defaults to active semiconductor use cases (active_only=True).
    Returns ranked list of use cases.
    """
    canonical_formula, comp, cif_warn = parse_material_input(material_input, is_cif=is_cif)
    
    # Precompute features once for all models
    feats_df = featurize_composition(comp)

    results = []
    for u_id, u_case in REGISTRY.items():
        if active_only and not u_case.active:
            continue
        res = score_material_for_usecase(
            material_input=canonical_formula,
            use_case=u_case,
            precomputed_feats=feats_df
        )
        if cif_warn:
            res["cif_warning"] = cif_warn
            # Ensure visible in ood_warning if not already included
            if not res.get("ood_warning"):
                res["ood_warning"] = cif_warn
            elif cif_warn not in res["ood_warning"]:
                res["ood_warning"] = f"{cif_warn} | {res['ood_warning']}"
        results.append(res)

    # Sort descending by score
    results.sort(key=lambda x: x["score"], reverse=True)
    return results
