# SemiScope Phase 2C: Validation Protocol

## 1. Scope & Objective
This protocol establishes the scientific requirements, integrity gates, and reproducibility procedures for validating the SemiScope production Random Forest band-gap prediction model against the curated Phase 2C external reference benchmark (`validation_results/phase2c/reference_benchmark.csv`).

---

## 2. Model Freeze & Isolation Rules
1. **Model Invariance:** The production model artifact (`models/bandgap/model.joblib`), metadata (`models/bandgap/metadata.json`), feature definitions (`src/magpie_features.json`), and training pool (`data/raw/matbench_expt_gap_renamed.csv`) are strictly frozen. No retraining, fine-tuning, or hyperparameter updates are permitted.
2. **Feature Generation Isolation:** Featurization must run exclusively through the production pipeline (`src.features.featurize_composition`), using the 132 Magpie elemental composition descriptors without modification.
3. **No Inference Overrides:** Benchmark reference values must never be hardcoded into inference routes or substituted as runtime lookups.
4. **Holdout Non-Contamination:** No record in `reference_benchmark.csv` may be merged into training data, feature selection, or validation tuning loops.

---

## 3. Scientific Benchmark Curation Rules
1. **Evidence Quality Standard:**
   - **`verified_primary`:** Original experimental publication directly inspected, DOI resolved and confirmed to the cited paper, numerical value located in specific table/page/figure, and measurement conditions (300 K, phase, single crystal) documented.
   - **`verified_secondary`:** Authoritative compilations (Landolt-Börnstein, CRC Handbook) where the primary measurement has consensus but original paper was not directly verified.
   - **`provisional` / `unresolved`:** Segregated into `excluded_records.csv` and strictly barred from primary evaluation metrics.
2. **Measurement Standardization:**
   - Temperature standardized to **300 K (ambient room temperature)**.
   - Values reported in **electron volts (eV)**.
   - Phase/polymorph explicitly recorded with space group symmetry (e.g., Rutile $P4_2/mnm$ vs Anatase $I4_1/amd$).
3. **Challenge Set Separation:**
   - Single-element materials (`Si`, `Ge`, `C`) must be flagged as `elemental_challenge` and evaluated separately from multielement compounds to account for descriptor degeneracy in single-element systems.

---

## 4. Evaluation & Subgroup Stratification Procedure
1. **Primary Metric Cohort:** Evaluated on the eligible in-domain multielement compounds ($n=51$).
2. **Elemental Challenge Cohort:** Evaluated separately on pure elemental semiconductors ($n=3$).
3. **Energy Range Subgroups:**
   - Narrow band gap: $E_g < 1.5\text{ eV}$ ($n=14$)
   - Conventional band gap: $1.5\text{ eV} \le E_g \le 3.0\text{ eV}$ ($n=19$)
   - Wide / Ultrawide band gap: $E_g > 3.0\text{ eV}$ ($n=18$)
4. **Metrics Reported:**
   - Mean Absolute Error (MAE)
   - Root Mean Squared Error (RMSE)
   - Mean Signed Error (Bias: $\text{prediction} - \text{reference}$)
   - Median Absolute Error
   - Mean Ensemble Tree Dispersion ($\sigma_{\text{trees}}$)

---

## 5. Automated Verification & Non-Regression Execution
Validation scripts must be executed via Python 3.13:
```bash
/Library/Frameworks/Python.framework/Versions/3.13/bin/python3 validation_results/phase2c/verify_benchmark_integrity.py
```
Verification checks confirm:
- 0 missing record IDs or values.
- 100% DOI resolution to authentic publications.
- 0 provisional/unresolved records in `reference_benchmark.csv`.
- Complete agreement between manifest hashes and generated files.
- Identical float metrics reproduced deterministically.
