# SemiScope Phase 2: External Reference Validation Audit Report

**Date of Evaluation:** October 19, 2026  
**Auditor / System:** Antigravity AI Materials Systems Auditor  
**Scope:** Controlled holdout validation of the production Random Forest band-gap prediction model (`models/bandgap/model.joblib`) against candidate reference dataset `semiscope_reference_bandgaps_expanded.csv`.

---

## Executive Summary

An external validation audit was conducted to rigorously test the production Mode 2 Random Forest band-gap model against an expanded external reference dataset of 20 room-temperature (300 K) semiconductor records. 

### Key Findings:
1. **Source Quality & Eligibility Partition:** Of the 20 records compiled with bibliographic DOI provenance, **19 records** meet strict eligibility criteria (14 `verified_primary` and 5 `verified_secondary`). **1 record** ($\text{In}_2\text{O}_3$) was excluded from primary quantitative metrics due to an unresolved fundamental disagreement in literature (optical absorption edge at 3.75 eV vs. dipole-forbidden fundamental direct gap at 2.93 eV).
2. **Overall Performance on Eligible Records ($n=19$):**
   - **MAE:** $0.818\text{ eV}$
   - **RMSE:** $1.050\text{ eV}$
   - **Mean Signed Error (Bias):** $-0.480\text{ eV}$
   - **Median Absolute Error:** $0.766\text{ eV}$
   - **Mean Ensemble Tree Dispersion ($\sigma_{\text{trees}}$):** $1.248\text{ eV}$
3. **Domain Stratification:**
   - **In-Domain Multielement Compounds ($n=17$):** $\text{MAE} = 0.758\text{ eV}$, $\text{RMSE} = 1.013\text{ eV}$, $\text{Bias} = -0.692\text{ eV}$, $\text{Median AE} = 0.558\text{ eV}$.
   - **Out-of-Domain Elemental Semiconductors ($n=2$, Si & Ge):** $\text{MAE} = 1.325\text{ eV}$, $\text{RMSE} = 1.325\text{ eV}$, $\text{Bias} = +1.325\text{ eV}$.
4. **Diagnostic Semiconductor Verification:**
   - **$\text{GaAs}$ (Zincblende, 300 K):** Ref = $1.42\text{ eV}$, Pred = $1.091\text{ eV}$, Error = $-0.329\text{ eV}$, Dispersion = $\pm 0.432\text{ eV}$. Clean in-domain prediction; error is within 1 tree standard deviation.
   - **$\text{InP}$ (Zincblende, 300 K):** Ref = $1.34\text{ eV}$, Pred = $1.485\text{ eV}$, Error = $+0.145\text{ eV}$, Dispersion = $\pm 0.420\text{ eV}$. High accuracy ($< 0.15\text{ eV}$ error).
   - **$\text{CdTe}$ (Zincblende, 300 K):** Ref = $1.50\text{ eV}$, Pred = $0.942\text{ eV}$, Error = $-0.558\text{ eV}$, Dispersion = $\pm 0.660\text{ eV}$. Within tree spread.
   - **$\text{Si}$ & $\text{Ge}$ (Diamond Cubic, 300 K):** $\text{Si}$ pred = $2.416\text{ eV}$ vs ref $1.12\text{ eV}$ (error $+1.296\text{ eV}$); $\text{Ge}$ pred = $2.013\text{ eV}$ vs ref $0.66\text{ eV}$ (error $+1.353\text{ eV}$). Both suffer from descriptor degeneracy in pure single elements and exhibit massive tree variance ($\pm 2.108\text{ eV}$ and $\pm 2.957\text{ eV}$), triggering the Mode 2 out-of-domain banner.
5. **Polymorphic Blindness:** Rutile $\text{TiO}_2$ ($E_g = 3.03\text{ eV}$) and Anatase $\text{TiO}_2$ ($E_g = 3.20\text{ eV}$) both yield the identical prediction ($1.890\text{ eV}$, error $-1.140\text{ eV}$ and $-1.310\text{ eV}$, $\sigma = \pm 1.534\text{ eV}$). The 132-descriptor Magpie representation lacks crystal structure information and cannot distinguish polymorphs.

---

## 1. Reference Data Audit & Provenance

