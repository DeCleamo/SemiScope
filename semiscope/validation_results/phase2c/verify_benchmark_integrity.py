#!/usr/bin/env python3
"""
SemiScope Phase 2C: Automated Benchmark Integrity Verification Script
-----------------------------------------------------------------------
Verifies:
1. Production model and training dataset freeze (SHA-256 invariance).
2. Reference benchmark completeness (record counts, non-empty fields, positive gaps).
3. Evidence tier purity (0 provisional/unresolved records in primary benchmark).
4. Automated recomputation of metrics directly from record-level errors.
5. Deterministic agreement with benchmark_integrity_checks.json and benchmark_manifest.json.
"""

import sys
import json
import hashlib
from pathlib import Path
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PHASE2C_DIR = REPO_ROOT / "validation_results" / "phase2c"

FROZEN_HASHES = {
    "models/bandgap/model.joblib": "44e961abfe07a9a11a9b895430cdf3943fa53caef8408a201cf883c7b95cdaaf",
    "models/bandgap/metadata.json": "0e265628b740713339bc32cf9826b0235f48a5fe133e69724806efba38ea32b0",
    "src/magpie_features.json": "3c6c36e7696df28f266290de860394b3cefb96001ea27672be94cb4f57101195",
    "data/raw/matbench_expt_gap_renamed.csv": "9d0b44f68a867ae8e55a38828390cd80e16ddbb884a483682dda1078df09ceb5"
}

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def test_model_freeze():
    print("[CHECK 1] Testing production model and training dataset freeze...")
    for rel_path, expected_hash in FROZEN_HASHES.items():
        p = REPO_ROOT / rel_path
        assert p.exists(), f"Missing frozen production file: {rel_path}"
        actual_hash = sha256_file(p)
        assert actual_hash == expected_hash, f"Hash mismatch on frozen artifact {rel_path}: got {actual_hash}, expected {expected_hash}"
    print("  -> PASSED: All production models, schemas, and training datasets are strictly unmodified.")

def test_benchmark_schema_and_purity():
    print("[CHECK 2] Testing benchmark schema, record count, and evidence purity...")
    bm_path = PHASE2C_DIR / "reference_benchmark.csv"
    assert bm_path.exists(), "reference_benchmark.csv missing!"
    df = pd.read_csv(bm_path)
    
    # Target >= 50 eligible records
    assert len(df) >= 50, f"Benchmark has only {len(df)} records, expected >= 50"
    assert len(df) == 54, f"Expected 54 records, found {len(df)}"
    
    # Required columns check
    req_cols = [
        'record_id', 'formula', 'normalized_formula', 'phase_or_structure', 'crystal_system',
        'single_crystal_status', 'band_gap_eV', 'gap_type', 'measurement_method',
        'temperature_K', 'pressure_or_conditions', 'source_title', 'authors', 'journal',
        'publication_year', 'doi', 'doi_url', 'source_url', 'source_page_or_table',
        'evidence_tier', 'verification_status', 'eligibility_status', 'domain_group',
        'exclusion_reason', 'curation_notes'
    ]
    for c in req_cols:
        assert c in df.columns, f"Missing required column in benchmark: {c}"
        
    # Check for duplicate record IDs
    assert df['record_id'].is_unique, "Duplicate record_id found in reference_benchmark.csv"
    assert (df['band_gap_eV'] > 0).all(), "Non-positive band gap value found!"
    assert (df['temperature_K'] == 300).all(), "Non-standard temperature found!"
    
    # Purity: NO provisional or unresolved records in primary benchmark
    forbidden_tiers = ['provisional', 'unresolved']
    bad_records = df[df['evidence_tier'].isin(forbidden_tiers)]
    assert len(bad_records) == 0, f"Found {len(bad_records)} unverified/provisional records in primary benchmark!"
    
    # Check excluded_records.csv
    ex_path = PHASE2C_DIR / "excluded_records.csv"
    assert ex_path.exists(), "excluded_records.csv missing!"
    df_ex = pd.read_csv(ex_path)
    assert len(df_ex) == 12, f"Expected 12 excluded records, found {len(df_ex)}"
    assert (df_ex['eligibility_status'] == 'excluded').all(), "Non-excluded record in excluded_records.csv!"
    assert (df_ex['exclusion_reason'] != "").all(), "Missing exclusion reason in excluded_records.csv!"
    
    # Check reference_source_audit.csv
    audit_path = PHASE2C_DIR / "reference_source_audit.csv"
    assert audit_path.exists(), "reference_source_audit.csv missing!"
    df_audit = pd.read_csv(audit_path)
    assert len(df_audit) == 66, f"Expected 66 total audited records, found {len(df_audit)}"
    
    print(f"  -> PASSED: Benchmark schema valid ({len(df)} eligible verified records, {len(df_ex)} excluded records).")

