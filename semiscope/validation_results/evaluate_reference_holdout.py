#!/usr/bin/env python3
"""
SemiScope Phase 2: Standalone Reproducible External Reference Validation Script
---------------------------------------------------------------------------------
Evaluates the production Random Forest band-gap model against the expanded external
reference dataset (semiscope_reference_bandgaps_expanded.csv) without modifying
any production code, retrained models, or feature schemas.

Output:
- validation_results/reference_source_audit.csv
- validation_results/external_validation_results.csv
- validation_results/validation_metrics.json
"""

import sys
import json
import hashlib
from pathlib import Path
import numpy as np
import pandas as pd
import joblib

# Ensure semiscope package can be imported in standalone execution
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.features import featurize_composition, parse_material_input

VALIDATION_DIR = REPO_ROOT / "validation_results"
REFERENCE_CSV = VALIDATION_DIR / "semiscope_reference_bandgaps_expanded.csv"
MODEL_PATH = REPO_ROOT / "models" / "bandgap" / "model.joblib"
METADATA_PATH = REPO_ROOT / "models" / "bandgap" / "metadata.json"

def calculate_sha256(filepath: Path) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def main():
    print(f"Loading reference dataset: {REFERENCE_CSV}")
    ref_df = pd.read_csv(REFERENCE_CSV)
    ref_sha256 = calculate_sha256(REFERENCE_CSV)
    print(f"Dataset SHA256: {ref_sha256}")

    print(f"Loading production model: {MODEL_PATH}")
    model = joblib.load(MODEL_PATH)
    
    with open(METADATA_PATH, "r") as f:
        meta = json.load(f)

    # 1. Audit Table Generation
    audit_rows = []
    eval_rows = []

    for idx, row in ref_df.iterrows():
        rid = idx + 1
        formula = str(row["formula"]).strip()
        ref_bg = float(row["bandgap_eV"])
        phase = row.get("phase", "")
        temp_k = row.get("temperature_K", 300)
        gap_type = row.get("gap_type", "")
        method = row.get("measurement_method", "")
        quality = row.get("evidence_quality", "provisional")
        bib_ref = row.get("source_title", "")
        doi = row.get("doi_or_citation", "")
        notes = row.get("notes", "")

        # Domain & formula check via production feature pipeline
        try:
            reduced_form, comp_obj, warn = parse_material_input(formula)
            canonical_form = comp_obj.reduced_formula
            is_valid = True
            if len(comp_obj.elements) == 1:
                is_in_domain = False
                domain_status = "out_of_domain_elemental"
            else:
                is_in_domain = True
                domain_status = "in_domain_multielement"
            warning_msg = warn or "None"
        except Exception as e:
            canonical_form = formula
            is_valid = False
            is_in_domain = False
            domain_status = "unsupported_input"
            warning_msg = str(e)

        # Classification / Exclusion rules
        # Exclude unresolved discrepancies from primary metrics
        if quality == "unresolved":
            eligibility = "excluded"
            exclusion_reason = "Unresolved literature dispute: optical absorption edge vs fundamental dipole-forbidden gap"
        else:
            eligibility = "eligible"
            exclusion_reason = "None"

        audit_rows.append({
            "record_id": rid,
            "formula": formula,
            "canonical_formula": canonical_form,
            "phase": phase,
            "temperature_K": temp_k,
            "gap_type": gap_type,
            "measurement_method": method,
            "evidence_quality": quality,
            "primary_reference": bib_ref,
            "doi": doi,
            "notes": notes,
            "eligibility_status": eligibility,
            "exclusion_reason": exclusion_reason,
            "domain_status": domain_status,
            "is_in_domain": is_in_domain
        })

        # Feature extraction & Model prediction
        feat_df = featurize_composition(formula)
        X = feat_df.values
        pred_bg = float(model.predict(X)[0])

        # Tree ensemble dispersion
        tree_preds = np.array([tree.predict(X)[0] for tree in model.estimators_])
        tree_std = float(np.std(tree_preds))
        tree_min = float(np.min(tree_preds))
        tree_max = float(np.max(tree_preds))

        signed_err = pred_bg - ref_bg
        abs_err = abs(signed_err)
        sq_err = signed_err ** 2

        eval_rows.append({
            "record_id": rid,
            "formula": formula,
            "canonical_formula": canonical_form,
            "phase": phase,
            "temperature_K": temp_k,
            "gap_type": gap_type,
            "evidence_quality": quality,
            "eligibility_status": eligibility,
            "domain_status": domain_status,
            "is_in_domain": is_in_domain,
            "reference_bandgap_eV": round(ref_bg, 3),
            "predicted_bandgap_eV": round(pred_bg, 3),
            "signed_error_eV": round(signed_err, 3),
            "absolute_error_eV": round(abs_err, 3),
            "squared_error_eV2": round(sq_err, 4),
            "tree_dispersion_std_eV": round(tree_std, 3),
            "tree_min_eV": round(tree_min, 3),
            "tree_max_eV": round(tree_max, 3),
            "warning_flag": warning_msg
        })

    audit_df = pd.DataFrame(audit_rows)
    eval_df = pd.DataFrame(eval_rows)

    audit_out_path = VALIDATION_DIR / "reference_source_audit.csv"
    eval_out_path = VALIDATION_DIR / "external_validation_results.csv"
    audit_df.to_csv(audit_out_path, index=False)
    eval_df.to_csv(eval_out_path, index=False)
    print(f"Saved audit output to: {audit_out_path}")
    print(f"Saved evaluation output to: {eval_out_path}")

    # Compute holdout metrics on eligible subset
    eligible_df = eval_df[eval_df["eligibility_status"] == "eligible"]
    in_domain_df = eligible_df[eligible_df["domain_status"] == "in_domain_multielement"]
    elemental_df = eligible_df[eligible_df["domain_status"] == "out_of_domain_elemental"]

    def calc_metrics(df_subset):
        if len(df_subset) == 0:
            return {}
        abs_errs = df_subset["absolute_error_eV"].values
        signed_errs = df_subset["signed_error_eV"].values
        sq_errs = df_subset["squared_error_eV2"].values
        stds = df_subset["tree_dispersion_std_eV"].values

        mae = float(np.mean(abs_errs))
        rmse = float(np.sqrt(np.mean(sq_errs)))
        bias = float(np.mean(signed_errs))
        med_ae = float(np.median(abs_errs))
        mean_std = float(np.mean(stds))
        
        corr = None
        if len(df_subset) > 2 and np.std(stds) > 1e-6 and np.std(abs_errs) > 1e-6:
            corr = float(np.corrcoef(abs_errs, stds)[0, 1])

        return {
            "count": int(len(df_subset)),
            "mae_eV": round(mae, 4),
            "rmse_eV": round(rmse, 4),
            "mean_signed_error_eV": round(bias, 4),
            "median_absolute_error_eV": round(med_ae, 4),
            "mean_tree_dispersion_eV": round(mean_std, 4),
            "abs_error_vs_dispersion_pearson_r": round(corr, 4) if corr is not None else None
        }

    overall_metrics = calc_metrics(eligible_df)
    in_domain_metrics = calc_metrics(in_domain_df)
    elemental_metrics = calc_metrics(elemental_df)

    # Diagnostic cases extraction
    diag_keys = ["Si", "Ge", "GaAs", "CdTe", "InP"]
    diag_results = {}
    for k in diag_keys:
        match = eval_df[eval_df["formula"] == k]
        if not match.empty:
            r = match.iloc[0].to_dict()
            disp_ratio = round(r["tree_dispersion_std_eV"] / r["absolute_error_eV"], 3) if r["absolute_error_eV"] > 0 else None
            diag_results[k] = {
                "record_id": int(r["record_id"]),
                "formula": r["formula"],
                "canonical_formula": r["canonical_formula"],
                "phase": r["phase"],
                "temperature_K": int(r["temperature_K"]),
                "gap_type": r["gap_type"],
                "evidence_quality": r["evidence_quality"],
                "eligibility_status": r["eligibility_status"],
                "domain_status": r["domain_status"],
                "reference_bandgap_eV": float(r["reference_bandgap_eV"]),
                "predicted_bandgap_eV": float(r["predicted_bandgap_eV"]),
                "signed_error_eV": float(r["signed_error_eV"]),
                "absolute_error_eV": float(r["absolute_error_eV"]),
                "squared_error_eV2": float(r["squared_error_eV2"]),
                "uncalibrated_tree_dispersion_std_eV": float(r["tree_dispersion_std_eV"]),
                "tree_min_eV": float(r["tree_min_eV"]),
                "tree_max_eV": float(r["tree_max_eV"]),
                "dispersion_error_ratio": disp_ratio,
                "warning_flag": r["warning_flag"]
            }

    metrics_payload = {
        "evaluation_metadata": {
            "evaluation_date": "2026-10-19",
            "dataset_name": REFERENCE_CSV.name,
            "dataset_sha256": ref_sha256,
            "model_artifact": "models/bandgap/model.joblib",
            "model_version_trained_timestamp": meta.get("trained_timestamp", ""),
            "feature_count": meta.get("feature_count", 132),
            "sklearn_runtime_version": "1.8.0",
            "sklearn_serialized_version": meta.get("sklearn_version", "1.9.0")
        },
        "dataset_partition_counts": {
            "total_evaluated_records": int(len(eval_df)),
            "eligible_records": int(len(eligible_df)),
            "excluded_unresolved_records": int(len(eval_df) - len(eligible_df)),
            "eligible_in_domain_records": int(len(in_domain_df)),
            "eligible_out_of_domain_elemental_records": int(len(elemental_df))
        },
        "overall_eligible_metrics": overall_metrics,
        "in_domain_multielement_metrics": in_domain_metrics,
        "out_of_domain_elemental_metrics": elemental_metrics,
        "diagnostic_cases": diag_results
    }

    metrics_out_path = VALIDATION_DIR / "validation_metrics.json"
    with open(metrics_out_path, "w") as f:
        json.dump(metrics_payload, f, indent=2)
    print(f"Saved validation metrics JSON to: {metrics_out_path}")
    print("Execution completed successfully.")

if __name__ == "__main__":
    main()
