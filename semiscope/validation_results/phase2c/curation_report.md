# SemiScope Phase 2C: External Band-Gap Benchmark Curation and Evidence Verification Report

**Date of Curation:** October 19, 2026  
**Auditor:** Antigravity AI Materials Systems Auditor  
**Dataset Directory:** `validation_results/phase2c/`  
**Primary Benchmark Artifact:** `validation_results/phase2c/reference_benchmark.csv` (54 records, SHA-256: `3a4f6bb8fbc923a1050e64f89d977e2ffb234479599ea78f8cb339c908581895`)  
**Integrity Suite:** `verify_benchmark_integrity.py` (Passed all 4 integrity test suites, 0 errors)

---

## Executive Summary & Decision Gate

In Phase 2B, an integrity audit revealed that earlier external validation candidate sets suffered from provisional citations, broken DOIs, mismatched papers, and report tables discordant with evaluated data.

Phase 2C addresses this by building an independently auditable, gold-standard benchmark from scratch:
- **Total candidate records audited:** 66 records.
- **Final eligible, verified primary records:** **54 records** (exceeding the $\ge 50$ requirement).
- **Excluded records:** 12 records (strictly isolated in `excluded_records.csv` due to broken DOIs, mismatched papers, stoichiometry/polymorphic sensitivity, or unresolved literature disputes).
- **Primary DOI resolution rate on eligible set:** **100% (54/54)** verified live against the CrossRef metadata API.
- **Model Freeze Verification:** The production Random Forest model, 132 Magpie feature schema, and training datasets were verified as 100% unchanged via cryptographic SHA-256 signatures.

### Official Decision Gate:
> ### **DECISION: `READY_FOR_MODEL_DEVELOPMENT_DECISIONS`**
> 
> **Scientific Justification:**  
> The Phase 2C benchmark contains **54 strictly verified, peer-reviewed primary experimental measurements** with authentic CrossRef-resolved DOIs, exact table/page citations, standardized 300 K temperatures, and explicit crystal structure/polymorph definitions. With $n=51$ in-domain multielement compounds and $n=3$ elemental challenge materials spanning narrow-gap ($<1.5\text{ eV}$), conventional ($1.5\text{–}3.0\text{ eV}$), and wide-gap ($>3.0\text{ eV}$) semiconductors, the benchmark provides statistically defensible power, representation, and purity to guide model development, architecture upgrades, and conformal calibration.

---

## 1. Frozen Model & Artifact Integrity Hashes

Before data curation or evaluation, the working tree and production artifacts were audited and cryptographically locked. No production code, training data, or hyperparameters were altered.

### Cryptographic Signatures (SHA-256):
- **Production Model Artifact (`models/bandgap/model.joblib`):**  
  `44e961abfe07a9a11a9b895430cdf3943fa53caef8408a201cf883c7b95cdaaf` (2.75 MB, 100 trees, max depth 20)
- **Production Metadata (`models/bandgap/metadata.json`):**  
  `0e265628b740713339bc32cf9826b0235f48a5fe133e69724806efba38ea32b0` (Trained 2026-10-15T07:22:05Z)
- **Feature Schema (`src/magpie_features.json`):**  
  `3c6c36e7696df28f266290de860394b3cefb96001ea27672be94cb4f57101195` (132 Magpie elemental descriptors)
- **Training Dataset Pool (`data/raw/matbench_expt_gap_renamed.csv`):**  
  `9d0b44f68a867ae8e55a38828390cd80e16ddbb884a483682dda1078df09ceb5` (4,604 experimental records, 3,705 chemical systems)
- **Production Featurizer (`src/features.py`):**  
  `93ecc44d2a4ac11067dbc2f60d972daea855cbdda1de57ff1b7da5bfe3511453`
- **Configuration (`src/config.py`):**  
  `e26ff5a4fc0131285d470a3a087ffb9a510ed7aa6c1338f272c92733bb1dcd6b`

---

## 2. Benchmark Composition, Coverage & Distribution

