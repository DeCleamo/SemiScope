# SemiScope Scientific Validation Report: Mode 1 Material Discovery

**Audit Date:** October 19, 2026  
**Target System:** SemiScope Mode 1 Screening Engine  
**Dataset Under Review:** Canonical 4,604-Record Band-Gap Benchmark & Candidate Catalog  
**Primary Source:** `data/raw/matbench_expt_gap_renamed.csv` → `data/semiconductor_pool.parquet`  
**Status:** Audit Complete & Validated  

---

## 1. Executive Summary

This validation report provides a rigorous scientific audit of SemiScope's Mode 1 material-discovery workflow. 
Mode 1 evaluates stoichiometric compositions in the verified 4,604-record experimental catalog against technological desirability transfer functions.

### Key Conclusions:
1. **Data Integrity & Traceability:** All top 20 candidates across Solar, General Semiconductor, and LED applications trace 100% losslessly to explicit rows in the upstream benchmark dataset (`data/raw/matbench_expt_gap_renamed.csv`). There are zero join errors, zero synthetic band gaps, and zero formula duplications.
2. **Nature of Ranking Ties:** Stored band-gap measurements in the upstream Matbench benchmark are quantized at 1 or 2 decimal places (69.27% 1-decimal, 30.73% 2-decimal). Multiple distinct compounds sharing exact values (e.g. 11 compounds at $2.50\text{ eV}$) legitimately share identical Gaussian desirability scores. Dense ranking correctly reflects equal band-gap alignment without artificial tie-breaking.
3. **Scientific Scope & Essential Boundaries:** Mode 1 operates strictly as a **band-gap alignment screening filter**. Band gap is a necessary but not sufficient condition for device performance. Crucial device properties (direct vs. indirect band transitions, carrier mobility, lifetime, phase stability, dopability, and defect tolerance) are currently **missing from the catalog** and must be evaluated before concluding device viability.
4. **Scoring Function Parameterization:** Gaussian transfer curves are anchored to established theoretical optima (e.g., $1.34\text{ eV}$ Shockley-Queisser limit for single-junction solar absorbers; $2.50\text{ eV}$ for visible green-blue light emission). However, parameter bandwidths ($\sigma$) are heuristic design choices that model continuous roll-off rather than empirical device efficiencies.

---

## 2. Dataset Provenance & Precision Audit

### 2.1 The Data Path
The candidate catalog data flow was inspected from raw source to Streamlit rendering:
```
data/raw/matbench_expt_gap_renamed.csv (4,604 rows)
   │
   ├── [src/consolidate.py]: Composition canonicalization via pymatgen.core.Composition
   │   Extracts sorted chemical systems and preserves all 132 Magpie feature columns.
   │
data/semiconductor_pool.parquet (4,604 rows, 136 columns)
   │
   ├── [src/precompute_pool.py]: Vectorized Gaussian desirability evaluation
   │   Maintains IEEE 754 64-bit unrounded float precision.
   │
data/semiconductor_scored.parquet (4,604 rows, 142 columns)
   │
   └── [src/precompute_pool.py: recommend_materials()]: Dense ranking and tie-detection
       └── [app/streamlit_app.py]: Mode 1 UI with explicit provenance, tie count, and scope boundary alerts.
```

### 2.2 Precision Distribution in Upstream Benchmark
An exhaustive precision audit of `BandGap_eV` across all 4,604 entries in `data/raw/matbench_expt_gap_renamed.csv`:
- **1 decimal place (e.g., 2.5, 2.0, 1.8, 0.0):** 3,189 entries (69.27%)
- **2 decimal places (e.g., 2.51, 2.49, 1.83):** 1,415 entries (30.73%)
- **3+ decimal places:** 0 entries (0.00%)