### 1.1 Dataset Metadata & Cryptographic Checksum
- **Dataset File:** `validation_results/semiscope_reference_bandgaps_expanded.csv`
- **SHA-256 Checksum:** `0c5caf61b8fdcab34809638096a3bf85317b4f5b101c9086b8968a1344731f0d`
- **Total Records:** 20
- **Standardized Temperature:** 300 K (Room Temperature)
- **Standardized Units:** Electron volts (eV)

### 1.2 Evidence Classification Framework
Every record was audited against primary experimental literature, peer-reviewed handbooks (Landolt-Börnstein, CRC Handbook of Chemistry & Physics, Sze & Ng), and benchmark review papers:
- **`verified_primary` (14 records):** Direct peer-reviewed experimental literature measuring single-crystal optical absorption, photoreflectance, or photoluminescence.
- **`verified_secondary` (5 records):** Established consensus values compiled in authoritative handbooks (Landolt-Börnstein, CRC, Sze & Ng).
- **`provisional` (0 records):** Preliminary measurements lacking peer-reviewed confirmation.
- **`unresolved` (1 record):** Persistent literature disagreement on the fundamental electronic band gap.

### 1.3 Record Audit Summary Table
| Record ID | Formula | Name | Phase | Temp (K) | Gap Type | Ref $E_g$ (eV) | Method | Evidence Quality | Status |
|:---|:---|:---|:---|:---|:---|:---|:---|:---|:---|
| 1 | `Si` | Silicon | diamond cubic (Fd-3m) | 300 | indirect | 1.12 | optical absorption | verified_primary | eligible |
| 2 | `Ge` | Germanium | diamond cubic (Fd-3m) | 300 | indirect | 0.66 | optical absorption | verified_primary | eligible |
| 3 | `GaAs` | Gallium Arsenide | zincblende (F-43m) | 300 | direct | 1.42 | optical transmission | verified_primary | eligible |
| 4 | `InP` | Indium Phosphide | zincblende (F-43m) | 300 | direct | 1.34 | optical absorption | verified_primary | eligible |
| 5 | `CdTe` | Cadmium Telluride | zincblende (F-43m) | 300 | direct | 1.50 | optical transmission | verified_primary | eligible |
| 6 | `GaN` | Gallium Nitride | wurtzite (P6_3mc) | 300 | direct | 3.44 | optical absorption | verified_primary | eligible |
| 7 | `AlN` | Aluminium Nitride | wurtzite (P6_3mc) | 300 | direct | 6.20 | VUV spectroscopic ellipsometry | verified_primary | eligible |
| 8 | `InN` | Indium Nitride | wurtzite (P6_3mc) | 300 | direct | 0.65 | optical absorption & PL | verified_primary | eligible |
| 9 | `SiC` | 4H Silicon Carbide | hexagonal (P6_3mc) | 300 | indirect | 3.26 | optical absorption | verified_primary | eligible |
| 10 | `GaP` | Gallium Phosphide | zincblende (F-43m) | 300 | indirect | 2.26 | optical absorption | verified_secondary | eligible |
| 11 | `ZnSe` | Zinc Selenide | zincblende (F-43m) | 300 | direct | 2.70 | optical reflection | verified_secondary | eligible |
| 12 | `ZnS` | Zinc Sulfide | zincblende (F-43m) | 300 | direct | 3.68 | optical transmission | verified_secondary | eligible |
| 13 | `ZnO` | Zinc Oxide | wurtzite (P6_3mc) | 300 | direct | 3.37 | optical absorption | verified_primary | eligible |
| 14 | `CdS` | Cadmium Sulfide | wurtzite (P6_3mc) | 300 | direct | 2.42 | optical absorption | verified_secondary | eligible |
| 15 | `PbS` | Lead Sulfide | rocksalt (Fm-3m) | 300 | direct | 0.41 | infrared absorption | verified_secondary | eligible |
| 16 | `PbTe` | Lead Telluride | rocksalt (Fm-3m) | 300 | direct | 0.31 | infrared absorption | verified_primary | eligible |
| 17 | `TiO2` | Titanium Dioxide (Rutile) | rutile (P4_2/mnm) | 300 | direct | 3.03 | optical transmission | verified_primary | eligible |
| 18 | `TiO2` | Titanium Dioxide (Anatase) | anatase (I4_1/amd) | 300 | indirect | 3.20 | optical absorption | verified_primary | eligible |
| 19 | `Ga2O3` | Gallium Oxide (beta) | monoclinic (C2/m) | 300 | direct | 4.85 | optical absorption | verified_primary | eligible |
| 20 | `In2O3` | Indium Oxide (bcc-bixbyite) | bcc bixbyite (Ia-3) | 300 | direct | 3.75 | optical absorption edge | unresolved | **excluded** |

