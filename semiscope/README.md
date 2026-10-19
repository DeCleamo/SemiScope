# SemiScope: Explainable Semiconductor Materials Discovery

> **One scoring engine, two front doors — focused on semiconductor band-gap screening.**

SemiScope is an explainable materials discovery framework refocused on stoichiometric semiconductor compositions and crystal structures. It evaluates materials against specific semiconductor technological requirements:
- **Solar Photovoltaics (Absorber)**: Shockley-Queisser optimal absorption window ($1.0 - 1.8\text{ eV}$).
- **General Electronics (Switching)**: Electronic channel switching window ($0.2 - 2.8\text{ eV}$).
- **Optoelectronics / LEDs (Emitters)**: Visible to near-UV emission window ($2.0 - 3.2\text{ eV}$).

---

## 1. Verified Data Foundation

The canonical foundation for all semiconductor training and active candidate screening is the verified **4,604-record experimental Band-Gap Benchmark and Candidate Catalog**:
- **Dataset Composition**: Exactly 4,604 stoichiometric compositions with complete experimental labels ($E_g$ range: $0.0 - 11.7\text{ eV}$, zero null values).
  - **Zero-gap (metallic / semi-metallic)**: 2,450 records ($53.2\%$). These receive a score of $0.00$ in semiconductor, solar, and LED application screens.
  - **Non-zero band gap (semiconducting / insulating)**: 2,154 records ($46.8\%$). These form the candidate space for semiconductor discovery.
- **Source of Truth**: `cleaned_semiconductor.csv` / `data/raw/matbench_expt_gap_renamed.csv` (100% identical compositions and targets in identical sequence).
- **Primary Candidate Catalog**: `data/semiconductor_pool.parquet` (4,604 verified candidate materials, fully annotated with 132 Magpie descriptors and ground-truth experimental measurements).
- **Archived Multi-Domain Pool**: `data/pool.parquet` (21,562 materials preserved for multi-domain reference; strictly decoupled from primary candidate screening).

---

## 2. Model Architecture & Grouped-CV Validation

Cross-validation splits are partitioned strictly by **chemical system** (unique elemental sets), eliminating optimistic data leakage from doped or stoichiometric near-duplicates:

| Model Architecture | Feature Representation | Grouped $R^2$ (Mean ± Std) | Grouped MAE (eV) | Model Complexity |
|---|---|---|---|---|
| **Baseline Decision Tree** | 6 Compositional Features | $0.285 \pm 0.047$ | $0.774 \pm 0.046$ | Low (single tree, depth=4) |
| **Tuned Decision Tree** | 6 Compositional Features | $0.315 \pm 0.068$ | $0.675 \pm 0.040$ | Low (single tree, depth=8) |
| **Random Forest Baseline** | 6 Compositional Features | $0.497 \pm 0.056$ | $0.584 \pm 0.024$ | Moderate (100 trees, depth=15) |
| **Production Random Forest** | **132 Magpie Descriptors** | **$0.658 \pm 0.033$** | **$0.469 \pm 0.016$** | High (100 trees, depth=20, 2.75 MB) |

*Decision*: The 132-feature Random Forest model provides a **+37.3 percentage point improvement in $R^2$** and reduces MAE from $0.774\text{ eV}$ to $0.469\text{ eV}$ compared to the 6-feature baseline. It is selected as the primary production model.

---

## 3. Product Workflows

### Mode 1: Application → Device/Role → Component → Ranked Candidates (From Verified Catalog)
Screen and rank across the canonical **4,604-record Band-Gap Benchmark and Candidate Catalog** in sub-10 milliseconds:
- **Ranking Source**: Mode 1 rankings use **verified experimental band-gap measurements** ($E_g$ in eV) stored in the candidate catalog.
- **Zero-gap materials**: Metallic compositions ($E_g = 0.00\text{ eV}$) evaluate to a desirability score of $0.00$ and are never presented as viable semiconductor candidates.
- **Hierarchy**:
  1. **Solar Photovoltaics** $\to$ Single-Junction Cell $\to$ Absorber Layer ($1.0 - 1.8\text{ eV}$).
  2. **General Electronics** $\to$ FET / Power Switch $\to$ Channel ($0.2 - 2.8\text{ eV}$).
  3. **Optoelectronics** $\to$ Solid-State Emitter $\to$ Radiative Quantum Well ($2.0 - 3.2\text{ eV}$).