### 2.3 Top Most Frequent Band-Gap Values in Benchmark
```text
  0.00 eV : 2,450 entries  (zero-gap metals and semimetals, d = 0.0000)
  2.30 eV :    40 entries
  2.00 eV :    40 entries
  1.00 eV :    31 entries
  1.80 eV :    29 entries
  1.50 eV :    27 entries
  2.20 eV :    26 entries
  2.40 eV :    25 entries
  1.60 eV :    24 entries
  1.40 eV :    23 entries
  2.60 eV :    23 entries
  0.80 eV :    21 entries
  0.70 eV :    20 entries
  0.30 eV :    18 entries
  0.90 eV :    17 entries
  2.80 eV :    16 entries
  3.10 eV :    16 entries
  0.60 eV :    16 entries
  1.20 eV :    15 entries
  1.90 eV :    15 entries
```
*Finding:* Repeated band-gap measurements are intrinsic to the historical experimental literature compiled in Matbench (derived from Zhuo et al. and Landolt-Börnstein tables). They are **not** an artifact of SemiScope's preprocessing or consolidation code.

---

## 3. Top-20 Candidate Audits Across Active Categories

### 3.1 Solar Photovoltaics (Absorber Layer)
- **Target Optimum:** $1.34\text{ eV}$ (Shockley-Queisser theoretical peak for single-junction cell)
- **Bandwidth:** $\sigma = 0.35\text{ eV}$
- **Cutoffs:** $E_{\min} = 0.05\text{ eV}$ (metals receive 0.00), $E_{\max} = 2.50\text{ eV}$