The 54 eligible records in `reference_benchmark.csv` exhibit rigorous scientific diversity:

### 2.1 By Evidence Tier & Status
- **`verified_primary`:** 54 records (100% of eligible benchmark)
- **`verified_secondary`:** 0 records in primary benchmark
- **`provisional`:** 0 records in primary benchmark (11 quarantined in `excluded_records.csv`)
- **`unresolved`:** 0 records in primary benchmark (1 quarantined in `excluded_records.csv`)

### 2.2 By Stoichiometric Order
- **Elemental challenge set:** 3 records (`Si`, `Ge`, `C` diamond)
- **Binary compounds:** 38 records (III-V, II-VI, IV-VI, transition metal oxides, silicides)
- **Ternary compounds:** 10 records (chalcopyrites, titanates, tantalate, double perovskite)
- **Quaternary compounds:** 3 records (halide perovskites $\text{CsPbBr}_3$, $\text{CsPbI}_3$, $\text{CsPbCl}_3$)

### 2.3 By Band-Gap Range
- **Narrow-gap ($E_g < 1.5\text{ eV}$):** 14 in-domain records (e.g., $\text{InSb}$, $\text{InAs}$, $\text{PbS}$, $\text{CuInSe}_2$, $\text{MoS}_2$)
- **Conventional ($1.5\text{ eV} \le E_g \le 3.0\text{ eV}$):** 19 in-domain records (e.g., $\text{CdTe}$, $\text{GaAs}$, $\text{GaP}$, $\text{ZnSe}$, $\text{Cu}_2\text{O}$)
- **Wide & Ultrawide gap ($E_g > 3.0\text{ eV}$):** 18 in-domain records (e.g., $\text{ZnO}$, $\text{GaN}$, $\text{AlN}$, $\text{TiO}_2$, $\text{SnO}_2$, $\text{MgO}$, $\text{BN}$)

### 2.4 By Experimental Gap Type
- **Direct gap:** 38 records
- **Indirect gap:** 16 records

---

## 3. Excluded Records Audit Trail

All 12 excluded candidates are recorded in `excluded_records.csv` with explicit scientific exclusion rationales:

| Record ID | Formula | Reference $E_g$ (eV) | Tier | Exclusion Category | Scientific Exclusion Rationale |
|:---:|:---|:---:|:---:|:---|:---|
| 55 | `In2O3` | 2.93 | unresolved | unresolved_dispute | Dipole-forbidden valence-to-conduction transition creates persistent unresolved discrepancy between fundamental gap (2.93 eV) and optical edge (3.75 eV). |
| 56 | `Bi2O3` | 2.85 | provisional | polycrystalline_defect_shift | Polycrystalline powder diffuse reflectance; strongly influenced by oxygen non-stoichiometry and synthesis thermal history. |
| 57 | `In5CuS8` | 1.34 | provisional | broken_doi_single_report | Publisher DOI `10.1016/S0925-8388(01)01533-3` is broken (HTTP 404); isolated report on spinel analogue lacking independent gold-standard confirmation. |
| 58 | `Cs3Bi2Br9` | 2.50 | provisional | mismatched_doi | Supplied DOI resolves to unrelated $\text{BiVO}_4$ water-splitting paper (Lardhi et al.); unverified primary benchmark citation. |
| 59 | `In0.6Ga0.4As0.6P0.4` | 1.25 | provisional | alloy_bowing_editorial_doi | Supplied DOI resolves to career editorial in *IEE Review*; quaternary random alloy with composition-dependent bowing rather than stoichiometric benchmark compound. |
| 60 | `PbSe` | 0.28 | provisional | burstein_moss_degeneracy | Severe room-temperature free-carrier Burstein-Moss shift in available single-crystal absorption data ($0.26\text{–}0.29\text{ eV}$). |
| 61 | `PbTe` | 0.31 | provisional | positive_temp_coeff_shift | Positive temperature coefficient of band gap and carrier degeneracy shift preclude rigorous uncorrected benchmark status without low-carrier single crystals. |
| 62 | `WO3` | 2.62 | provisional | polaronic_substoichiometry | Strongly influenced by oxygen deficiency (polaronic absorption band overlaps fundamental edge); reported values range across 2.6–2.8 eV. |
| 63 | `V2O5` | 2.30 | provisional | optical_anisotropy_dichroism | Extreme optical anisotropy along crystallographic $a, b, c$ axes yields disparate absorption edges (2.15 to 2.38 eV); uncorrected for dichroism. |
| 64 | `CuInS2` | 1.53 | provisional | mismatched_doi | Mismatched DOI in original table (resolves to amorphous Si backscattering); primary single-crystal benchmark citation unverified. |
| 65 | `CdSnP2` | 1.17 | provisional | mismatched_doi | Supplied DOI resolves to scanning electron microscopy contrast mechanism, not chalcopyrite optical absorption. |
| 66 | `BeO` | 10.60 | provisional | mismatched_doi_vuv_limit | Supplied DOI resolves to ion implantation study; band gap exceeds standard spectrophotometric accuracy limits. |