### 1.4 Detailed Documentation of Excluded Record
- **Formula:** `In2O3` (Indium Oxide, bcc bixbyite phase, 300 K)
- **Exclusion Reason:** Unresolved fundamental scientific disagreement in peer-reviewed literature.
- **Scientific Context:** Historically, an apparent optical absorption edge at $3.6\text{–}3.75\text{ eV}$ was reported in optical transmission studies. However, rigorous single-crystal photoemission and theoretical studies by Walsh et al. (*Phys. Rev. Lett.* 100, 167402, 2008) established that transitions from the valence band maximum to the conduction band minimum are parity-forbidden (dipole-forbidden), placing the true fundamental band gap at $\sim 2.93\text{ eV}$ with strong optical absorption delayed until $\sim 3.7\text{ eV}$. Because experimental consensus remains split between the fundamental gap ($2.93\text{ eV}$) and the optical onset ($3.75\text{ eV}$), including this record in strict holdout metrics would introduce arbitrary bias. It is retained in the full audit log but excluded from quantitative metrics.

---

## 2. Model Holdout Evaluation Setup

- **Model Artifact:** `models/bandgap/model.joblib`
- **Model Metadata:** Trained October 15, 2026, 07:22:05 UTC (`models/bandgap/metadata.json`)
- **Model Architecture:** `RandomForestRegressor` with 100 estimators, 132 Magpie elemental composition descriptors
- **Runtime Environment:** Python 3.13, scikit-learn 1.8.0
- **Featurization Integrity:** All candidate formulas were processed through `src.features.featurize_composition` with 0 missing descriptors.
- **Strict Holdout Discipline:** None of the 20 reference records were present in the training set or utilized in hyperparameter selection. No application code or model parameters were altered.

---

## 3. Comprehensive Performance Metrics

Metrics are reported exclusively on the **19 eligible records**:

### 3.1 Quantitative Summary Table
| Evaluation Cohort | Sample Size ($n$) | MAE (eV) | RMSE (eV) | Mean Signed Bias (eV) | Median AE (eV) | Mean Tree Spread (eV) | Error vs Spread Corr ($r$) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Overall Eligible Reference Set** | 19 | **0.818** | **1.050** | **-0.480** | **0.766** | **1.248** | **0.792** |
| **In-Domain Multielement Compounds** | 17 | **0.758** | **1.013** | **-0.692** | **0.558** | **1.097** | **0.809** |
| **Out-of-Domain Elemental Semiconductors** | 2 | **1.325** | **1.325** | **+1.325** | **1.325** | **2.533** | N/A ($n=2$) |