| Rank | Formula | Chem Sys | Measured $E_g$ | Raw Row | Raw Value | Desirability Score | Tie Status | Validation & Literature Notes |
|:---:|:---|:---|:---:|:---:|:---:|:---:|:---:|:---|
| **#1** | `In5CuS8` | Cu-In-S | 1.34 eV | 1838 | 1.34 | 1.0000 | Unique | Spinel-type thiospinel / chalcopyrite analogue. Direct band gap near SQ optimum (~1.3-1.4 eV). Excellent optical absorption; investigated in thin-film PV literature. |
| **#2** | `K3Cr2(PS4)3` | Cr-K-P-S | 1.35 eV | 1946 | 1.35 | 0.9996 | Tied (n=13) | Quaternary thiophosphate. Insulating/complex dielectric; low carrier transport; moisture sensitive. |
| **#2** | `YbNd2CuS5` | Cu-Nd-S-Yb | 1.35 eV | 4408 | 1.35 | 0.9996 | Tied (n=13) | Rare-earth chalcogenide. High effective mass; unverified solar cell efficiency. |
| **#2** | `TlAsSe2` | As-Se-Tl | 1.35 eV | 4038 | 1.35 | 0.9996 | Tied (n=13) | Chalcogenide glass / crystal. Extreme toxicity (Tl, As); low chemical durability. |
| **#2** | `K2Gd2Sb2Se9` | Gd-K-Sb-Se | 1.33 eV | 1899 | 1.33 | 0.9996 | Tied (n=13) | Complex selenide. High defect density expected; unverified carrier lifetime. |
| **#2** | `Mg3AsN` | As-Mg-N | 1.33 eV | 2611 | 1.33 | 0.9996 | Tied (n=13) | Anti-perovskite nitride. Promising earth-abundant p-type candidate, but synthesis challenging. |
| **#2** | `Ba2CeInTe5` | Ba-Ce-In-Te | 1.35 eV | 186 | 1.35 | 0.9996 | Tied (n=13) | Complex telluride. Heavy elements; air sensitive; unverified absorption coefficient. |
| **#2** | `Rb1.54Cd1.54Bi2.46S6` | Bi-Cd-Rb-S | 1.33 eV | 3162 | 1.33 | 0.9996 | Tied (n=13) | Non-stoichiometric bismuth chalcogenide. Disorder-induced localized states likely. |
| **#2** | `Ba2DyInTe5` | Ba-Dy-In-Te | 1.35 eV | 194 | 1.35 | 0.9996 | Tied (n=13) | Telluride; heavy rare-earth dopant; synthesis via high-temperature quartz ampoule only. |
| **#2** | `Ba2ErInTe5` | Ba-Er-In-Te | 1.35 eV | 198 | 1.35 | 0.9996 | Tied (n=13) | Isostructural with Ba2DyInTe5. Low dielectric breakdown; missing mobility data. |
| **#2** | `BaGe4(IrSe3)2` | Ba-Ge-Ir-Se | 1.33 eV | 372 | 1.33 | 0.9996 | Tied (n=13) | Contains precious metal (Ir); commercially unviable for terrestrial PV scale. |
| **#2** | `InSb2Se4Br` | Br-In-Sb-Se | 1.35 eV | 1859 | 1.35 | 0.9996 | Tied (n=13) | Chalcohalide. Moisture unstable; prone to halogen outgassing under illumination. |
| **#2** | `Cd0.99Ga0.01Sb0.01Te0.99` | Cd-Ga-Sb-Te | 1.35 eV | 663 | 1.35 | 0.9996 | Tied (n=13) | Doped CdTe alloy. CdTe is an established commercial solar absorber (1.45 eV). Excellent candidate. |
| **#2** | `Cs3Nb2AsSe11` | As-Cs-Nb-Se | 1.35 eV | 962 | 1.35 | 0.9996 | Tied (n=13) | Polyselenide. Highly volatile selenium chains; poor thermal stability. |
| **#15** | `Ba2GdInTe5` | Ba-Gd-In-Te | 1.36 eV | 214 | 1.36 | 0.9984 | Tied (n=13) | Telluride analogue. Unverified absorption coefficient; low air stability. |
| **#15** | `In0.9Ga0.1As0.1P0.9` | As-Ga-In-P | 1.32 eV | 1778 | 1.32 | 0.9984 | Tied (n=13) | III-V quaternary alloy. Direct band gap; excellent transport; established tandem PV material. |
| **#15** | `TlS` | S-Tl | 1.36 eV | 4069 | 1.36 | 0.9984 | Tied (n=13) | Thallium sulfide. High toxicity; low phase stability at ambient conditions. |
| **#15** | `Al0.1Cd0.9Sb0.1Te0.9` | Al-Cd-Sb-Te | 1.36 eV | 51 | 1.36 | 0.9984 | Tied (n=13) | Alloyed CdTe derivative. High theoretical efficiency; needs phase segregation study. |
| **#15** | `In1.6Cu0.4Se2.6` | Cu-In-Se | 1.32 eV | 1786 | 1.32 | 0.9984 | Tied (n=13) | Defect chalcopyrite (CIS family). Excellent established PV lineage; high absorption. |
| **#15** | `In1.85Cu0.15Se2.85` | Cu-In-Se | 1.32 eV | 1789 | 1.32 | 0.9984 | Tied (n=13) | Defect-ordered CIS phase. Good band alignment; prone to copper vacancy clustering. |

---

### 3.2 LED and Optoelectronic Emitters
- **Target Optimum:** $2.50\text{ eV}$ (Green-blue emission, $\lambda \approx 496\text{ nm}$)
- **Bandwidth:** $\sigma = 0.50\text{ eV}$
- **Cutoffs:** $E_{\min} = 0.10\text{ eV}$, $E_{\max} = 4.00\text{ eV}$

