"""
Consolidates raw datasets into unified, canonicalized representations
and constructs the ~20,000 material candidate pool.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from pymatgen.core import Composition

# Ensure semiscope package importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import (
    RAW_DATASETS,
    MAGPIE_FEATURES,
    POOL_FILE,
    POOL_CSV
)


def canonicalize_formula(formula_str: str) -> str:
    """Returns the reduced formula string using pymatgen."""
    try:
        return Composition(str(formula_str)).reduced_formula
    except Exception:
        return str(formula_str).strip()


def get_chemical_system(formula_str: str) -> str:
    """Returns the sorted hyphen-delimited chemical system (e.g. 'Fe-O', 'Ba-Cu-O-Y')."""
    try:
        comp = Composition(str(formula_str))
        elements = sorted([el.symbol for el in comp.elements])
        return "-".join(elements)
    except Exception:
        return "Unknown"


def load_dataset(dataset_key: str) -> pd.DataFrame:
    """
    Loads and standardizes any of the raw datasets:
    'bandgap', 'tc', 'enthalpy', 'zt'.
    Returns DataFrame with:
    - 'original_formula'
    - 'reduced_formula'
    - 'chem_sys'
    - target column named after target_col
    - 132 Magpie features
    """
    if dataset_key not in RAW_DATASETS:
        raise ValueError(f"Unknown dataset '{dataset_key}'. Must be one of {list(RAW_DATASETS.keys())}")

    meta = RAW_DATASETS[dataset_key]
    df = pd.read_csv(meta["file"])
    f_col = meta["formula_col"]
    t_col = meta["target_col"]

    df["original_formula"] = df[f_col].astype(str)
    df["reduced_formula"] = df["original_formula"].apply(canonicalize_formula)
    df["chem_sys"] = df["reduced_formula"].apply(get_chemical_system)

    # Standardize column structure
    cols = ["original_formula", "reduced_formula", "chem_sys", t_col] + MAGPIE_FEATURES
    return df[cols].copy()


def build_candidate_pool() -> pd.DataFrame:
    """
    Constructs the consolidated candidate pool from the union of all 4 datasets.
    Aggregates measured values across duplicate canonical compositions and preserves
    the 132 Magpie feature descriptors for fast candidate scoring.
    """
    print("Building candidate pool from 4 datasets...")
    pool_records = {}  # reduced_formula -> dict of properties & features

    for name in ["bandgap", "tc", "enthalpy", "zt"]:
        meta = RAW_DATASETS[name]
        df = load_dataset(name)
        t_col = meta["target_col"]
        print(f"Processing '{name}': {len(df)} rows...")

        for _, row in df.iterrows():
            formula = row["reduced_formula"]
            target_val = row[t_col]
            chem_sys = row["chem_sys"]

            if formula not in pool_records:
                record = {
                    "formula": formula,
                    "chem_sys": chem_sys,
                    "_measured_vals": {
                        "measured_bandgap": [],
                        "measured_tc": [],
                        "measured_enthalpy": [],
                        "measured_zt": []
                    },
                    "sources": set(),
                }
                # store the 132 Magpie features from the first encounter
                for feat in MAGPIE_FEATURES:
                    record[feat] = row[feat]
                pool_records[formula] = record

            rec = pool_records[formula]
            rec["sources"].add(name)

            if pd.notna(target_val):
                target_map = {
                    "bandgap": "measured_bandgap",
                    "tc": "measured_tc",
                    "enthalpy": "measured_enthalpy",
                    "zt": "measured_zt"
                }
                rec["_measured_vals"][target_map[name]].append(float(target_val))

    # Convert to DataFrame
    rows = []
    for f, rec in pool_records.items():
        rec_copy = rec.copy()
        # Compute proper arithmetic mean across all accumulated measurements
        for prop_name, vals in rec["_measured_vals"].items():
            rec_copy[prop_name] = float(np.mean(vals)) if len(vals) > 0 else np.nan
        del rec_copy["_measured_vals"]
        rec_copy["sources"] = ",".join(sorted(rec_copy["sources"]))
        rows.append(rec_copy)

    pool_df = pd.DataFrame(rows)
    # Sort by formula
    pool_df.sort_values(by="formula", inplace=True)
    pool_df.reset_index(drop=True, inplace=True)

    print(f"Consolidation complete! Total unique candidate materials: {len(pool_df)}")
    print(f"Measured bandgap count: {pool_df['measured_bandgap'].notna().sum()}")
    print(f"Measured tc count: {pool_df['measured_tc'].notna().sum()}")
    print(f"Measured enthalpy count: {pool_df['measured_enthalpy'].notna().sum()}")
    print(f"Measured zt count: {pool_df['measured_zt'].notna().sum()}")

    # Save to parquet and csv
    try:
        pool_df.to_parquet(POOL_FILE, index=False)
        print(f"Saved candidate pool to {POOL_FILE}")
    except Exception as e:
        print(f"Parquet export failed ({e}), relying on CSV.")
    
    pool_df.to_csv(POOL_CSV, index=False)
    print(f"Saved candidate pool to {POOL_CSV}")

    return pool_df


def build_semiconductor_catalog() -> pd.DataFrame:
    """
    Constructs the canonical semiconductor candidate catalog from the verified 4,604-record
    semiconductor dataset. Preserves all 132 Magpie feature descriptors and experimental band gaps.
    """
    from src.config import SEMICONDUCTOR_POOL_FILE, SEMICONDUCTOR_POOL_CSV

    print("Building canonical semiconductor candidate catalog (4,604 materials)...")
    df = load_dataset("bandgap")

    catalog_records = []
    for _, row in df.iterrows():
        formula = row["reduced_formula"]
        chem_sys = row["chem_sys"]
        bg = row["BandGap_eV"]

        rec = {
            "formula": formula,
            "chem_sys": chem_sys,
            "measured_bandgap": float(bg) if pd.notna(bg) else np.nan,
            "sources": "bandgap"
        }
        for feat in MAGPIE_FEATURES:
            rec[feat] = row[feat]
        catalog_records.append(rec)

    catalog_df = pd.DataFrame(catalog_records)
    catalog_df.sort_values(by="formula", inplace=True)
    catalog_df.reset_index(drop=True, inplace=True)

    print(f"Semiconductor catalog complete! Total verified materials: {len(catalog_df)}")
    print(f"Experimental bandgap measurements: {catalog_df['measured_bandgap'].notna().sum()}")

    try:
        catalog_df.to_parquet(SEMICONDUCTOR_POOL_FILE, index=False)
        print(f"Saved semiconductor catalog to {SEMICONDUCTOR_POOL_FILE}")
    except Exception as e:
        print(f"Parquet export failed ({e}), relying on CSV.")

    catalog_df.to_csv(SEMICONDUCTOR_POOL_CSV, index=False)
    print(f"Saved semiconductor catalog to {SEMICONDUCTOR_POOL_CSV}")

    return catalog_df


if __name__ == "__main__":
    build_semiconductor_catalog()