---

## 4. Frozen Production Model Evaluation Results

Evaluation was executed deterministically on the frozen model against all 54 eligible records in `reference_benchmark.csv`.

### 4.1 Stratified Quantitative Performance Metrics
| Cohort / Subgroup | Sample Size ($n$) | MAE (eV) | RMSE (eV) | Mean Signed Bias (eV) | Median AE (eV) | Mean Tree Dispersion ($\sigma$) (eV) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Overall Benchmark Set** | **54** | **0.7031** | **0.9201** | **-0.5037** | **0.5420** | **1.2446** |
| **In-Domain Multielement Compounds** | **51** | **0.6625** | **0.8842** | **-0.5553** | **0.5210** | **1.1481** |
| **Elemental Challenge Set (`Si`, `Ge`, `C`)** | **3** | **1.3923** | **1.3957** | **+0.3737** | **1.3530** | **2.8847** |
| **Narrow-Gap Subgroup ($E_g < 1.5\text{ eV}$)** | **14** | **0.2511** | **0.3268** | **-0.0055** | **0.2010** | **0.5901** |
| **Conventional Gap ($1.5\text{–}3.0\text{ eV}$)** | **19** | **0.5283** | **0.6504** | **-0.4214** | **0.5580** | **0.9207** |
| **Wide & Ultrawide Gap ($E_g > 3.0\text{ eV}$)** | **18** | **1.1242** | **1.2982** | **-1.1242** | **1.0890** | **1.8222** |

---

## 5. Key Scientific Findings & Failure Modes

### 5.1 Energy-Dependent Underprediction (The Regression Attenuation Effect)
The benchmark reveals a dramatic, monotonic divergence across band-gap ranges:
- **Narrow-gap semiconductors ($n=14$):** Remarkable fidelity ($\text{MAE} = 0.251\text{ eV}$, bias $-0.006\text{ eV}$). Binary materials like $\text{InAs}$ (error $+0.049\text{ eV}$), $\text{InSb}$ (error $+0.171\text{ eV}$), $\text{PbS}$ (error $+0.133\text{ eV}$), and $\text{CuInSe}_2$ (error $-0.057\text{ eV}$) demonstrate that the model accurately interpolates infrared and near-IR energetics.
- **Conventional semiconductors ($n=19$):** Solid screening performance ($\text{MAE} = 0.528\text{ eV}$, bias $-0.421\text{ eV}$). Prototypical photovoltaics like $\text{GaAs}$ (error $-0.329\text{ eV}$), $\text{InP}$ (error $+0.145\text{ eV}$), $\text{GaP}$ (error $+0.198\text{ eV}$), and $\text{CdS}$ (error $-0.097\text{ eV}$) perform well within typical ML screening tolerances.
- **Wide & Ultrawide semiconductors ($n=18$):** Severe, systematic negative bias ($\text{MAE} = 1.124\text{ eV}$, bias **$-1.124\text{ eV}$**). Every single wide-gap compound is underpredicted. The ensemble leaf averages are bounded by training set distributions, causing severe compression on extreme band gaps:
  - $\text{MgO}$ ($E_g = 7.77\text{ eV}$): Predicted $5.04\text{ eV}$ (Error: $-2.734\text{ eV}$)
  - $\text{AlN}$ ($E_g = 6.20\text{ eV}$): Predicted $3.92\text{ eV}$ (Error: $-2.277\text{ eV}$)
  - $\text{BN}$ ($E_g = 5.96\text{ eV}$): Predicted $4.72\text{ eV}$ (Error: $-1.242\text{ eV}$)
  - $\text{Ga}_2\text{O}_3$ ($E_g = 4.85\text{ eV}$): Predicted $2.96\text{ eV}$ (Error: $-1.888\text{ eV}$)
  - $\text{ZnO}$ ($E_g = 3.37\text{ eV}$): Predicted $1.73\text{ eV}$ (Error: $-1.638\text{ eV}$)

