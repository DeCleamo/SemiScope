import os
import json
from pathlib import Path

# Base paths
SRC_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SRC_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
MODELS_DIR = PROJECT_ROOT / "models"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Datasets metadata
RAW_DATASETS = {
    "bandgap": {
        "file": RAW_DATA_DIR / "matbench_expt_gap_renamed.csv",
        "formula_col": "Composition",
        "target_col": "BandGap_eV",
        "target_name": "Band Gap (eV)"
    },
    "tc": {
        "file": RAW_DATA_DIR / "metallic_cluster_superconductivity.csv",
        "formula_col": "composition",
        "target_col": "Tc",
        "target_name": "Tc (K)"
    },
    "enthalpy": {
        "file": RAW_DATA_DIR / "redox_cluster_formation_enthalpy.csv",
        "formula_col": "formula",
        "target_col": "e_form expt",
        "target_name": "Formation Enthalpy (eV/atom)"
    },
    "zt": {
        "file": RAW_DATA_DIR / "thermoelectric_cluster.csv",
        "formula_col": "composition",
        "target_col": "zT",
        "target_name": "Figure of Merit (zT)"
    }
}

# 132 Magpie feature names
MAGPIE_FEATURES_FILE = SRC_DIR / "magpie_features.json"
if MAGPIE_FEATURES_FILE.exists():
    with open(MAGPIE_FEATURES_FILE, "r") as f:
        MAGPIE_FEATURES = json.load(f)
else:
    MAGPIE_FEATURES = []

POOL_FILE = DATA_DIR / "pool.parquet"
POOL_CSV = DATA_DIR / "pool.csv"

# Primary semiconductor catalog (4,604 verified materials)
SEMICONDUCTOR_POOL_FILE = DATA_DIR / "semiconductor_pool.parquet"
SEMICONDUCTOR_POOL_CSV = DATA_DIR / "semiconductor_pool.csv"

# Random state
RANDOM_SEED = 42