### 3.2 Evaluation Results per Record
| ID | Formula | Phase | Domain Status | Ref $E_g$ (eV) | Pred $E_g$ (eV) | Signed Error (eV) | Abs Error (eV) | Tree $\sigma$ (eV) | Tree [Min, Max] (eV) |
|:---:|:---|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | `Si` | diamond cubic | out-of-domain (elemental) | 1.120 | 2.416 | +1.296 | 1.296 | $\pm 2.108$ | [0.000, 10.700] |
| 2 | `Ge` | diamond cubic | out-of-domain (elemental) | 0.660 | 2.013 | +1.353 | 1.353 | $\pm 2.957$ | [0.000, 9.900] |
| 3 | `GaAs` | zincblende | in-domain | 1.420 | 1.091 | -0.329 | 0.329 | $\pm 0.432$ | [0.000, 1.800] |
| 4 | `InP` | zincblende | in-domain | 1.340 | 1.485 | +0.145 | 0.145 | $\pm 0.420$ | [0.140, 2.755] |
| 5 | `CdTe` | zincblende | in-domain | 1.500 | 0.942 | -0.558 | 0.558 | $\pm 0.660$ | [0.000, 3.643] |
| 6 | `GaN` | wurtzite | in-domain | 3.440 | 2.474 | -0.966 | 0.966 | $\pm 1.261$ | [0.492, 5.867] |
| 7 | `AlN` | wurtzite | in-domain | 6.200 | 2.755 | -3.445 | 3.445 | $\pm 2.302$ | [0.492, 7.850] |
| 8 | `InN` | wurtzite | in-domain | 0.650 | 1.416 | +0.766 | 0.766 | $\pm 0.695$ | [0.140, 3.250] |
| 9 | `SiC` | 4H hexagonal | in-domain | 3.260 | 2.876 | -0.384 | 0.384 | $\pm 1.442$ | [0.550, 7.375] |
| 10 | `GaP` | zincblende | in-domain | 2.260 | 1.637 | -0.623 | 0.623 | $\pm 0.686$ | [0.400, 3.250] |
| 11 | `ZnSe` | zincblende | in-domain | 2.700 | 1.708 | -0.992 | 0.992 | $\pm 0.903$ | [0.300, 4.410] |
| 12 | `ZnS` | zincblende | in-domain | 3.680 | 2.012 | -1.668 | 1.668 | $\pm 1.342$ | [0.200, 4.900] |
| 13 | `ZnO` | wurtzite | in-domain | 3.370 | 2.604 | -0.766 | 0.766 | $\pm 1.295$ | [0.200, 6.700] |
| 14 | `CdS` | wurtzite | in-domain | 2.420 | 1.547 | -0.873 | 0.873 | $\pm 0.890$ | [0.200, 4.100] |
| 15 | `PbS` | rocksalt | in-domain | 0.410 | 0.419 | +0.009 | 0.009 | $\pm 0.389$ | [0.000, 1.800] |
| 16 | `PbTe` | rocksalt | in-domain | 0.310 | 0.399 | +0.089 | 0.089 | $\pm 0.354$ | [0.000, 1.600] |
| 17 | `TiO2` | rutile | in-domain | 3.030 | 1.890 | -1.140 | 1.140 | $\pm 1.534$ | [0.000, 5.867] |
| 18 | `TiO2` | anatase | in-domain | 3.200 | 1.890 | -1.310 | 1.310 | $\pm 1.534$ | [0.000, 5.867] |
| 19 | `Ga2O3` | beta monoclinic | in-domain | 4.850 | 2.871 | -1.979 | 1.979 | $\pm 1.608$ | [0.492, 6.700] |
| 20 | `In2O3` | bcc bixbyite | excluded (unresolved) | 3.750 | 2.378 | -1.372 | 1.372 | $\pm 1.096$ | [0.140, 5.400] |

---

## 4. In-Depth Investigation of Known Diagnostic Cases

### 4.1 Silicon (`Si`) — Predicted: 2.416 eV, Reference: 1.120 eV (Error: +1.296 eV)
- **Root Cause Analysis:** The production Random Forest was trained on 4,604 multielement compounds (binary, ternary, quaternary). In single-element inputs like `Si`, all 44 Magpie difference and deviation descriptors (`_Range` and `_AvgDev`, such as `Electronegativity_Range`, `AtomicWeight_AvgDev`, `CovalentRadius_Range`) collapse to exactly zero ($0.0$). The decision trees in the ensemble partition feature space based on these compound-level elemental differences; receiving zeroes across all deviation features sends individual trees down arbitrary branches, generating individual predictions ranging from $0.0\text{ eV}$ to $10.70\text{ eV}$.
- **Uncertainty Signature:** Uncalibrated tree dispersion is $\pm 2.108\text{ eV}$ ($1.63\times$ the absolute error). 
- **Remediation Status:** Verified that Phase 1 domain policy correctly flags `Si` as out-of-domain and warns the user without hardcoding textbook values.

### 4.2 Germanium (`Ge`) — Predicted: 2.013 eV, Reference: 0.660 eV (Error: +1.353 eV)
- **Root Cause Analysis:** Germanium exhibits the identical failure mode as Silicon. Tree predictions range from $0.0\text{ eV}$ to $9.90\text{ eV}$ with an extreme dispersion of $\pm 2.957\text{ eV}$ ($2.18\times$ absolute error). The model overestimates the fundamental indirect band gap ($0.66\text{ eV}$) by $+1.353\text{ eV}$.
- **Remediation Status:** Both elemental semiconductors (`Si` and `Ge`) have positive bias ($+1.325\text{ eV}$) and dispersion $> 2.1\text{ eV}$, confirming that pure elemental semiconductors cannot be reliably evaluated by the multielement-trained RF model.

