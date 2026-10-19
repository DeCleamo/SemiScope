"""
Composition and CIF featurization module for SemiScope.
Extracts reduced chemical formula and computes the exact 132 Magpie feature descriptors
matching the trained models.
"""

import sys
import warnings
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from pymatgen.core import Composition

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import MAGPIE_FEATURES

# Lazy load Matminer ElementProperty to keep startup instantaneous
_FEATURIZER = None


def get_featurizer():
    global _FEATURIZER
    if _FEATURIZER is None:
        from matminer.featurizers.composition import ElementProperty
        _FEATURIZER = ElementProperty.from_preset(preset_name="magpie")
        # Enforce single-process execution (n_jobs=1) to prevent [Errno 5] Input/output error
        # caused by multiprocessing Pool pipe communication on macOS / Python 3.13 in Streamlit.
        if hasattr(_FEATURIZER, "set_n_jobs"):
            _FEATURIZER.set_n_jobs(1)
        elif hasattr(_FEATURIZER, "n_jobs"):
            _FEATURIZER.n_jobs = 1
    return _FEATURIZER


# Elements confirmed in the 4,604-record training dataset (all multielement compounds)
TRAINING_ELEMENTS = {
    "Ag", "Al", "As", "Au", "B", "Ba", "Be", "Bi", "Br", "C", "Ca", "Cd", "Ce", "Cl", "Co",
    "Cr", "Cs", "Cu", "Dy", "Er", "Eu", "F", "Fe", "Ga", "Gd", "Ge", "H", "Hf", "Hg", "Ho",
    "I", "In", "Ir", "K", "La", "Li", "Lu", "Mg", "Mn", "Mo", "N", "Na", "Nb", "Nd", "Ni",
    "O", "Os", "P", "Pb", "Pd", "Pm", "Pr", "Pt", "Rb", "Re", "Rh", "Ru", "S", "Sb", "Sc",
    "Se", "Si", "Sm", "Sn", "Sr", "Ta", "Tb", "Tc", "Te", "Th", "Ti", "Tl", "Tm", "U", "V",
    "W", "Xe", "Y", "Yb", "Zn", "Zr"
}

# Elements known to produce unphysical NaN descriptors in Pauling electronegativity or elemental properties
UNSUPPORTED_ELEMENTS = {
    "He", "Ne", "Ar", "Rf", "Db", "Sg", "Bh", "Hs", "Mt", "Ds", "Rg", "Cn", "Nh", "Fl", "Mc", "Lv", "Ts", "Og"
}


