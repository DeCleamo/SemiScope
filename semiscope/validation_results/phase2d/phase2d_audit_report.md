# SemiScope Phase 2D: Independent Benchmark Source Audit Report

**Audit Phase:** Phase 2D  
**Timestamp:** 2026-10-19T11:15:00Z  
**Audit Scope:** Independent bibliographic, physical-measurement, and metadata verification of all 54 records from the Phase 2C external benchmark (`validation_results/phase2c/reference_benchmark.csv`), reconciliation of SHA-256 signatures, recomputation of model validation metrics on verified eligible records, and readiness assessment.

---

## Executive Summary

Phase 2D was initiated to conduct an **independent source-level audit** of the Phase 2C external reference benchmark prior to any model development, retraining, or architecture modifications. While Phase 2C verified structural integrity, schema adherence, and basic HTTP DOI resolution, a deep scientific and bibliographic audit revealed that **DOI resolution alone is insufficient to substantiate scientific validity**.

### Key Findings:
1. **Bibliographic & Citation Errors (15 Records Downgraded/Excluded):**
   - **Mismatched DOIs / Unrelated Papers (10 records):** 10 records had DOIs resolving to entirely different physical phenomena or unrelated materials:
     - `GaP` (#8): DOI resolved to L. M. Roth (1960) on donor spin-lattice relaxation and g-factors in Ge/Si, not GaP absorption.
     - `AlSb` (#11): DOI resolved to P. P. Debye & E. M. Conwell (1954) on N-type Germanium.
     - `SnO2` (#22): DOI resolved to D. M. Brown & R. Bray (1962) on lattice scattering in p-type Germanium.
     - `Cu2O` (#23): DOI resolved to J. K. Furdyna & M. E. Brodwin (1961) on Faraday ellipticity.
     - `Fe2O3` (#26): DOI resolved to S. Y. Yoon et al. (2000) on low-temperature Ni-silicide crystallization of amorphous Si.
     - `BiFeO3` (#27): DOI resolved to H. W. Jang et al. (2008) on dielectric fatigue/leakage, not optical transitions.
     - `KTaO3` (#30): DOI resolved to G. Rupprecht & R. O. Bell (1964) on dielectric constants in paraelectric perovskites, not optical band gap.
     - `Mg2Sn` (#33): DOI resolved to R. G. Morris et al. (1958) on Mg2Si, not Lipson & O Connor on Mg2Sn.
     - `Bi2Se3` (#34): DOI resolved to M. Cardona & D. L. Greenaway (1964) on IV-VI semiconductors, not Greenaway & Harbeke on Bi2Se3.
     - `SiC` 4H (#51): DOI resolved to T. Walter et al. (1996) on Cu(In,Ga)Se2 admittance spectroscopy, not Choyke & Patrick on 4H-SiC.
   - **Perovskite Mismatched Citations (3 records):** The DOI assigned to `CsPbBr3` (#44), `CsPbI3` (#45), and `CsPbCl3` (#46) (`10.1021/ja411014k`) resolves to Christians et al. *JACS* 2013 (*"An Inorganic Hole Conductor for Organo-Lead Halide Perovskite Solar Cells"*), which investigated CuI and CsSnI3 as hole transport layers for solar cells, rather than Stoumpos et al.'s crystallographic characterization of cesium lead halides.
   - **Dimensional / Bulk vs. Monolayer Discrepancies (2 records):** `WS2` (#36) and `MoSe2` (#37) cited publications that measured 2D monolayers (Gutiérrez et al. measuring direct 1.95 eV photoluminescence in monolayer WS2 flakes, and Jin et al. on monolayer MoSe2 transport), whereas the benchmark claimed bulk indirect gaps (1.35 eV and 1.10 eV).
2. **Review Articles & Compilations Mislabeled as Primary Experiments (7 Records Reclassified):**
   - 7 records (`InP` #5, `GaN` #6, `AlN` #7, `InAs` #9, `ZnO` #12, `Ga2O3` #21, and `CH3NH3PbI3` #47) cited prominent, highly cited review papers or consensus compilations (e.g., Vurgaftman, Meyer & Ram-Mohan 2001 JAP; Özgür et al. 2005 JAP; Pearton et al. 2018 APR; Green et al. 2014 Nature Photonics). These provide high-confidence consensus values at 300 K, but are secondary compilations rather than primary experimental reports. They have been reclassified to **`verified_secondary`**.
3. **Legitimate Multi-Compound Studies with Shared DOIs (Verified):**
   - Shared DOIs were independently inspected. Shay, Tell & Kasper (1973 *Phys. Rev. B* 7, 4485) legitimately measured 4 chalcopyrites simultaneously (`CuGaS2` #39, `AgGaS2` #40, `AgGaSe2` #41, `AgInSe2` #42). Van Elp et al. (1991 *Phys. Rev. B* 44, 1530) legitimately measured both `NiO` (#24) and `CoO` (#25). Cardona & Harbeke (1965 *Phys. Rev.* 137, A1467) measured both sphalerite (#53) and wurtzite (#54) polymorphs of `ZnS`. These shared DOIs were substantiated and retained.
4. **Target Shortfall & Honest Evidence Enforcement:**
   - With 15 defective records excluded and 7 records reclassified as secondary, the **eligible verified benchmark contains 39 records** (32 `verified_primary`, 7 `verified_secondary`).
   - This represents an **11-record shortfall** against the Phase 2C target of >= 50 verified records.
   - In strict compliance with instructions, the evidence standard was **not relaxed** to artificially reach 50 records.

---

## 1. SHA-256 Hash Reconciliation & Structural vs. Scientific Integrity

### Structural Tests vs. Scientific Source Verification
The automated verification script in Phase 2C (`verify_benchmark_integrity.py`) checked:
1. Production model and training dataset freeze (SHA-256 matches).
2. Completeness (no empty cells, all columns present, positive band gaps).
3. Purity against the internal column value (`evidence_tier != 'provisional'`).
4. Recomputation of summary metrics against `model_evaluation_results.csv`.

**Critical Distinction:** The script tested **structural integrity and data pipeline determinism**, but **did not perform scientific source verification**. It verified that the CSV had 54 non-empty rows and that the text in the `evidence_tier` column read `verified_primary`, but could not verify whether the cited DOI actually described the material or whether the paper was a review or an original experiment.

### SHA-256 Reconciliation
- **Physical file SHA-256** (`validation_results/phase2c/reference_benchmark.csv`):  
  `b404a4c5861fe4e4b810e7b3bddc24765d6655bc65ca0e9a906b82f599b16e42`
- **Phase 2C Manifest SHA-256** (`benchmark_manifest.json`):  
  `b404a4c5861fe4e4b810e7b3bddc24765d6655bc65ca0e9a906b82f599b16e42`
- **Phase 2C Curation Report Text SHA-256** (`curation_report.md`):  
  `3a4f6bb8fbc923a1050e64f89d977e2ffb234479599ea78f8cb339c908581895`

**Explanation of Mismatch:**  
The physical benchmark CSV and the machine-readable manifest agree with 100% precision (`b404a4c5...`). The hash recorded in the narrative text of `curation_report.md` (`3a4f6bb8...`) was generated during an intermediate draft of the benchmark before final column formatting, and the markdown narrative was not updated prior to freezing Phase 2C. The physical file was preserved unchanged.

---

## 2. Audit Record Breakdown

Across the 66 total candidate records audited (54 Phase 2C benchmark records + 12 Phase 2C excluded records):

| Evidence Tier | Total Candidate Count | Retained in Benchmark | Excluded / Downgraded | Description |
| :--- | :---: | :---: | :---: | :--- |
| **`verified_primary`** | 32 | **32** | 0 | Original experimental measurement directly inspected and supported. |
| **`verified_secondary`** | 7 | **7** | 0 | High-confidence review or consensus compilation supporting 300 K band gap. |
| **`provisional`** | 16 | 0 | 16 | 5 from P2C benchmark (monolayers / perovskites) + 11 from P2C excluded. |
| **`unresolved`** | 11 | 0 | 11 | 10 from P2C benchmark (mismatched DOIs/papers) + 1 from P2C excluded (In2O3 dispute). |
| **Total** | **66** | **39** | **27** | Eligible benchmark: **39 records** (Shortfall: 11 records). |

---

## 3. Detailed Audit of Excluded and Downgraded Records (15 Records from Phase 2C Benchmark)

The following 15 records from `validation_results/phase2c/reference_benchmark.csv` failed independent source verification and have been moved to `validation_results/phase2d/excluded_or_downgraded_records.csv`:

| ID | Formula | Claimed Eg (eV) | Cited DOI | Resolved Publication & Discrepancy Reason | New Tier | Decision |
| :---: | :--- | :---: | :--- | :--- | :---: | :--- |
| **8** | `GaP` | 2.26 | `10.1103/PhysRev.118.1534` | Resolves to L. M. Roth (1960), *g-Factor and Donor Spin-Lattice Relaxation for Electrons in Germanium and Silicon*. Unrelated to GaP absorption edge spectrum. | `unresolved` | Excluded |
| **11** | `AlSb` | 1.62 | `10.1103/PhysRev.93.693` | Resolves to P. P. Debye & E. M. Conwell (1954), *Electrical Properties of N-Type Germanium*. Unrelated to AlSb. | `unresolved` | Excluded |
| **22** | `SnO2` | 3.60 | `10.1103/PhysRev.127.1593` | Resolves to D. M. Brown & R. Bray (1962), *Analysis of Lattice and Ionized Impurity Scattering in p-Type Germanium*. Unrelated to SnO2. | `unresolved` | Excluded |
| **23** | `Cu2O` | 2.17 | `10.1103/PhysRev.124.740` | Resolves to J. K. Furdyna & M. E. Brodwin (1961), *Dependence of the Free-Carrier Faraday Ellipticity in Semiconductors on Scattering Mechanisms*. Unrelated to Cu2O exciton absorption. | `unresolved` | Excluded |
| **26** | `Fe2O3` | 2.20 | `10.1063/1.371906` | Resolves to S. Y. Yoon et al. (2000), *Structural and electrical properties of polycrystalline silicon produced by low-temperature Ni silicide mediated crystallization*. Unrelated to hematite. | `unresolved` | Excluded |
| **27** | `BiFeO3` | 2.74 | `10.1063/1.2842418` | Resolves to H. W. Jang et al. (2008), *Epitaxial (001) BiFeO3 membranes with substantially reduced fatigue and leakage*. Investigates fatigue and leakage, not sub-band-gap optical transitions. | `unresolved` | Excluded |
| **30** | `KTaO3` | 3.64 | `10.1103/PhysRev.135.A748` | Resolves to G. Rupprecht & R. O. Bell (1964), *Dielectric Constant in Paraelectric Perovskites*. Does not measure the fundamental optical absorption edge of KTaO3. | `unresolved` | Excluded |
| **33** | `Mg2Sn` | 0.36 | `10.1103/PhysRev.109.1909` | Resolves to R. G. Morris et al. (1958), *Semiconducting Properties of Mg2Si Single Crystals*. Measures Mg2Si, not Mg2Sn. | `unresolved` | Excluded |
| **34** | `Bi2Se3` | 0.35 | `10.1103/PhysRev.133.A1685` | Resolves to M. Cardona & D. L. Greenaway (1964), *Optical Properties and Band Structure of Group IV-VI and Group V Materials*. Covers PbS/PbSe/PbTe and Bi/Sb/As, not Bi2Se3. | `unresolved` | Excluded |
| **36** | `WS2` | 1.35 | `10.1021/nl3026357` | Resolves to H. R. Gutiérrez et al. (2012), *Extraordinary Room-Temperature Photoluminescence in Triangular WS2 Monolayers*. Measures 2D monolayer direct gap (1.95 eV), not bulk indirect gap. | `provisional` | Excluded |
| **37** | `MoSe2` | 1.10 | `10.1103/PhysRevB.90.045422` | Resolves to Z. Jin et al. (2014), *Intrinsic transport properties of electrons and holes in monolayer transition-metal dichalcogenides*. Theoretical/monolayer transport study, not bulk crystal band gap. | `provisional` | Excluded |
| **44** | `CsPbBr3` | 2.36 | `10.1021/ja411014k` | Resolves to J. A. Christians et al. (2013), *An Inorganic Hole Conductor for Organo-Lead Halide Perovskite Solar Cells*. Investigates CuI/CsSnI3 hole transport layers, not CsPbBr3 band gap. | `provisional` | Excluded |
| **45** | `CsPbI3` | 2.82 | `10.1021/ja411014k` | Resolves to J. A. Christians et al. (2013) on CuI/CsSnI3 hole conductors. Does not measure yellow/black CsPbI3 band gaps. | `provisional` | Excluded |
| **46** | `CsPbCl3` | 3.03 | `10.1021/ja411014k` | Resolves to J. A. Christians et al. (2013) on CuI/CsSnI3 hole conductors. Does not report CsPbCl3 band gap. | `provisional` | Excluded |
| **51** | `SiC` (4H) | 3.26 | `10.1063/1.363401` | Resolves to T. Walter et al. (1996), *Determination of defect distributions from admittance measurements and application to Cu(In,Ga)Se2 based heterojunctions*. Unrelated to 4H-SiC. | `unresolved` | Excluded |

---

## 4. Retained and Verified Benchmark Records (39 Records)

The 39 substantiated records forming `validation_results/phase2d/corrected_benchmark.csv`:

| ID | Formula | Eg (eV) | Transition | Phase / Space Group | Tier | Primary / Secondary Citation | Verified Location |
| :---: | :--- | :---: | :---: | :--- | :---: | :--- | :--- |
| **1** | `Si` | 1.12 | indirect | diamond cubic ($Fd\bar{3}m$) | `verified_primary` | [G. G. Macfarlane (1958)](https://doi.org/10.1103/PhysRev.111.1245) | Table I, p. 1249 |
| **2** | `Ge` | 0.66 | indirect | diamond cubic ($Fd\bar{3}m$) | `verified_primary` | [W. C. Dash (1955)](https://doi.org/10.1103/PhysRev.99.1151) | Fig. 4, p. 1153 |
| **3** | `C` | 5.47 | indirect | diamond cubic ($Fd\bar{3}m$) | `verified_primary` | [H. R. Phillip (1964)](https://doi.org/10.1103/PhysRev.136.A1445) | Section IV, p. A1448 |
| **4** | `GaAs` | 1.42 | direct | zincblende ($F\bar{4}3m$) | `verified_primary` | [M. D. Sturge (1962)](https://doi.org/10.1103/PhysRev.127.768) | Fig. 6, p. 772 |
| **5** | `InP` | 1.34 | direct | zincblende ($F\bar{4}3m$) | `verified_secondary` | [I. Vurgaftman (2001)](https://doi.org/10.1063/1.1368156) | Table I, p. 2483 |
| **6** | `GaN` | 3.44 | direct | wurtzite ($P6_3mc$) | `verified_secondary` | [I. Vurgaftman (2001)](https://doi.org/10.1063/1.1368156) | Table III, p. 2487 |
| **7** | `AlN` | 6.20 | direct | wurtzite ($P6_3mc$) | `verified_secondary` | [I. Vurgaftman (2001)](https://doi.org/10.1063/1.1368156) | Table III, p. 2487 |
| **9** | `InAs` | 0.35 | direct | zincblende ($F\bar{4}3m$) | `verified_secondary` | [I. Vurgaftman (2001)](https://doi.org/10.1063/1.1368156) | Table I, p. 2483 |
| **10** | `InSb` | 0.18 | direct | zincblende ($F\bar{4}3m$) | `verified_primary` | [M. Tanenbaum (1953)](https://doi.org/10.1103/PhysRev.91.1561.2) | Fig. 1, p. 1562 |
| **12** | `ZnO` | 3.37 | direct | wurtzite ($P6_3mc$) | `verified_secondary` | [U. Ozgur (2005)](https://doi.org/10.1063/1.1992666) | Section II, p. 041301-4 |
| **13** | `ZnSe` | 2.70 | direct | zincblende ($F\bar{4}3m$) | `verified_primary` | [R. H. Bube (1958)](https://doi.org/10.1103/PhysRev.110.1040) | Table I, p. 1042 |
| **14** | `ZnTe` | 2.26 | direct | zincblende ($F\bar{4}3m$) | `verified_primary` | [R. E. Dietz (1962)](https://doi.org/10.1103/PhysRevLett.8.391) | p. 392 |
| **15** | `CdS` | 2.42 | direct | wurtzite ($P6_3mc$) | `verified_primary` | [D. G. Thomas (1959)](https://doi.org/10.1103/PhysRev.116.573) | Section III, p. 576 |
| **16** | `CdSe` | 1.74 | direct | wurtzite ($P6_3mc$) | `verified_primary` | [L. T. Chadderton (1962)](https://doi.org/10.1016/0022-3697(62)90110-5) | Table 1, p. 270 |
| **17** | `CdTe` | 1.50 | direct | zincblende ($F\bar{4}3m$) | `verified_primary` | [D. T. F. Marple (1964)](https://doi.org/10.1063/1.1713411) | Table III, p. 541 |
| **18** | `PbS` | 0.41 | direct | rocksalt ($Fm\bar{3}m$) | `verified_primary` | [A. F. Gibson (1952)](https://doi.org/10.1088/0370-1301/65/7/516) | Fig. 2, p. 520 |
| **19** | `TiO2` | 3.03 | direct | rutile ($P4_2/mnm$) | `verified_primary` | [D. C. Cronemeyer (1952)](https://doi.org/10.1103/PhysRev.87.876) | Fig. 5, p. 880 |
| **20** | `TiO2` | 3.20 | indirect | anatase ($I4_1/amd$) | `verified_primary` | [H. Tang (1993)](https://doi.org/10.1016/0038-1098(93)90427-O) | Fig. 2, p. 849 |
| **21** | `Ga2O3` | 4.85 | direct | monoclinic ($C2/m$) | `verified_secondary` | [S. J. Pearton (2018)](https://doi.org/10.1063/1.5006941) | Table I, p. 011301-4 |
| **24** | `NiO` | 3.70 | direct | rocksalt ($Fm\bar{3}m$) | `verified_primary` | [J. van Elp (1991)](https://doi.org/10.1103/PhysRevB.44.1530) | Table III, p. 1535 |
| **25** | `CoO` | 2.60 | direct | rocksalt ($Fm\bar{3}m$) | `verified_primary` | [J. van Elp (1991)](https://doi.org/10.1103/PhysRevB.44.1530) | Table II, p. 1534 |
| **28** | `BaTiO3` | 3.20 | direct | tetragonal ($P4mm$) | `verified_primary` | [M. Cardona (1965)](https://doi.org/10.1103/PhysRev.140.A651) | Fig. 4, p. A654 |
| **29** | `SrTiO3` | 3.25 | indirect | cubic perovskite ($Pm\bar{3}m$) | `verified_primary` | [M. Cardona (1965)](https://doi.org/10.1103/PhysRev.140.A651) | Fig. 6, p. A656 |
| **31** | `Mg2Si` | 0.77 | indirect | antifluorite ($Fm\bar{3}m$) | `verified_primary` | [R. G. Morris (1958)](https://doi.org/10.1103/PhysRev.109.1909) | p. 1912 |
| **32** | `Mg2Ge` | 0.69 | indirect | antifluorite ($Fm\bar{3}m$) | `verified_primary` | [R. D. Redin (1958)](https://doi.org/10.1103/PhysRev.109.1916) | p. 1919 |
| **35** | `MoS2` | 1.29 | indirect | hexagonal ($P6_3/mmc$, 2H) | `verified_primary` | [K. F. Mak (2010)](https://doi.org/10.1103/PhysRevLett.105.136805) | Fig. 2, p. 136805-2 |
| **38** | `CuInSe2` | 1.04 | direct | chalcopyrite ($I\bar{4}2d$) | `verified_primary` | [P. Migliorato (1974)](https://doi.org/10.1063/1.1655162) | Fig. 1, p. 435 |
| **39** | `CuGaS2` | 2.43 | direct | chalcopyrite ($I\bar{4}2d$) | `verified_primary` | [J. L. Shay (1973)](https://doi.org/10.1103/PhysRevB.7.4485) | Table I, p. 4488 |
| **40** | `AgGaS2` | 2.73 | direct | chalcopyrite ($I\bar{4}2d$) | `verified_primary` | [J. L. Shay (1973)](https://doi.org/10.1103/PhysRevB.7.4485) | Table I, p. 4488 |
| **41** | `AgGaSe2` | 1.83 | direct | chalcopyrite ($I\bar{4}2d$) | `verified_primary` | [J. L. Shay (1973)](https://doi.org/10.1103/PhysRevB.7.4485) | Table I, p. 4488 |
| **42** | `AgInSe2` | 1.24 | direct | chalcopyrite ($I\bar{4}2d$) | `verified_primary` | [J. L. Shay (1973)](https://doi.org/10.1103/PhysRevB.7.4485) | Table I, p. 4488 |
| **43** | `Cs2AgBiBr6` | 2.05 | indirect | double perovskite ($Fm\bar{3}m$) | `verified_primary` | [A. H. Slavney (2016)](https://doi.org/10.1021/jacs.5b13294) | Fig. 2, p. 2139 |
| **47** | `CH3NH3PbI3` | 1.55 | direct | tetragonal ($I4/mcm$) | `verified_secondary` | [M. A. Green (2014)](https://doi.org/10.1038/nphoton.2014.134) | Box 1, p. 507 |
| **48** | `BAs` | 1.82 | indirect | zincblende ($F\bar{4}3m$) | `verified_primary` | [S. Li (2018)](https://doi.org/10.1126/science.aat8982) | Fig. 1, p. 576 |
| **49** | `BN` | 5.96 | direct | hexagonal ($P6_3/mmc$) | `verified_primary` | [K. Watanabe (2004)](https://doi.org/10.1038/nmat1134) | Fig. 2, p. 405 |
| **50** | `MgO` | 7.77 | direct | rocksalt ($Fm\bar{3}m$) | `verified_primary` | [D. M. Roessler (1967)](https://doi.org/10.1103/PhysRev.159.733) | Fig. 1, p. 735 |
| **52** | `SiC` (6H) | 3.02 | indirect | hexagonal ($P6_3mc$, 6H) | `verified_primary` | [W. J. Choyke (1957)](https://doi.org/10.1103/PhysRev.105.1721) | Fig. 3, p. 1723 |
| **53** | `ZnS` (sph.) | 3.68 | direct | zincblende sphalerite ($F\bar{4}3m$) | `verified_primary` | [M. Cardona (1965)](https://doi.org/10.1103/PhysRev.137.A1467) | Table I, p. A1470 |
| **54** | `ZnS` (wurt.) | 3.78 | direct | wurtzite ($P6_3mc$) | `verified_primary` | [M. Cardona (1965)](https://doi.org/10.1103/PhysRev.137.A1467) | Table I, p. A1470 |

---

## 5. Model Evaluation Metrics Recomputation (Corrected Benchmark)

Metrics were recomputed strictly from the record-level evaluation errors of the 39 verified eligible records:

| Evaluation Group | Sample Size ($N$) | MAE (eV) | RMSE (eV) | Mean Signed Error (eV) | Median AE (eV) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Overall Corrected Benchmark** | **39** | **0.7799** | **1.0076** | **-0.5209** | **0.5970** |
| **In-Domain Multielement** | **36** | **0.7288** | **0.9683** | **-0.5954** | **0.5420** |
| **Elemental Challenge (Si, Ge, C)** | **3** | **1.3923** | **1.3957** | **+0.3737** | **1.3530** |

### Comparison with Phase 2C Reported Metrics:
- Phase 2C overall reported MAE (n=54): `0.7811 eV` (RMSE `1.0371 eV`).
- Corrected Phase 2D overall MAE (n=39): `0.7799 eV` (RMSE `1.0076 eV`).
- The general error profile remains consistent: the model exhibits an underestimation bias on multielement wide-bandgap insulators, and severe catastrophic failure on elemental semiconductors (Silicon error +1.296 eV, Diamond error -1.528 eV, Germanium error +1.353 eV).

---

## 6. Verification Artifacts Generated

All Phase 2D deliverables have been created in `validation_results/phase2d/`:
1. `source_verification_matrix.csv`: Complete audit of all 66 records with DOI resolution, title matching, author matching, source type, evidence tier, and eligibility decision.
2. `corrected_benchmark.csv`: The 39 substantiated, verified records (32 primary, 7 secondary).
3. `excluded_or_downgraded_records.csv`: The 27 excluded/downgraded records (15 from Phase 2C benchmark + 12 original Phase 2C exclusions).
4. `phase2d_integrity_checks.json`: Machine-readable integrity check file with exact counts, reconciled SHA-256 hashes, recomputed metrics, and audit decisions.
5. `phase2d_audit_report.md`: This comprehensive report.

---

## 7. Official Phase 2D Decision

### Final Verdict: `READY_FOR_EXTERNAL_DIAGNOSTIC`

#### Scientific Rationale:
1. **Target Shortfall Prevents Model Development Decisions:**  
   The primary benchmark target of >= 50 verified records has not been achieved (current eligible count: 39 records, shortfall of 11). Pursuant to the explicit constraints of Phase 2D, the evidence standard was not relaxed. Therefore, the system is **`NOT` ready for model-development or retraining decisions** until curation expands the verified pool to >= 50 materials.
2. **Readiness for Diagnostic Assessment:**  
   The 39 remaining records represent an immaculate, independently substantiated ground-truth testbed. Every record has been verified to resolve directly to the authentic physical measurement or consensus review compilation at 300 K. This clean reference set is fully qualified and **`READY_FOR_EXTERNAL_DIAGNOSTIC`** evaluation.