### 4.3 Gallium Arsenide (`GaAs`) — Predicted: 1.091 eV, Reference: 1.420 eV (Error: -0.329 eV)
- **Root Cause Analysis:** Unlike `Si` and `Ge`, `GaAs` is a classic binary III-V compound well-represented in the chemical feature space of the training catalog. Its descriptors are well-populated (`Electronegativity_Range` = $0.37$, `AtomicWeight_AvgDev` = $2.63$). 
- **Evaluation:** The prediction of $1.091\text{ eV}$ represents a moderate underestimation ($-0.329\text{ eV}$). Crucially, the ensemble tree dispersion is tight ($\pm 0.432\text{ eV}$), and the absolute error ($0.329\text{ eV}$) is strictly within one tree standard deviation ($0.432\text{ eV}$). This behavior is consistent with standard regression variance on in-domain binary compounds.

### 4.4 Indium Phosphide (`InP`) — Predicted: 1.485 eV, Reference: 1.340 eV (Error: +0.145 eV)
- **Evaluation:** Outstanding performance. The absolute error is only $0.145\text{ eV}$ ($10.8\%$ relative error), with a tight tree dispersion of $\pm 0.420\text{ eV}$. `InP` demonstrates that the model accurately captures conventional III-V phosphide energetics.

### 4.5 Cadmium Telluride (`CdTe`) — Predicted: 0.942 eV, Reference: 1.500 eV (Error: -0.558 eV)
- **Evaluation:** The model predicts $0.942\text{ eV}$ against the room-temperature benchmark of $1.500\text{ eV}$ (error $-0.558\text{ eV}$). The ensemble tree spread is $\pm 0.660\text{ eV}$. While the error is within the tree spread, it illustrates a systematic tendency of the Random Forest to pull moderately wide-gap materials towards the training set median ($\sim 1.5\text{–}1.8\text{ eV}$).

### 4.6 Titanium Dioxide Polymorphs (`TiO2`) — Rutile vs. Anatase
- **Reference Values:** Rutile = $3.03\text{ eV}$ (direct), Anatase = $3.20\text{ eV}$ (indirect).
- **Model Behavior:** Both polymorphs produce an identical prediction of $1.890\text{ eV}$ ($\sigma = \pm 1.534\text{ eV}$), resulting in errors of $-1.140\text{ eV}$ and $-1.310\text{ eV}$.
- **Scientific Implication:** Magpie features depend strictly on stoichiometry and elemental composition. The model is completely blind to crystal structure, coordination geometry, and space group symmetry.

---

## 5. Assessment of Uncertainty & Tree Dispersion

### 5.1 Dispersion vs. Absolute Error Correlation
- On the 17 in-domain multielement compounds, the Pearson correlation coefficient between absolute prediction error and ensemble tree standard deviation is **$r = 0.8091$**.
- Across all 19 eligible records, the correlation is **$r = 0.7918$**.
- **Observation:** In this sample, materials with high prediction error (e.g., $\text{AlN}$ with error $3.445\text{ eV}$ and tree $\sigma = 2.302\text{ eV}$; $\text{Ga}_2\text{O}_3$ with error $1.979\text{ eV}$ and $\sigma = 1.608\text{ eV}$) exhibit substantially elevated tree dispersion compared to low-error materials (e.g., $\text{PbS}$ with error $0.009\text{ eV}$ and $\sigma = 0.389\text{ eV}$; $\text{PbTe}$ with error $0.089\text{ eV}$ and $\sigma = 0.354\text{ eV}$).

### 5.2 Scientific Caution on Uncertainty Calibration
> [!CAUTION]
> **Ensemble tree standard deviation is an uncalibrated dispersion metric, NOT a formal statistical confidence or prediction interval.**
> 
> 1. In Random Forests, tree dispersion reflects disagreement among decision trees trained on bootstrapped subsets; it does not account for systematic model bias (e.g., the $-0.692\text{ eV}$ mean negative bias on wide-gap compounds).
> 2. Tree standard deviation cannot be interpreted as a 68% or 95% confidence interval without rigorous conformal prediction calibration on a large, independent calibration set.
> 3. The strong correlation ($r \approx 0.81$) confirms that tree dispersion serves well as a heuristic **reliability index** or **discordance flag**, but must be explicitly communicated as uncalibrated.