### Mode 2: Material Characterization (Arbitrary Formula / CIF → Model Predicted & Scored Suitability)
Characterize an arbitrary chemical formula or uploaded `.cif` file across active semiconductor applications:
- **On-the-fly Prediction**: Generates band-gap predictions using the 132-feature Random Forest model. If the input formula matches a catalog entry, exact experimental ground truth is prioritized.
- **Provenance & Units**: Every property displays whether it is `measured experimental` ($0.0\text{ uncertainty}$) or `model predicted` ($E_g$ in eV with ensemble tree dispersion $\pm \sigma_{\text{trees}}$ in eV).
- **Desirability Primitive**: Bounded suitability score $\mathcal{S} \in [0, 1]$ (continuous desirability transfer function, not a probability).
- **Physical Explainability**: Feature attributions generated on demand via SHAP `TreeExplainer`.

---

## 4. Directory Structure

```
semiscope/
├── data/
│   ├── raw/
│   │   └── matbench_expt_gap_renamed.csv    # Canonical 4,604 experimental bandgap dataset
│   ├── semiconductor_pool.parquet           # Primary 4,604 Band-Gap Benchmark & Candidate Catalog
│   ├── semiconductor_scored.parquet         # Precomputed scores for 4,604 candidate catalog
│   ├── pool.parquet                         # Archived 21,562 multi-domain candidate pool
│   └── pool_scored.parquet                  # Archived precomputed pool scores
├── models/
│   └── bandgap/                             # Serialized 132-feature RF ensemble & metadata.json
├── src/
│   ├── config.py                            # Paths, constants, and Magpie feature schema
│   ├── consolidate.py                       # Semiconductor catalog & pool builder
│   ├── features.py                          # 132 Magpie featurizer (Matminer) & CIF parser
│   ├── train.py                             # Grouped-CV training & model serialization
│   ├── registry.py                          # Semiconductor criteria & desirability transfer functions
│   ├── scoring.py                           # Unified scoring engine & ensemble dispersion
│   ├── explain.py                           # SHAP TreeExplainer & scientific narrative generator
│   ├── precompute_pool.py                   # High-speed precomputations for candidate retrieval
│   └── api.py                               # FastAPI REST service
├── app/
│   └── streamlit_app.py                     # Dual-mode semiconductor interactive UI
├── tests/
│   └── test_semiscope.py                    # Automated test suite (8/8 passing)
├── Dockerfile                               # Containerization
└── requirements.txt
```

---

## 5. Quickstart

### 1. Launch the Streamlit Web UI
```bash
streamlit run app/streamlit_app.py
```
Open your browser at `http://localhost:8501`.

### 2. Launch the FastAPI REST Service
```bash
python3 src/api.py
```
Open interactive Swagger docs at `http://127.0.0.1:8000/docs`.

### 3. Run Automated Tests
```bash
python3 tests/test_semiscope.py
```

---

## 6. Scientific Governance & Scope Boundaries

1. **Band-Gap Alone Is Not Device Performance**: A predicted band gap within a desired range indicates band alignment feasibility only. It does **not** establish carrier mobility, dopability, recombination lifetime, direct vs. indirect gap, or device power conversion efficiency.
2. **Direct vs. Indirect Band Gap Limitation**: The experimental dataset lacks momentum-space direct vs. indirect band gap annotations. Indirect-gap semiconductors will exhibit poor LED emission efficiency.
3. **CIF Geometry Discard**: When a CIF is provided, 3D structural geometry and symmetry coordinates are discarded with an explicit notification. All predictions are composition-based via 132 Magpie elemental descriptors.
4. **Ensemble Dispersion vs. Confidence Intervals**: Tree variance across the Random Forest ensemble represents estimator spread ($\pm \sigma_{\text{trees}}$), not calibrated confidence intervals or posterior probabilities.
5. **Deferred Non-Semiconductor Tracks**: Superconducting qubit films, insulating dielectrics, redox formation enthalpies, and thermoelectric figure-of-merit screening are archived and deactivated from the primary semiconductor workflow.