### 5.2 Elemental Semiconductor Degeneracy
The elemental challenge set confirms that single-element materials (`Si`, `Ge`, `C`) fail due to descriptor range/deviation collapse (`Electronegativity_Range = 0.0`, etc.):
- `Si`: Ref $1.12\text{ eV}$, Pred $2.42\text{ eV}$ (Error $+1.296\text{ eV}$, tree spread $\pm 2.108\text{ eV}$)
- `Ge`: Ref $0.66\text{ eV}$, Pred $2.01\text{ eV}$ (Error $+1.353\text{ eV}$, tree spread $\pm 2.957\text{ eV}$)
- `C` (diamond): Ref $5.47\text{ eV}$, Pred $3.94\text{ eV}$ (Error $-1.528\text{ eV}$, tree spread $\pm 3.589\text{ eV}$)
The average tree dispersion on elemental materials ($\pm 2.885\text{ eV}$) is $2.5\times$ higher than in-domain multielement compounds, validating the Phase 1 out-of-domain banner policy.

### 5.3 Polymorphic Blindness
The Phase 2C benchmark explicitly includes polymorph pairs:
1. **$\text{TiO}_2$:** Rutile ($E_g = 3.03\text{ eV}$) and Anatase ($E_g = 3.20\text{ eV}$) receive the identical prediction of $1.890\text{ eV}$.
2. **$\text{SiC}$:** $4\text{H}$ polytype ($E_g = 3.26\text{ eV}$) and $6\text{H}$ polytype ($E_g = 3.02\text{ eV}$) receive the identical prediction of $2.494\text{ eV}$.
3. **$\text{ZnS}$:** Sphalerite cubic ($E_g = 3.68\text{ eV}$) and Wurtzite hexagonal ($E_g = 3.78\text{ eV}$) receive the identical prediction of $2.701\text{ eV}$.
Because Magpie descriptors are purely stoichiometric, the model cannot distinguish crystal symmetry or coordination geometry without structural descriptors.

---

## 6. Recommendations for Future Model Development

With a verified 54-record benchmark now established, future development phases can proceed with sound statistical grounding:
1. **Calibrate Prediction Intervals via Split-Conformal Quantile Regression:** Raw tree dispersion reflects model disagreement but fails to capture the $-1.12\text{ eV}$ wide-gap underprediction bias. Conformal prediction intervals will guarantee rigorous coverage (e.g., 90%).
2. **Incorporate Crystal Symmetry / Structural Descriptors:** Augment composition features with space-group numbers and density to resolve polymorph pairs ($\text{TiO}_2$, $\text{SiC}$, $\text{ZnS}$).
3. **Catalog Matching Overlay in Mode 2 UI:** When a user inputs a canonical semiconductor that exists in the verified benchmark (e.g., `Si`, `GaAs`, `CdTe`), display the experimental reference value prominently alongside the model prediction.