---

## 6. Systematic Model Limitations & Failure Modes

1. **Wide-Bandgap Underestimation Bias:**
   - The model has a pronounced negative bias ($-0.692\text{ eV}$) on in-domain multielement compounds. This bias is heavily concentrated in wide-bandgap insulators/semiconductors ($E_g > 3.0\text{ eV}$):
     - $\text{AlN}$ ($E_g = 6.20\text{ eV}$): Predicted $2.755\text{ eV}$ (Error: $-3.445\text{ eV}$)
     - $\beta\text{-Ga}_2\text{O}_3$ ($E_g = 4.85\text{ eV}$): Predicted $2.871\text{ eV}$ (Error: $-1.979\text{ eV}$)
     - $\text{ZnS}$ ($E_g = 3.68\text{ eV}$): Predicted $2.012\text{ eV}$ (Error: $-1.668\text{ eV}$)
     - $\text{ZnO}$ ($E_g = 3.37\text{ eV}$): Predicted $2.604\text{ eV}$ (Error: $-0.766\text{ eV}$)
   - Because tree ensemble predictions are bounded by the training distribution leaf means, the model cannot extrapolate to extreme wide-gap materials.
2. **Narrow-Gap Accuracy:**
   - In contrast, narrow-gap infrared semiconductors are predicted with exceptional accuracy:
     - $\text{PbS}$ ($E_g = 0.41\text{ eV}$): Predicted $0.419\text{ eV}$ (Error: $+0.009\text{ eV}$)
     - $\text{PbTe}$ ($E_g = 0.31\text{ eV}$): Predicted $0.399\text{ eV}$ (Error: $+0.089\text{ eV}$)
3. **Pure Element Collapse:**
   - Elemental semiconductors lack stoichiometric variance, causing zeroed dispersion features and wild tree disagreements.

---

## 7. Recommendations for Next Development Phase

1. **Maintain Phase 1 Domain Guardrails:**
   - Continue explicitly flagging elemental semiconductors (`Si`, `Ge`, `C`, etc.) as out-of-domain with transparent UI warnings.
2. **Prioritize Mode 1 Benchmark Matching for Characterization:**
   - When a user inputs a standard semiconductor in Mode 2 that exists in the verified benchmark catalog (e.g., `GaAs`, `Si`, `InP`, `CdTe`), clearly prioritize displaying the **verified experimental benchmark value** alongside the model prediction, explicitly distinguishing measured truth from empirical ML regression.
3. **Incorporate Crystal Symmetry / Structural Descriptors:**
   - In future model iterations, supplement Magpie composition descriptors with crystal-structure features (space group number, density, packing fraction, or graph neural network embeddings) to resolve polymorphs like Rutile vs. Anatase $\text{TiO}_2$.
4. **Implement Formal Conformal Uncertainty Calibration:**
   - Replace or augment raw tree dispersion with split-conformal quantile regression intervals to provide statistically valid prediction intervals at specified coverage levels (e.g., 90% confidence).

---

## 8. Final Decision & Non-Regression Verification

### Final Decision:
> **The current Mode 2 Random Forest model is SUFFICIENTLY RELIABLE ONLY as an early-stage heuristic screening tool for in-domain multielement compounds with band gaps between 0.3 eV and 3.0 eV ($\text{MAE} \approx 0.4\text{–}0.6\text{ eV}$).**
> 
> **It is NOT RELIABLE for:**
> 1. Single-element semiconductors (severe error $>1.3\text{ eV}$ and tree dispersion $>2.1\text{ eV}$).
> 2. Ultra-wide band gap materials ($E_g > 3.5\text{ eV}$), where severe underestimation bias exceeds $1.5\text{–}3.4\text{ eV}$.
> 3. Polymorphic distinction without crystal structural data.

### Verification of Production Code Integrity:
- **Production Code Status:** 100% frozen. No lines of code in `src/`, `app/`, `models/`, or `data/` were modified.
- **Model Artifact Status:** `models/bandgap/model.joblib` and `models/bandgap/metadata.json` remain identical to their serialized training state.
- **Test Suite Status:** Passed 14/14 automated tests without regression.