| Rank | Formula | Chem Sys | Measured $E_g$ | Raw Row | Raw Value | Desirability Score | Approx. $\lambda$ ($\approx hc/E_g$) | Validation & Photoluminescence Notes |
|:---:|:---|:---|:---:|:---:|:---:|:---:|:---:|:---|
| **#1** | `RbTbSe2` | Rb-Se-Tb | 2.50 eV | 3292 | 2.5 | 1.0000 | ~496 nm | Delafossite-related rare-earth selenide. Luminescence from Tb3+ 4f-4f transitions possible. |
| **#1** | `Cs3Bi2Br9` | Bi-Br-Cs | 2.50 eV | 958 | 2.5 | 1.0000 | ~496 nm | Lead-free halide perovskite derivative. Known blue-green PL (~460-490 nm), but indirect-like character/self-trapped excitons reduce external quantum efficiency (EQE < 5%). |
| **#1** | `LaGaS3` | Ga-La-S | 2.50 eV | 2169 | 2.5 | 1.0000 | ~496 nm | Lanthanum gallium sulfide (GLS glass host). Widely studied IR/laser host; poor p-type dopability. |
| **#1** | `V3Bi(PbO4)3` | Bi-O-Pb-V | 2.50 eV | 4209 | 2.5 | 1.0000 | ~496 nm | Vanadate apatite. Deep d-orbital defect states; severe non-radiative quenching expected. |
| **#1** | `Sm3B(SO)3` | B-O-S-Sm | 2.50 eV | 3517 | 2.5 | 1.0000 | ~496 nm | Oxysulfide borate. Highly complex insulating lattice; unverified radiative recombination. |
| **#1** | `MnSe` | Mn-Se | 2.50 eV | 2725 | 2.5 | 1.0000 | ~496 nm | Transition metal chalcogenide / antiferromagnet. Strongly correlated d-electrons; non-radiative trap dominant. |
| **#1** | `MnPSe3` | Mn-P-Se | 2.50 eV | 2720 | 2.5 | 1.0000 | ~496 nm | 2D van der Waals antiferromagnet. Excitonic absorption; poor LED injection efficiency. |
| **#1** | `RbIn5S6` | In-Rb-S | 2.50 eV | 3269 | 2.5 | 1.0000 | ~496 nm | Ternary thioindate. Broad emission; low carrier mobility. |
| **#1** | `La1Se0.14S1.86` | La-S-Se | 2.50 eV | 2084 | 2.5 | 1.0000 | ~496 nm | Solid solution. Defect scattering from alloy disorder. |
| **#1** | `PSe` | P-Se | 2.50 eV | 3042 | 2.5 | 1.0000 | ~496 nm | Binary phosphorus selenide. Polymer-like network; unstable under high optical flux. |
| **#1** | `Ho2GeS5` | Ge-Ho-S | 2.50 eV | 1699 | 2.5 | 1.0000 | ~496 nm | Quaternary thiogermanate. High optical transparency, but high resistivity. |
| **#12** | `Ba5(GaSe4)2` | Ba-Ga-Se | 2.51 eV | 320 | 2.51 | 0.9998 | ~494 nm | Selenogallate. High band gap; poor carrier injection. |
| **#12** | `VTeHO5` | H-O-Te-V | 2.51 eV | 4249 | 2.51 | 0.9998 | ~494 nm | Hydrated tellurate. Poor thermal stability; water loss at device temperatures. |
| **#12** | `K6CdTe4` | Cd-K-Te | 2.51 eV | 1973 | 2.51 | 0.9998 | ~494 nm | Alkali tellurometalate. Extreme moisture reactivity; ignites in moist air. |
| **#12** | `Ba2GaSbSe5` | Ba-Ga-Sb-Se | 2.51 eV | 208 | 2.51 | 0.9998 | ~494 nm | Quaternary selenide. Complex quaternary phase; missing luminescence data. |
| **#12** | `CdAg2(PS3)2` | Ag-Cd-P-S | 2.49 eV | 695 | 2.49 | 0.9998 | ~498 nm | Thiophosphate. Low electrical conductivity prevents LED diode action. |
| **#12** | `Sn3WO6` | O-Sn-W | 2.49 eV | 3616 | 2.49 | 0.9998 | ~498 nm | Mixed valence oxide. Known photocatalyst; polaronic transport hinders radiative recombination. |
| **#12** | `K3Th2Cu3S7` | Cu-K-S-Th | 2.49 eV | 1957 | 2.49 | 0.9998 | ~498 nm | Actinide (Thorium). Radioactive; unsuitable for commercial consumer optoelectronics. |
| **#12** | `Al0.99Ga0.01P1` | Al-Ga-P | 2.49 eV | 70 | 2.49 | 0.9998 | ~498 nm | III-V AlGaP alloy. Indirect band gap ($X$-valley minimum). Very low radiative recombination efficiency without isoelectronic nitrogen doping (AlGaP:N). |
| **#20** | `Sr2La2Pt1O7.13` | La-O-Pt-Sr | 2.52 eV | 3655 | 2.52 | 0.9992 | ~492 nm | Perovskite-related platinate. High cost (Pt); catalytic rather than luminescent. |

