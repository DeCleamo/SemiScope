"""
Model training and serialization pipeline for SemiScope.
Implements Grouped-K-Fold Cross Validation by chemical system,
trains robust Random Forest ensembles, and serializes models with full metadata.
"""

import sys
import json
import time
from pathlib import Path
from typing import Dict, Any
import numpy as np
import pandas as pd
import joblib
import sklearn
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GroupKFold
from sklearn.metrics import r2_score, mean_absolute_error

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import (
    RAW_DATASETS,
    MAGPIE_FEATURES,
    MODELS_DIR,
    RANDOM_SEED
)
from src.consolidate import load_dataset


def train_and_evaluate_model(
    target_key: str,
    n_estimators: int = 100,
    max_depth: int = 20,
    min_samples_split: int = 4
) -> Dict[str, Any]:
    """
    Trains and evaluates a Random Forest regressor on the specified target using
    Grouped-5-Fold Cross Validation grouped by chemical system (chem_sys).
    Saves the final production model fitted on all clean data along with metadata.
    """
    if target_key not in RAW_DATASETS:
        raise ValueError(f"Unknown target '{target_key}'")

    meta = RAW_DATASETS[target_key]
    target_col = meta["target_col"]
    print(f"\n========================================================")
    print(f"Training Model for: {meta['target_name']} ({target_key})")
    print(f"========================================================")

    # 1. Load data and drop target NaNs
    df = load_dataset(target_key).dropna(subset=[target_col]).reset_index(drop=True)
    X = df[MAGPIE_FEATURES].values
    y = df[target_col].values.astype(float)
    groups = df["chem_sys"].values

    n_samples = len(df)
    n_groups = df["chem_sys"].nunique()
    print(f"Loaded {n_samples} samples across {n_groups} unique chemical systems.")

    # 2. Grouped 5-Fold Cross Validation
    gkf = GroupKFold(n_splits=5)
    r2_scores = []
    mae_scores = []

    print("Running Grouped-5-Fold Cross Validation by chemical system...")
    start_cv = time.time()
    for fold, (train_idx, test_idx) in enumerate(gkf.split(X, y, groups=groups), 1):
        rf_cv = RandomForestRegressor(
            n_estimators=min(n_estimators, 80),
            max_depth=max_depth,
            min_samples_split=min_samples_split,
            n_jobs=-1,
            random_state=RANDOM_SEED + fold
        )
        rf_cv.fit(X[train_idx], y[train_idx])
        preds = rf_cv.predict(X[test_idx])
        r2 = r2_score(y[test_idx], preds)
        mae = mean_absolute_error(y[test_idx], preds)
        r2_scores.append(r2)
        mae_scores.append(mae)
        print(f"  Fold {fold}: R2 = {r2:.4f}, MAE = {mae:.4f}")

    cv_time = time.time() - start_cv
    mean_r2, std_r2 = float(np.mean(r2_scores)), float(np.std(r2_scores))
    mean_mae, std_mae = float(np.mean(mae_scores)), float(np.std(mae_scores))
    print(f"Grouped-CV Results -> R2: {mean_r2:.4f} ± {std_r2:.4f} | MAE: {mean_mae:.4f} ± {std_mae:.4f} (CV time: {cv_time:.1f}s)")

    # 3. Fit final production model on full dataset
    print(f"Fitting final production ensemble (n_estimators={n_estimators}, max_depth={max_depth})...")
    final_rf = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_split=min_samples_split,
        n_jobs=-1,
        random_state=RANDOM_SEED
    )
    final_rf.fit(X, y)

    # 4. Serialize model and metadata
    target_dir = MODELS_DIR / target_key
    target_dir.mkdir(parents=True, exist_ok=True)
    model_path = target_dir / "model.joblib"
    meta_path = target_dir / "metadata.json"

    # Compress model using joblib
    joblib.dump(final_rf, model_path, compress=3)
    file_size_mb = model_path.stat().st_size / (1024 * 1024)
    print(f"Saved model to {model_path} ({file_size_mb:.2f} MB)")

    # Metadata package
    metadata = {
        "target_key": target_key,
        "target_name": meta["target_name"],
        "target_col": target_col,
        "n_samples": n_samples,
        "n_chemical_systems": n_groups,
        "features": MAGPIE_FEATURES,
        "n_features": len(MAGPIE_FEATURES),
        "target_range": {
            "min": float(np.min(y)),
            "max": float(np.max(y)),
            "mean": float(np.mean(y)),
            "std": float(np.std(y))
        },
        "grouped_cv_metrics": {
            "r2_mean": mean_r2,
            "r2_std": std_r2,
            "mae_mean": mean_mae,
            "mae_std": std_mae,
            "r2_folds": r2_scores,
            "mae_folds": mae_scores
        },
        "hyperparameters": {
            "n_estimators": n_estimators,
            "max_depth": max_depth,
            "min_samples_split": min_samples_split,
            "random_state": RANDOM_SEED
        },
        "environment": {
            "sklearn_version": sklearn.__version__,
            "numpy_version": np.__version__,
            "joblib_version": joblib.__version__
        },
        "model_file_size_mb": round(file_size_mb, 2),
        "trained_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"Saved metadata to {meta_path}")

    return metadata


def train_all_models():
    """Trains all 4 models sequentially."""
    configs = {
        "bandgap": {"n_estimators": 100, "max_depth": 20},
        "tc": {"n_estimators": 80, "max_depth": 18},
        "enthalpy": {"n_estimators": 80, "max_depth": 18},
        "zt": {"n_estimators": 60, "max_depth": 14}
    }

    results = {}
    for target_key, cfg in configs.items():
        results[target_key] = train_and_evaluate_model(
            target_key=target_key,
            n_estimators=cfg["n_estimators"],
            max_depth=cfg["max_depth"]
        )

    print("\n========================================================")
    print("ALL MODELS TRAINED & SERIALIZED SUCCESSFULLY!")
    print("========================================================")
    for k, v in results.items():
        cv = v["grouped_cv_metrics"]
        print(f"{k.upper():10s} | R2: {cv['r2_mean']:.4f} ± {cv['r2_std']:.4f} | MAE: {cv['mae_mean']:.4f} | Size: {v['model_file_size_mb']} MB")


if __name__ == "__main__":
    train_all_models()