def parse_material_input(
    input_val: str,
    is_cif: bool = False
) -> Tuple[str, Composition, Optional[str]]:
    """
    Parses a formula string or CIF file/content into a pymatgen Composition.
    Validates physical plausibility and supported composition domain.
    
    Returns:
        (canonical_formula, composition_obj, warning_msg)
    """
    warning = None
    if not input_val or not isinstance(input_val, str) or not input_val.strip():
        raise ValueError("Invalid material input: Input formula or CIF string cannot be empty.")

    s_clean = input_val.strip()

    if is_cif or s_clean.startswith("data_") or "loop_" in s_clean or "\n" in s_clean:
        from pymatgen.io.cif import CifParser
        try:
            if "\n" not in s_clean and len(s_clean) < 260 and Path(s_clean).exists():
                parser = CifParser(s_clean)
            else:
                parser = CifParser.from_str(s_clean)
            structures = parser.parse_structures(primitive=True)
            if not structures:
                raise ValueError("No valid crystal structures found in CIF file.")
            struct = structures[0]
            comp = struct.composition
            warning = (
                "CIF parsed: 3D crystal geometry discarded. Space group symmetry and lattice parameters are not utilized. "
                "Evaluated purely on compositional Magpie descriptors; polymorph-specific band gaps are not predicted."
            )
        except Exception as e:
            raise ValueError(f"Failed to parse CIF: {e}")
    else:
        try:
            comp = Composition(s_clean)
        except Exception as e:
            raise ValueError(f"Invalid chemical formula '{s_clean}': {e}")

    # Validate elements present (reject DummySpecies or invalid symbol tokens like INVALID123)
    from pymatgen.core.periodic_table import Element
    if not comp.elements or not all(isinstance(el, Element) for el in comp.elements):
        invalid_symbols = [getattr(el, "symbol", str(el)) for el in comp.elements if not isinstance(el, Element)]
        raise ValueError(f"Invalid chemical formula '{s_clean}': Contains unrecognized element symbols {invalid_symbols}.")

    element_symbols = [el.symbol for el in comp.elements]
    unsupported_present = [sym for sym in element_symbols if sym in UNSUPPORTED_ELEMENTS]
    if unsupported_present:
        raise ValueError(
            f"Unsupported elements detected: {', '.join(unsupported_present)}. "
            f"These elements lack verified physical property descriptors in the standard Magpie database."
        )

    # Check for pure elemental composition (OOD for the multielement RF model)
    if len(comp.elements) == 1:
        el_sym = comp.elements[0].symbol
        el_msg = (
            f"Elemental semiconductor / pure element '{el_sym}' detected: The production Random Forest model was "
            f"trained exclusively on multielement compounds (binary, ternary, quaternary). Predictions for single-element "
            f"systems suffer from descriptor range degeneracy and extreme tree variance (out-of-distribution)."
        )
        warning = f"{warning} | {el_msg}" if warning else el_msg

    reduced_formula = comp.reduced_formula
    return reduced_formula, comp, warning


def featurize_composition(comp: Union[str, Composition]) -> pd.DataFrame:
    """
    Computes the 132 Magpie features for a given composition or formula.
    Guarantees column parity and exact order with MAGPIE_FEATURES.
    Rejects feature vectors containing NaNs or infinite values.
    """
    if isinstance(comp, str):
        comp = Composition(comp)

    featurizer = get_featurizer()
    df_temp = pd.DataFrame({"composition": [comp]})
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            feats_df = featurizer.featurize_dataframe(df_temp, "composition", ignore_errors=False, pbar=False)
        except KeyError as e:
            raise ValueError(f"Failed to featurize composition '{comp.reduced_formula}': Missing elemental properties for element {e}.")
        except Exception as e:
            raise ValueError(f"Featurization error for composition '{comp.reduced_formula}': {e}")

    # Drop original composition col
    feats_df.drop(columns=["composition"], inplace=True)

    # Matminer Magpie descriptors match our 132 MAGPIE_FEATURES index for index
    if len(feats_df.columns) == len(MAGPIE_FEATURES):
        feats_df.columns = MAGPIE_FEATURES
    else:
        raise ValueError(f"Feature count mismatch: expected {len(MAGPIE_FEATURES)}, got {len(feats_df.columns)}")

    result_df = feats_df[MAGPIE_FEATURES].copy()

    # Integrity verification: reject NaNs or Infs
    if result_df.isna().any().any():
        nan_cols = result_df.columns[result_df.isna().any()].tolist()
        raise ValueError(f"Featurization produced NaN values in descriptors: {nan_cols[:5]}. Composition is out-of-domain.")
    if np.isinf(result_df.values).any():
        inf_cols = result_df.columns[np.isinf(result_df.values).any(axis=0)].tolist()
        raise ValueError(f"Featurization produced infinite values in descriptors: {inf_cols[:5]}. Composition is out-of-domain.")

    return result_df



if __name__ == "__main__":
    test_formula = "BaTiO3"
    formula, comp, warn = parse_material_input(test_formula)
    print(f"Parsed {test_formula} -> {formula}")
    feats = featurize_composition(comp)
    print(f"Featurized shape: {feats.shape}")
    print(f"Any NaNs: {feats.isna().any().any()}")
    print("Sample features:", feats.iloc[0, :5].to_dict())