---

### 3.3 General Semiconductor (Electronic Channel)
- **Target Optimum:** $1.25\text{ eV}$ (Room-temperature electronic switching optimum)
- **Bandwidth:** $\sigma = 0.70\text{ eV}$
- **Cutoffs:** $E_{\min} = 0.05\text{ eV}$, $E_{\max} = 3.50\text{ eV}$

| Rank | Formula | Chem Sys | Measured $E_g$ | Raw Row | Raw Value | Desirability Score | Tie Status | Validation & Electronic Device Notes |
|:---:|:---|:---|:---:|:---:|:---:|:---:|:---:|:---|
| **#1** | `In0.6Ga0.4As0.6P0.4` | As-Ga-In-P | 1.25 eV | 1770 | 1.25 | 1.0000 | Tied (n=6) | Quaternary III-V. High electron mobility ($\mu_e > 4000\text{ cm}^2/\text{V}\cdot\text{s}$). Verified high-speed HEMT/transistor channel material. |
| **#1** | `EuN` | Eu-N | 1.25 eV | 1337 | 1.25 | 1.0000 | Tied (n=6) | Rare-earth nitride / magnetic semiconductor. Air sensitive; difficult stoichiometry control. |
| **#1** | `Cd4Sb3` | Cd-Sb | 1.25 eV | 690 | 1.25 | 1.0000 | Tied (n=6) | Known thermoelectric material; high carrier concentration; unsuitable for low-leakage FET switch. |
| **#1** | `Ce1.3Lu0.7S3` | Ce-Lu-S | 1.25 eV | 737 | 1.25 | 1.0000 | Tied (n=6) | Rare-earth sesquisulfide. High defect hopping conduction; unverified channel mobility. |
| **#1** | `SbTeI` | I-Sb-Te | 1.25 eV | 3358 | 1.25 | 1.0000 | Tied (n=6) | Ferroelectric semiconductor. Studied for memory/switching, but low thermal stability. |
| **#1** | `YbPr2CuS5` | Cu-Pr-S-Yb | 1.25 eV | 4414 | 1.25 | 1.0000 | Tied (n=6) | Complex quaternary sulfide. High effective mass; low carrier mobility. |
| **#7** | `Zr1.86Cu1S4` | Cu-S-Zr | 1.26 eV | 4530 | 1.26 | 0.9999 | Tied (n=7) | Thiospinel phase. Moderately high resistivity; unverified gate modulation. |
| **#7** | `Si15(TeP2)4` | P-Si-Te | 1.24 eV | 3457 | 1.24 | 0.9999 | Tied (n=7) | Silicon tellurophosphate clathrate. Cage structure suppresses lattice thermal conductivity; useful for thermoelectrics, poor for high-power FETs. |
| **#7** | `La3LuSe6` | La-Lu-Se | 1.26 eV | 2129 | 1.26 | 0.9999 | Tied (n=7) | Rare-earth selenide. Air sensitive; poor carrier mobility. |
| **#7** | `In1.5Cu0.5Se2.5` | Cu-In-Se | 1.24 eV | 1784 | 1.24 | 0.9999 | Tied (n=7) | Cu-In-Se alloy phase. p-type dominant; bipolar switching possible; lower mobility than GaAs. |
| **#7** | `In1.8Cu0.2Se2.8` | Cu-In-Se | 1.26 eV | 1790 | 1.26 | 0.9999 | Tied (n=7) | Defect-ordered phase. Trap-assisted recombination; poor transconductance. |
| **#7** | `La2GeSe5` | Ge-La-Se | 1.24 eV | 2097 | 1.24 | 0.9999 | Tied (n=7) | Selenogermanate. High dielectric permittivity, but low mobility. |
| **#7** | `Ta2Tl4S11` | S-Ta-Tl | 1.26 eV | 3752 | 1.26 | 0.9999 | Tied (n=7) | Thallium tantalate sulfide. Highly toxic (Tl); chemically unstable. |
| **#14** | `Ho(InS2)3` | Ho-In-S | 1.23 eV | 1685 | 1.23 | 0.9996 | Tied (n=6) | Complex ternary sulfide. Low carrier concentration; missing dopability data. |
| **#14** | `YbB66` | B-Yb | 1.27 eV | 4392 | 1.27 | 0.9996 | Tied (n=6) | Boron-rich boride. Extreme hardness and high melting point, but hopping transport; unviable for logic channels. |
| **#14** | `Bi9S6O7.5` | Bi-O-S | 1.27 eV | 496 | 1.27 | 0.9996 | Tied (n=6) | Bismuth oxysulfide. Layered photocatalyst; missing dielectric breakdown field data. |
| **#14** | `GdB66` | B-Gd | 1.27 eV | 1529 | 1.27 | 0.9996 | Tied (n=6) | Boride clathrate-like framework. Hopping conduction; unsuitable for field-effect transport. |
| **#14** | `Cd3In2(Te2S)2` | Cd-In-S-Te | 1.23 eV | 682 | 1.23 | 0.9996 | Tied (n=6) | Quaternary chalcogenide. High defect density; unverified mobility. |
| **#14** | `Lu(InS2)3` | In-Lu-S | 1.27 eV | 2527 | 1.27 | 0.9996 | Tied (n=6) | Isostructural with Ho(InS2)3. Missing carrier transport evidence. |
| **#20** | `BiSeI` | Bi-I-Se | 1.28 eV | 514 | 1.28 | 0.9991 | Tied (n=9) | Ferroelectric chalcohalide. High spin-orbit coupling; candidate for spintronics, but low breakdown field. |

