"""
Explainability engine for SemiScope.
Utilizes SHAP TreeExplainer on demand to extract physical feature attributions,
maps technical Magpie descriptors into intuitive chemical properties,
and synthesizes fluent natural-language explanations.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import numpy as np
if not hasattr(np, "obj2sctype"):
    np.obj2sctype = lambda x: np.dtype(x).type

import pandas as pd
import shap

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import MAGPIE_FEATURES
from src.features import parse_material_input, featurize_composition
from src.scoring import load_model, get_candidate_pool, _POOL_INDEX
from src.registry import REGISTRY, get_use_case
from src.typography import format_formula_html

# Cache TreeExplainer instances
_EXPLAINERS: Dict[str, shap.TreeExplainer] = {}

# Clean feature name mapping
FEATURE_NAME_MAP = {
    "AtomicNumber": "Atomic Number",
    "MendeleevNumber": "Mendeleev Periodic Position",
    "AtomicWeight": "Atomic Weight",
    "MeltingPoint": "Melting Point",
    "PeriodicColumn": "Periodic Table Group",
    "PeriodicRow": "Periodic Table Period",
    "CovalentRadius": "Covalent Radius",
    "Electronegativity": "Pauling Electronegativity",
    "sValenceElectrons": "s-Valence Electron Count",
    "pValenceElectrons": "p-Valence Electron Count",
    "dValenceElectrons": "d-Valence Electron Count",
    "fValenceElectrons": "f-Valence Electron Count",
    "TotalValenceElectrons": "Total Valence Electrons",
    "sUnfilledSlots": "s-Orbital Unfilled Slots",
    "pUnfilledSlots": "p-Orbital Unfilled Slots",
    "dUnfilledSlots": "d-Orbital Unfilled Slots",
    "fUnfilledSlots": "f-Orbital Unfilled Slots",
    "TotalUnfilledSlots": "Total Unfilled Electron Slots",
    "GroundStateVolumePerAtom": "Atomic Volume per Atom",
    "ElementBandGap": "Constituent Element Band Gap",
    "GroundStateMagneticMoment": "Magnetic Moment",
    "SpaceGroupNumber": "Elemental Space Group Symmetry"
}

STAT_MAP = {
    "Min": "Minimum",
    "Max": "Maximum",
    "Range": "Spread / Range",
    "Mean": "Average",
    "AvgDev": "Mean Deviation",
    "Mode": "Most Frequent"
}


def humanize_feature_name(raw_name: str) -> str:
    """Converts raw Magpie feature names like 'Electronegativity_Mean' into plain English."""
    parts = raw_name.split("_")
    base = parts[0]
    stat = parts[1] if len(parts) > 1 else ""

    h_base = FEATURE_NAME_MAP.get(base, base)
    h_stat = STAT_MAP.get(stat, stat)

    if h_stat:
        return f"{h_stat} {h_base}"
    return h_base


def get_tree_explainer(target_key: str) -> shap.TreeExplainer:
    global _EXPLAINERS
    if target_key not in _EXPLAINERS:
        model, _ = load_model(target_key)
        _EXPLAINERS[target_key] = shap.TreeExplainer(model)
    return _EXPLAINERS[target_key]


def explain_prediction(
    material_input: str,
    target_key: str,
    top_k: int = 4,
    precomputed_feats: Optional[pd.DataFrame] = None
) -> Dict[str, Any]:
    """
    Computes SHAP feature importance for a single material prediction.
    """
    canonical_formula, comp, _ = parse_material_input(material_input)
    if precomputed_feats is not None:
        feats_df = precomputed_feats
    else:
        feats_df = featurize_composition(comp)

    explainer = get_tree_explainer(target_key)
    X = feats_df[MAGPIE_FEATURES].values
    shap_vals = explainer(X).values[0]

    # Rank features by absolute impact
    top_indices = np.argsort(np.abs(shap_vals))[::-1][:top_k]

    drivers = []
    for idx in top_indices:
        raw_feat = MAGPIE_FEATURES[idx]
        impact = float(shap_vals[idx])
        val = float(feats_df.iloc[0][raw_feat])
        friendly_name = humanize_feature_name(raw_feat)

        direction = "increased" if impact > 0 else "decreased"
        drivers.append({
            "feature": raw_feat,
            "friendly_name": friendly_name,
            "value": round(val, 2),
            "impact": round(impact, 3),
            "direction": direction
        })

    return {
        "material": canonical_formula,
        "target_key": target_key,
        "base_value": float(explainer.expected_value),
        "drivers": drivers
    }


def synthesize_explanation(scoring_result: Dict[str, Any]) -> str:
    """
    Produces a concise, scientifically accurate natural-language narrative
    explaining why a material earned its score for a specific use case.
    """
    mat = scoring_result["material"]
    mat_html = format_formula_html(mat)
    uc_id = scoring_result["use_case_id"]
    uc_name = scoring_result["use_case_name"]
    score = scoring_result["score"]
    tag = scoring_result["tag"]
    props = scoring_result["properties"]
    verdict = scoring_result["verdict"]

    lines = []

    # 1. Provenance & Score Header
    if tag == "measured":
        prop_summaries = [f"{k} = {v['value']} eV (measured experimental)" for k, v in props.items()]
        lines.append(f"**{mat_html}** receives a suitability score of **{score:.2f} ({verdict})** for {uc_name} based on verified experimental data: {', '.join(prop_summaries)}.")
    else:
        prop_summaries = [f"predicted {k} = {v['value']} eV (ensemble tree spread ±{v['std']})" for k, v in props.items()]
        lines.append(f"**{mat_html}** is predicted with **{score:.2f} suitability ({verdict})** for {uc_name} ({', '.join(prop_summaries)}).")

    # 2. Key Physical Drivers via SHAP (for primary predicted model)
    primary_pred_key = None
    for k, v in props.items():
        if v["tag"] == "predicted":
            primary_pred_key = k
            break

    if primary_pred_key:
        try:
            exp = explain_prediction(mat, primary_pred_key, top_k=3)
            driver_phrases = []
            for d in exp["drivers"]:
                driver_phrases.append(f"{d['friendly_name'].lower()} ({d['impact']:+.2f} eV)")
            if driver_phrases:
                lines.append(f"Top statistical model feature attributions (SHAP, not causal physical mechanisms) were: {', '.join(driver_phrases)}.")
        except Exception:
            pass

    # 3. Application-specific context and explicit scientific boundaries
    bg_val = props.get("bandgap", {}).get("value", 0.0)

    if uc_id == "solar":
        if score >= 0.7:
            lines.append("The band gap falls within the optimal Shockley-Queisser single-junction absorption window (1.0–1.8 eV). Candidate for further optical absorption and transport characterization.")
        elif bg_val > 1.8:
            lines.append("The band gap exceeds 1.8 eV, which is too wide for optimal single-junction terrestrial solar absorption.")
        else:
            lines.append("The band gap is sub-optimal (<1.0 eV), causing severe thermalization losses under the AM1.5 solar spectrum.")
    elif uc_id == "semiconductor":
        if score >= 0.7:
            lines.append("The band gap falls in the standard electronic switching window (0.2–2.8 eV). Dopability, breakdown voltage, and carrier mobilities must be evaluated experimentally.")
        elif bg_val > 2.8:
            lines.append("Wide band gap; potentially suited for wide-bandgap power electronics or insulating applications rather than standard switching.")
        else:
            lines.append("Very narrow band gap (<0.2 eV); high thermal leakage current expected at room temperature.")
    elif uc_id == "led":
        if score >= 0.7:
            lines.append("The band gap corresponds to visible or near-UV photon energy (2.0–3.2 eV). Note: Direct vs. indirect band gap is unclassified in this model; indirect gaps will have low emission efficiency.")
        elif bg_val > 3.2:
            lines.append("Deep UV energy range; requires specialized transparent contact and substrate technologies.")
        else:
            lines.append("Emits in the near-infrared spectrum rather than the targeted visible/near-UV optoelectronic window.")
    elif uc_id == "quantum_superconductor":
        if score >= 0.7:
            lines.append("High critical temperature combined with normal-state zero gap makes this a candidate for further exploration.")
        else:
            lines.append("Does not meet concurrent metallic normal state (gap ≈ 0) and high Tc criteria.")
    elif uc_id == "stability_screen":
        lines.append("Formation enthalpy indicates thermodynamic stability against decomposition into constituent elements.")

    return " ".join(lines)