def test_metrics_recomputation():
    print("[CHECK 3] Independently recomputing metrics from record-level evaluation CSV...")
    eval_path = PHASE2C_DIR / "model_evaluation_results.csv"
    assert eval_path.exists(), "model_evaluation_results.csv missing!"
    df_eval = pd.read_csv(eval_path)
    assert len(df_eval) == 54, f"Expected 54 evaluation rows, got {len(df_eval)}"
    
    # Recompute overall
    mae_overall = float(np.mean(df_eval['absolute_error_eV']))
    rmse_overall = float(np.sqrt(np.mean(df_eval['squared_error_eV2'])))
    bias_overall = float(np.mean(df_eval['signed_error_eV']))
    med_overall = float(np.median(df_eval['absolute_error_eV']))
    
    # Recompute in-domain multielement
    df_in = df_eval[df_eval['domain_group'] == 'in_domain_multielement']
    assert len(df_in) == 51, f"Expected 51 in-domain records, got {len(df_in)}"
    mae_in = float(np.mean(df_in['absolute_error_eV']))
    rmse_in = float(np.sqrt(np.mean(df_in['squared_error_eV2'])))
    bias_in = float(np.mean(df_in['signed_error_eV']))
    med_in = float(np.median(df_in['absolute_error_eV']))
    
    # Load JSON metrics
    json_path = PHASE2C_DIR / "benchmark_integrity_checks.json"
    with open(json_path, "r") as f:
        data = json.load(f)
        
    m_all = data['overall_benchmark_metrics']
    assert round(mae_overall, 4) == m_all['mae_eV'], "MAE mismatch on overall"
    assert round(rmse_overall, 4) == m_all['rmse_eV'], "RMSE mismatch on overall"
    assert round(bias_overall, 4) == m_all['mean_signed_error_eV'], "Bias mismatch on overall"
    assert round(med_overall, 4) == m_all['median_absolute_error_eV'], "Median mismatch on overall"
    
    m_in = data['in_domain_multielement_metrics']
    assert round(mae_in, 4) == m_in['mae_eV'], "MAE mismatch on in-domain"
    assert round(rmse_in, 4) == m_in['rmse_eV'], "RMSE mismatch on in-domain"
    assert round(bias_in, 4) == m_in['mean_signed_error_eV'], "Bias mismatch on in-domain"
    assert round(med_in, 4) == m_in['median_absolute_error_eV'], "Median mismatch on in-domain"
    
    print(f"  -> PASSED: Metrics independently verified against record-level calculations.")
    print(f"     Overall (n=54): MAE={mae_overall:.4f} eV, RMSE={rmse_overall:.4f} eV, Bias={bias_overall:.4f} eV")
    print(f"     In-Domain (n=51): MAE={mae_in:.4f} eV, RMSE={rmse_in:.4f} eV, Bias={bias_in:.4f} eV")

def test_manifest_agreement():
    print("[CHECK 4] Verifying agreement between benchmark manifest and physical files...")
    man_path = PHASE2C_DIR / "benchmark_manifest.json"
    assert man_path.exists(), "benchmark_manifest.json missing!"
    with open(man_path, "r") as f:
        manifest = json.load(f)
        
    for fname, exp_hash in manifest['file_hashes_sha256'].items():
        fp = PHASE2C_DIR / fname
        assert fp.exists(), f"File listed in manifest does not exist: {fname}"
        actual = sha256_file(fp)
        assert actual == exp_hash, f"Manifest hash mismatch for {fname}: got {actual}, expected {exp_hash}"
    print("  -> PASSED: All file hashes agree 100% with benchmark manifest.")

def main():
    print("=" * 70)
    print("SEMISCOPE PHASE 2C: AUTOMATED BENCHMARK INTEGRITY SUITE")
    print("=" * 70)
    test_model_freeze()
    test_benchmark_schema_and_purity()
    test_metrics_recomputation()
    test_manifest_agreement()
    print("=" * 70)
    print("ALL INTEGRITY CHECKS PASSED SUCCESSFULLY (0 ERRORS).")
    print("=" * 70)

if __name__ == "__main__":
    main()