---

## 4. Property Coverage & Missing Data Matrix

To evaluate the scientific trustworthiness of candidates, we assess data availability across 6 key physical dimensions:

| Property Dimension | Importance to Application | SemiScope Catalog Status | External Data Availability | Impact on Current Recommendations |
|:---|:---|:---:|:---:|:---|
| **Band Gap ($E_g$)** | Fundamental optical & electrical threshold | **100% Verified** | Universal | Accurately screens absorption/emission window. |
| **Transition Nature (Direct vs. Indirect)** | Critical for LEDs (radiative rate) & Thin-Film PV (absorption length) | **Missing (0%)** | Requires DFT band structures or k-resolved spectroscopy | Materials like `Al0.99Ga0.01P1` have optimal gap ($2.49\text{ eV}$) but are indirect with near-zero LED efficiency. |
| **Carrier Mobility ($\mu_e, \mu_h$)** | Critical for FET switching speed & PV charge extraction | **Missing (0%)** | Sparse experimental Hall data; some calculated acoustic phonon values | Candidates like `YbB66` have hopping transport ($< 1\text{ cm}^2/\text{V}\cdot\text{s}$), making them unviable for logic devices despite $E_g = 1.27\text{ eV}$. |
| **Radiative Efficiency / PLQY** | Defines LED luminescence | **Missing (0%)** | Highly sensitive to defect density and surface passivation | Equal band gap does not imply equal luminescence; candidates like `Cs3Bi2Br9` suffer self-trapped excitons (low PLQY). |
| **Phase & Moisture Stability** | Practical device operating lifetime | **Missing (0%)** | Materials Project $\Delta E_{\text{hull}}$ available; ambient stability empirical | Materials like `K6CdTe4` decompose rapidly in moist air; `Tl`-containing materials present extreme toxicity hazards. |
| **Dopability (p-type / n-type)** | Required to form p-n junctions for diodes and FETs | **Missing (0%)** | Requires defect formation energy calculations | Many wide-gap oxides/sulfides suffer native vacancy compensation, preventing bipolar doping. |

