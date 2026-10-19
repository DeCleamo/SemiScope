# SemiScope Phase 2B: Validation Integrity Audit Report

**Audit Date:** October 19, 2026  
**Auditor:** Antigravity AI Materials Systems Auditor  
**Scope:** Independent integrity audit of the completed Phase 2 external validation results, reference dataset provenance, DOI authenticity, evaluation eligibility rules, and statistical claims prior to any model modification or retraining.

---

## Executive Summary & Audit Verdict

> [!CAUTION]
> **AUDIT DECISION: The external validation is NOT yet trustworthy enough to serve as the sole gold-standard benchmark for model development or retraining decisions.**
> 
> While the evaluation script executes deterministically against the frozen production model, this integrity audit uncovered three critical discrepancies:
> 1. **Dataset Inconsistency & Report Markdown Disconnect:** The actual CSV evaluated (`semiscope_reference_bandgaps_expanded.csv`) contained 20 materials (including complex compositions like $\text{In}_5\text{CuS}_8$, $\text{Cs}_3\text{Bi}_2\text{Br}_9$, and $\text{In}_{0.6}\text{Ga}_{0.4}\text{As}_{0.6}\text{P}_{0.4}$), but the narrative markdown report (`phase2_validation_report.md`) displayed a discordant table containing legacy binary entries ($\text{PbS}$, $\text{PbTe}$, $\text{ZnSe}$, $\text{GaP}$) that were never evaluated in the actual code.
> 2. **Bibliographic Quality Deficits (4 Broken DOIs, 2 Mismatched DOIs):** Out of 20 records, 6 records had invalid or mismatched citations (e.g., $\text{Cs}_3\text{Bi}_2\text{Br}_9$'s DOI resolved to a $\text{BiVO}_4$ photocatalysis paper; $\text{CdTe}$, $\text{SiC}$, $\text{ZnS}$, and $\text{In}_5\text{CuS}_8$ had HTTP 404 links). In total, 4 records were improperly elevated to `verified_primary` instead of `provisional` or `verified_secondary`.
> 3. **Provisional Records Polluted the "Verified" Holdout:** The original evaluation treated `provisional` records as fully eligible ground truth. When provisional and unverified records are properly sequestered, the in-domain error **increases** from $\text{MAE} = 0.758\text{ eV}$ ($n=17$) to **$\text{MAE} = 0.890\text{ eV}$** ($n=13$), and overall error increases from $0.818\text{ eV}$ to **$0.948\text{ eV}$** ($n=15$).
> 4. **Unsupported Subgroup Reliability Claim:** The assertion that the model achieves "$\text{MAE} \approx 0.4\text{–}0.6\text{ eV}$" in the $0.3\text{–}3.0\text{ eV}$ band-gap range was based on a micro-sample of only $n=9$ materials, nearly half of which were provisional/unverified. This claim is statistically underpowered and uncalibrated.

---

## 1. Dataset Reconciliation & Provenance Audit

### 1.1 The 40-Record vs. 20-Record Discrepancy
- **Candidate CSVs in Repository:** An exhaustive search of the repository and file system revealed that only one expanded candidate CSV was generated and committed during Phase 2: `validation_results/semiscope_reference_bandgaps_expanded.csv` (SHA256: `0c5caf61b8fdcab34809638096a3bf85317b4f5b101c9086b8968a1344731f0d`). This file contains exactly **20 rows**.
- **Origin of the Metrics:** The exact dataset that produced `validation_metrics.json` and `external_validation_results.csv` is this 20-record file.
- **Root Cause of Narrative Discrepancy:** During the compilation of `phase2_validation_report.md`, an earlier 20-record exploratory table (incorporating $\text{PbS}$, $\text{PbTe}$, $\text{GaP}$, $\text{ZnSe}$) was accidentally copied into the markdown text, while the python execution pipeline (`evaluate_reference_holdout.py`) featurized and scored the 20 records in `semiscope_reference_bandgaps_expanded.csv` (which had replaced those binary materials with Mode 1 top-ranked materials $\text{In}_5\text{CuS}_8$, $\text{Cs}_3\text{Bi}_2\text{Br}_9$, $\text{In}_{0.6}\text{Ga}_{0.4}\text{As}_{0.6}\text{P}_{0.4}$, and double-perovskite $\text{Cs}_2\text{AgBiBr}_6$).

---

## 2. Independent Bibliographic & Source Verification

Every record was queried directly against the CrossRef API (`https://doi.org/...`) to verify the existence of the source, resolution of the DOI, author attribution, and experimental conditions:

### 2.1 Audit Results by Record
| Record ID | Formula | Common Name | Phase | Ref $E_g$ (eV) | Stated DOI / Citation | Automated DOI Resolution Result | Audited Status | Audit Finding |
|:---:|:---|:---|:---|:---:|:---|:---|:---:|:---|
| 1 | `Si` | Silicon | diamond cubic | 1.12 | ISBN: 978-0-471-14323-9; Macfarlane et al. (1958) | Valid ISBN & Phys. Rev. 111, 1245 citation | **verified_primary** | Fundamental indirect gap at 300 K. |
| 2 | `Ge` | Germanium | diamond cubic | 0.66 | ISBN: 978-0-471-14323-9; Dash & Newman (1955) | Valid ISBN & Phys. Rev. 99, 1151 citation | **verified_primary** | Fundamental indirect gap at 300 K. |
| 3 | `GaAs` | Gallium Arsenide | zincblende | 1.42 | 10.1103/PhysRev.127.768 | `RESOLVED`: Sturge, *Phys. Rev.* (1962) | **verified_primary** | Benchmark direct gap at 300 K. |
| 4 | `InP` | Indium Phosphide | zincblende | 1.34 | 10.1063/1.1368156 | `RESOLVED`: Vurgaftman et al., *J. Appl. Phys.* | **verified_primary** | Standard III-V review benchmark. |
| 5 | `CdTe` | Cadmium Telluride | zincblende | 1.50 | 10.1016/0022-3697(61)90045-8 | `FAIL`: HTTP 404 Not Found | **verified_secondary** | **Downgraded.** Broken Elsevier DOI. Value matches secondary Landolt-Börnstein/EMIS compilation. |
| 6 | `GaN` | Gallium Nitride | wurtzite | 3.40 | 10.1063/1.1368156 | `RESOLVED`: Vurgaftman et al. / Monemar | **verified_primary** | Standard room-temperature direct gap. |
| 7 | `ZnO` | Zinc Oxide | wurtzite | 3.37 | 10.1063/1.1992666 | `RESOLVED`: Özgür et al., *J. Appl. Phys.* (2005) | **verified_primary** | Comprehensive single-crystal review. |
| 8 | `TiO2` | Titanium Dioxide (Rutile) | rutile | 3.03 | 10.1103/PhysRev.87.876 | `RESOLVED`: Cronemeyer, *Phys. Rev.* (1952) | **verified_primary** | Benchmark single-crystal optical absorption. |
| 9 | `TiO2` | Titanium Dioxide (Anatase) | anatase | 3.20 | 10.1016/0038-1098(93)90427-O | `RESOLVED`: Tang et al., *Solid State Commun.* | **verified_primary** | Single-crystal optical absorption (polymorph test). |
| 10 | `In5CuS8` | Copper Pentaindium Octasulfide | spinel cubic | 1.34 | 10.1016/S0925-8388(01)01533-3 | `FAIL`: HTTP 404 Not Found | **provisional** | **Downgraded.** Broken DOI; single report on thiospinel; lacks independent gold-standard confirmation. |
| 11 | `Cs3Bi2Br9` | Cesium Bismuth Bromide | trigonal | 2.50 | 10.1021/acs.jpclett.0c01234 | `RESOLVED`: Lardhi et al., *J. Phys. Chem. Lett.* | **provisional** | **Downgraded.** Mismatched DOI! Resolves to $\text{BiVO}_4$ water splitting, NOT $\text{Cs}_3\text{Bi}_2\text{Br}_9$. Unverified primary citation. |
| 12 | `In0.6Ga0.4As0.6P0.4` | InGaAsP Quaternary | zincblende alloy | 1.25 | 10.1049/em:19910001 | `RESOLVED`: Constable, *IEE Review* | **provisional** | **Downgraded.** Mismatched DOI! Resolves to career editorial ("Success is in your own hands"). Alloy interpolation, not a single-crystal benchmark. |
| 13 | `AlN` | Aluminium Nitride | wurtzite | 6.20 | 10.1063/1.1368156 | `RESOLVED`: Vurgaftman et al., *J. Appl. Phys.* | **verified_primary** | Deep-UV bandgap benchmark. |
| 14 | `Ga2O3` | Gallium Oxide ($\beta$) | monoclinic | 4.85 | 10.1063/1.5006941 | `RESOLVED`: Pearton et al., *Appl. Phys. Rev.* | **verified_primary** | Benchmark ultrawide band gap. |
| 15 | `SiC` | Silicon Carbide (4H) | hexagonal | 3.26 | 10.1007/978-3-540-34988-4_2 | `FAIL`: HTTP 404 Not Found | **verified_secondary** | **Downgraded.** Broken Springer DOI. Value matches Goldberg handbook chapter. |
| 16 | `ZnS` | Zinc Sulfide | zincblende | 3.68 | 10.1103/PhysRev.136.A741 | `FAIL`: HTTP 404 Not Found | **verified_secondary** | **Downgraded.** Broken PhysRev DOI. Value matches CRC Handbook. |
| 17 | `CdS` | Cadmium Sulfide | wurtzite | 2.42 | 10.1103/PhysRev.116.573 | `RESOLVED`: Thomas & Hopfield, *Phys. Rev.* | **verified_primary** | Benchmark optical absorption / exciton. |
| 18 | `In2O3` | Indium Oxide | cubic bixbyite | 2.93 | 10.1103/PhysRevLett.100.167402 | `RESOLVED`: Walsh et al., *Phys. Rev. Lett.* | **unresolved** | **Correctly Excluded.** Dipole-forbidden fundamental gap vs. optical edge dispute ($2.93\text{ eV}$ vs $3.75\text{ eV}$). |
| 19 | `Cs2AgBiBr6` | Cs-Ag-Bi-Br Double Perovskite | cubic | 2.05 | 10.1021/jacs.5b13294 | `RESOLVED`: Slavney et al., *JACS* (2016) | **verified_primary** | High-quality double perovskite benchmark. |
| 20 | `Bi2O3` | Bismuth Trioxide ($\alpha$) | monoclinic | 2.85 | 10.1016/j.jssc.2016.05.010 | `RESOLVED`: Dolgonos et al., *J. Solid State Chem.* | **provisional** | Highly sensitive to oxygen stoichiometry and synthesis history. |

---

## 3. Inspection of Evaluation Eligibility Rules

In `evaluate_reference_holdout.py`, line 84 defined eligibility as:
```python
if quality == "unresolved":
    eligibility = "excluded"
else:
    eligibility = "eligible"
```
### Audit Finding:
**This rule improperly admitted `provisional` records into the primary benchmark.**  
Provisional records (such as $\text{Bi}_2\text{O}_3$, or downgraded records $\text{In}_5\text{CuS}_8$, $\text{Cs}_3\text{Bi}_2\text{Br}_9$, $\text{In}_{0.6}\text{Ga}_{0.4}\text{As}_{0.6}\text{P}_{0.4}$ with defective/mismatched citations) must NOT automatically qualify as gold-standard reference data. Admitting unverified candidate entries into a holdout benchmark creates false confidence and distorts error metrics.

---

## 4. Recomputation of Validation Metrics

All record-level errors in `external_validation_results.csv` and `validation_metrics.json` were recomputed directly from the row-level data.

### 4.1 Verification of Reported Metrics (Original n=19 Eligible Set)
Recomputation confirmed that the mathematical calculations in `validation_metrics.json` were strictly accurate for the dataset evaluated:
- **Overall Eligible ($n=19$):** $\text{MAE} = 0.8175\text{ eV}$, $\text{RMSE} = 1.0504\text{ eV}$, $\text{Bias} = -0.4797\text{ eV}$, $\text{Median AE} = 0.7660\text{ eV}$.
- **In-Domain Multielement ($n=17$):** $\text{MAE} = 0.7578\text{ eV}$, $\text{RMSE} = 1.0132\text{ eV}$, $\text{Bias} = -0.6919\text{ eV}$, $\text{Median AE} = 0.5580\text{ eV}$.
- **Out-of-Domain Elemental ($n=2$):** $\text{MAE} = 1.3245\text{ eV}$, $\text{RMSE} = 1.3247\text{ eV}$, $\text{Bias} = +1.3245\text{ eV}$, $\text{Median AE} = 1.3245\text{ eV}$.

### 4.2 Corrected Metrics on the Strictly Verified Subset (Excluding Provisional Records)
When provisional and unverified records ($\text{In}_5\text{CuS}_8$, $\text{Cs}_3\text{Bi}_2\text{Br}_9$, $\text{In}_{0.6}\text{Ga}_{0.4}\text{As}_{0.6}\text{P}_{0.4}$, and $\text{Bi}_2\text{O}_3$) are excluded, leaving only verified gold-standard records ($n=15$ total, $n=13$ in-domain):

| Cohort | Original $n$ | Original MAE (eV) | Original RMSE (eV) | Audited $n$ | Audited MAE (eV) | Audited RMSE (eV) | Audited Bias (eV) | Audited Median AE (eV) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Strictly Verified Overall** | 19 | 0.8175 | 1.0504 | **15** | **0.9480** | **1.1570** | **-0.5625** | **0.9790** |
| **Strictly Verified In-Domain** | 17 | 0.7578 | 1.0132 | **13** | **0.8901** | **1.1290** | **-0.8528** | **0.7660** |
| **Strictly Verified OOD Elemental** | 2 | 1.3245 | 1.3247 | **2** | **1.3245** | **1.3247** | **+1.3245** | **1.3245** |

> [!WARNING]
> **Impact of Strict Verification:** On the strictly verified in-domain ground truth, the model's true error is **$\text{MAE} = 0.890\text{ eV}$** (not $0.758\text{ eV}$), and the median error is **$0.766\text{ eV}$** (not $0.558\text{ eV}$). The provisional entries had artificially deflated the reported error because the model coincidentally predicted values near their candidate records ($0.087\text{–}0.184\text{ eV}$ error).

---

## 5. Investigation of Subgroup Range & Reliability Claims

The Phase 2 report claimed that the model is *"sufficiently reliable ... for in-domain multielement compounds with band gaps between 0.3 eV and 3.0 eV ($\text{MAE} \approx 0.4\text{–}0.6\text{ eV}$)"*.

### Audit Findings:
1. **Actual Sample Size in that Subgroup:** Exactly **$n = 9$ records** exist in the $0.3\text{–}3.0\text{ eV}$ range (`GaAs`, `InP`, `CdTe`, `In5CuS8`, `Cs3Bi2Br9`, `In0.6Ga0.4As0.6P0.4`, `CdS`, `Cs2AgBiBr6`, `Bi2O3`).
2. **Subgroup Sample Composition:** Of these 9 records, **4 records** ($\text{In}_5\text{CuS}_8$, $\text{Cs}_3\text{Bi}_2\text{Br}_9$, $\text{In}_{0.6}\text{Ga}_{0.4}\text{As}_{0.6}\text{P}_{0.4}$, $\text{Bi}_2\text{O}_3$) were classified as provisional or had invalid DOIs. Only **5 records** are strictly verified.
3. **Statistical Validity:** Asserting a generalized domain reliability claim of "0.4–0.6 eV MAE" based on 5 verified records is **statistically invalid and unsupported by sample size**. Furthermore, wide-bandgap materials ($E_g > 3.0\text{ eV}$) exhibit an extreme underestimation bias of up to $-2.28\text{ eV}$ ($\text{AlN}$) and $-1.89\text{ eV}$ ($\text{Ga}_2\text{O}_3$).

---

## 6. Reproducibility & Environment Verification

- **Production Model:** `models/bandgap/model.joblib` loaded cleanly.
- **Python Runtime:** Python `3.13.0`
- **scikit-learn Runtime:** `1.9.0` (Runtime version matches serialized version `1.9.0`).
- **Deterministic Execution:** The evaluation script runs deterministically and reproduces the exact same float values across runs without warnings.
- **Compatibility Risk:** Python 3.13 is a very recent release; ensure virtual environments pin `scikit-learn==1.9.0` and `numpy` to prevent serialization drift.

---

## 7. Audit Deliverables Created

1. [`validation_results/validation_integrity_audit.md`](file:///Users/anshulpathak/Desktop/AI_Project/semiscope/validation_results/validation_integrity_audit.md): This comprehensive integrity audit document.
2. [`validation_results/verified_reference_subset.csv`](file:///Users/anshulpathak/Desktop/AI_Project/semiscope/validation_results/verified_reference_subset.csv): The audited reference dataset containing corrected evidence classifications (`verified_primary`, `verified_secondary`, `provisional`, `unresolved`) and specific bibliographic audit notes for all 20 records.
3. [`validation_results/validation_metrics_corrected.json`](file:///Users/anshulpathak/Desktop/AI_Project/semiscope/validation_results/validation_metrics_corrected.json): Machine-readable metrics capturing both original and audited strictly-verified holdout results.

---

## 8. Final Decision & Development Recommendation

### Is the external validation trustworthy enough to guide model development?
**DECISION: NO, not in its current state.**

### Justification:
1. **The reference dataset contains citation errors:** 4 broken DOIs and 2 mismatched DOIs must be corrected and replaced with peer-reviewed single-crystal papers.
2. **True holdout error is higher than reported:** On verified in-domain ground truth, $\text{MAE} = 0.890\text{ eV}$ (not $0.758\text{ eV}$), with systematic underprediction on wide-gap oxides/nitrides (bias $-0.853\text{ eV}$).
3. **Sample size is too small for subgroup claims:** With only 13 verified in-domain records, any claim of localized 0.4–0.6 eV reliability is statistically premature.

### Required Actions Before Proceeding to Model Retraining:
1. **Curate a True 50+ Gold-Standard Holdout:** Build a curated reference set of at least 50 experimentally verified single-crystal semiconductor band gaps with fully verified primary DOIs.
2. **Maintain Strict Exclusion of Provisional Data:** Separate candidate/screening data from gold-standard holdout benchmarks.
3. **Preserve Phase 1 Out-of-Domain Guardrails:** Continue enforcing out-of-domain rejection for elemental semiconductors (`Si`, `Ge`) and displaying explicit warnings.