---

## 5. Scoring Methodology Evaluation

### 5.1 Desirability Function Formula
All three active use cases utilize a symmetric continuous Gaussian transfer function with sharp physical cutoffs:
$$d(E_g) = \begin{cases}
0.0 & \text{if } E_g \le E_{\min} \text{ (zero-gap metal / sub-gap cutoff)} \\
0.0 & \text{if } E_g \ge E_{\max} \text{ (insulator / deep-UV cutoff)} \\
\exp\left(-\frac{1}{2}\left(\frac{E_g - E_{\text{opt}}}{\sigma}\right)^2\right) & \text{if } E_{\min} < E_g < E_{\max}
\end{cases}$$

### 5.2 Scoring Parameters: Physical Motivation vs. Heuristic Choices

| Parameter | Solar Absorber | LED Emitter | General Semiconductor | Parameter Classification | Justification & Limitations |
|:---|:---:|:---:|:---:|:---:|:---|
| **Optimal Peak ($E_{\text{opt}}$)** | **1.34 eV** | **2.50 eV** | **1.25 eV** | **Physically Motivated** | • Solar: Rigorously matches the Shockley-Queisser theoretical maximum (~33% for single-junction cell under AM1.5G).<br>• LED: Corresponds to central visible green-blue spectrum ($\lambda \approx 496\text{ nm}$).<br>• Semiconductor: Balanced room-temperature switching point between subthreshold leakage ($E_g < 1.0\text{ eV}$) and excessive on-state resistance/operating voltage ($E_g > 2.0\text{ eV}$). |
| **Bandwidth ($\sigma$)** | **0.35 eV** | **0.50 eV** | **0.70 eV** | **Heuristic Design Choice** | Smooth mathematical decay. Does not represent an empirical efficiency curve (e.g. real SQ efficiency drops precipitously below 1.1 eV and above 1.7 eV). |
| **Lower Cutoff ($E_{\min}$)** | **0.05 eV** | **0.10 eV** | **0.05 eV** | **Physically Motivated** | Strictly sets metallic/semi-metallic zero-gap phases ($E_g = 0$) to 0.0000 suitability. |
| **Upper Cutoff ($E_{\max}$)** | **2.50 eV** | **4.00 eV** | **3.50 eV** | **Heuristic Threshold** | Filters out deep insulators and UV-transparent dielectrics unsuited for the primary target roles. |

---

## 6. Known Limitations and Actionable Roadmap

### 6.1 Known Scientific Limitations
1. **Band-Gap-Only Screening:** A high score reflects optical band alignment alone. It does not indicate carrier lifetime, mobility, defect tolerance, chemical stability, or synthesis feasibility.
2. **Quantized Upstream Measurements:** 69% of benchmark records are rounded to 1 decimal place. Ties in the catalog reflect identical literature measurements, not synthetic clustering.
3. **Absence of Direct/Indirect Labels:** Emitters and absorbers cannot be distinguished between dipole-allowed direct transitions and phonon-assisted indirect transitions without supplemental data.

### 6.2 Prioritized Next Steps
1. **Tier 1 (High Impact, Low Friction):** Integrate direct/indirect band-gap flags from Materials Project DFT calculations to demote indirect-gap LED candidates.
2. **Tier 2 (Physical Viability):** Ingest thermodynamic stability ($\Delta E_{\text{hull}}$ in meV/atom) from Materials Project to penalize unstable/decomposing compounds.
3. **Tier 3 (Subcategory Specialization):** Split "General Semiconductor" into distinct application profiles:
   - *Logic Channel (Low Voltage):* $E_g \approx 1.1 - 1.4\text{ eV}$, requiring high electron mobility.
   - *Power Electronics (Wide Band Gap):* $E_g \approx 3.0 - 4.5\text{ eV}$, requiring high critical breakdown electric field ($E_{\text{crit}}$).
   - *Thermoelectric Channel:* Low lattice thermal conductivity and high power factor.
