"""
SemiScope Dual-Mode Interactive Materials Discovery Web Application.
Built with Streamlit and styled for modern, premium scientific UX.
"""

import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import numpy as np
if not hasattr(np, "obj2sctype"):
    np.obj2sctype = lambda x: np.dtype(x).type

# Ensure semiscope path is available
app_dir = Path(__file__).resolve().parent
project_root = app_dir.parent
sys.path.insert(0, str(project_root))

from src.registry import REGISTRY, list_use_cases, get_use_case
from src.scoring import score_material_all_usecases, score_material_for_usecase, get_candidate_pool
from src.precompute_pool import recommend_materials
from src.explain import synthesize_explanation, explain_prediction
from src.typography import format_formula_html

# Page setup
st.set_page_config(
    page_title="SemiScope | Computational Materials Screening",
    page_icon="S",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for high-end aesthetic
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;650;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
        color: #172B3A !important;
    }

    .stApp {
        background-color: #F7F8F6 !important;
    }

    /* Typography Specifications */
    .app-header-title {
        font-size: 30px !important;
        font-weight: 650 !important;
        color: #172B3A !important;
        letter-spacing: -0.02em;
        margin: 0 0 2px 0;
        line-height: 1.2;
    }

    .app-header-tagline {
        font-size: 15px !important;
        font-style: italic;
        color: #287D78 !important;
        margin: 0 0 4px 0;
    }

    .app-header-sub {
        font-size: 14px !important;
        color: #71808A !important;
        margin: 0 0 12px 0;
        line-height: 1.4;
    }

    .section-title {
        font-size: 21px !important;
        font-weight: 600 !important;
        color: #172B3A !important;
        margin: 16px 0 8px 0;
    }

    .card-title {
        font-size: 15px !important;
        font-weight: 600 !important;
        color: #172B3A !important;
    }

    .body-text {
        font-size: 14px !important;
        font-weight: 400 !important;
        color: #172B3A !important;
    }

    .caption-text {
        font-size: 12px !important;
        font-weight: 400 !important;
        color: #71808A !important;
    }

    .metric-value-large {
        font-size: 30px !important;
        font-weight: 600 !important;
        color: #172B3A !important;
        line-height: 1.1;
    }

    /* Clean Surface Containers */
    .clean-surface {
        background: #FFFFFF;
        border: 1px solid #E1E6E4;
        border-radius: 6px;
        padding: 14px 18px;
        margin-bottom: 12px;
    }

    .workflow-card {
        background: #FFFFFF;
        border: 1px solid #E1E6E4;
        border-radius: 6px;
        padding: 16px;
        height: 100%;
    }

    /* Badges & Tags */
    .badge-ref {
        background: #F0FDF4;
        color: #166534;
        padding: 2px 7px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 500;
        border: 1px solid #DCFCE7;
        display: inline-block;
    }

    .badge-pred {
        background: #F7F8F6;
        color: #172B3A;
        padding: 2px 7px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 500;
        border: 1px solid #E1E6E4;
        display: inline-block;
    }

    .badge-xgb {
        background: #F0FDFA;
        color: #0F766E;
        padding: 2px 7px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 500;
        border: 1px solid #CCFBF1;
        display: inline-block;
    }

    /* Callout & Explanation boxes */
    .info-callout {
        background: #FFFFFF;
        border: 1px solid #E1E6E4;
        border-left: 3px solid #287D78;
        border-radius: 4px;
        padding: 10px 14px;
        font-size: 13px;
        line-height: 1.5;
        color: #172B3A;
        margin-top: 8px;
    }

    /* Streamlit Button Restyling */
    .stButton > button {
        background-color: #287D78 !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        border: none !important;
        border-radius: 4px !important;
        padding: 6px 16px !important;
    }

    .stButton > button:hover {
        background-color: #20635F !important;
    }
</style>
""", unsafe_allow_html=True)


# Header Section
st.markdown("""
<div class="clean-surface" style="margin-bottom: 12px;">
    <div class="app-header-title">SemiScope</div>
    <div class="app-header-tagline">Semiconductor discovery, powered by materials intelligence.</div>
    <div class="app-header-sub">Screen known materials or predict band gaps for new compositions.</div>
</div>
""", unsafe_allow_html=True)

with st.expander("About the model & methodology"):
    st.markdown("""
    SemiScope integrates a canonical **4,604-record experimental band-gap benchmark** with composition-based machine learning.
    
    - **Features**: 132 Magpie elemental physical and electronic descriptors derived strictly from chemical stoichiometry.
    - **Production Model**: 100-tree Random Forest regressor trained with grouped-CV leakage-free composition splitting.
    - **Auxiliary Benchmark Booster**: 5-fold cross-validated XGBoost gradient-boosted ensemble.
    - **Scope & Limitations**: Band-gap suitability reflects electronic window alignment only (e.g. AM1.5 solar spectrum absorption, logic switching off-state current leakage, or radiative photon emission). It does not evaluate carrier mobilities, dopability, dielectric breakdown, or thermal stability. Uncalibrated ensemble tree spread indicates model dispersion, not a formal confidence interval.
    """)
# Navigation / Mode Toggle
mode = st.radio(
    "Select Workflow:",
    [
        "Catalog Screening (Rank verified experimental materials by application)",
        "AI Prediction (Predict band gap and explain features for any composition)"
    ],
    horizontal=True
)

st.markdown("---")

# ==============================================================================
# MODE 1: APPLICATION -> DEVICE/ROLE -> COMPONENT -> RANKED CANDIDATES
# ==============================================================================
if "Catalog" in mode:
    st.markdown('<div class="section-title">Catalog Screening</div>', unsafe_allow_html=True)
    st.caption("Screen known materials from the 4,604-record verified benchmark by application suitability.")

    # Application Hierarchy mapping
    HIERARCHY = {
        "solar": {
            "application": "Solar Photovoltaics",
            "role": "Single-Junction PV Cell",
            "component": "Photoactive Absorber Layer",
            "target_window": "Optimum: 1.34 eV (Shockley-Queisser Peak), Window: 0.70 – 2.20 eV",
            "limitations": "Band gap evaluates the optical absorption window only. Does NOT establish carrier diffusion lengths, mobility, recombination lifetime, or device cell efficiency."
        },
        "semiconductor": {
            "application": "General Electronics",
            "role": "Field-Effect Transistor (FET) / Power Switch",
            "component": "Semiconductor Channel",
            "target_window": "Optimum: 1.25 eV (Room-Temp Switching Peak), Window: 0.05 – 3.50 eV",
            "limitations": "Band gap evaluates the electronic window for switching (zero-gap metals receive 0.00 score). Dopability (n/p type), dielectric breakdown, and thermal conductivity require separate experimental validation."
        },
        "led": {
            "application": "Optoelectronics / Solid-State Lighting",
            "role": "Visible / Near-UV Light Emitter",
            "component": "Active Radiative Quantum Well / Emitter",
            "target_window": "Optimum: 2.50 eV (Visible Emission Peak), Window: 1.60 – 3.60 eV",
            "limitations": "Dataset lacks direct vs. indirect band gap classification. Indirect-gap semiconductors exhibit low radiative emission efficiency without phonon assistance."
        }
    }

    c1, c2, c3 = st.columns([1.5, 1, 1])

    with c1:
        selected_uc_id = st.selectbox(
            "Select Target Application & Technological Role:",
            options=list(HIERARCHY.keys()),
            format_func=lambda x: f"{HIERARCHY[x]['application']} → {HIERARCHY[x]['component']}",
            index=0
        )

    with c2:
        top_n = st.slider("Number of Candidates (Top N):", min_value=5, max_value=50, value=15, step=5)

    with c3:
        catalog_choice = st.selectbox(
            "Candidate Catalog:",
            ["Canonical 4,604 Band-Gap Catalog", "Archived 21.5k Multi-Domain Pool"],
            index=0,
            help="Defaults to the verified 4,604-record band-gap benchmark catalog (2,154 semiconductors/insulators and 2,450 zero-gap materials). The archived 21.5k pool includes non-semiconductor compositions."
        )
        use_full_pool = ("Archived" in catalog_choice)

    h_info = HIERARCHY[selected_uc_id]
    uc_info = get_use_case(selected_uc_id)

    # Architectural Hierarchy Banner
    st.markdown(f"""
    <div style="background: #f1f5f9; border-left: 4px solid #3b82f6; padding: 0.9rem 1.2rem; border-radius: 8px; margin-bottom: 1.2rem;">
        <div style="font-size: 0.95rem; font-weight: 600; color: #1e293b;">
            Application: <span style="color: #2563eb;">{h_info['application']}</span> &nbsp;|&nbsp; 
            Device/Role: <span style="color: #475569;">{h_info['role']}</span> &nbsp;|&nbsp; 
            Component: <span style="color: #0f172a;">{h_info['component']}</span>
        </div>
        <div style="font-size: 0.85rem; color: #475569; margin-top: 0.3rem;">
            <strong>Target Window:</strong> {h_info['target_window']} &nbsp;|&nbsp; Evidence Level: <strong>{uc_info.evidence_level}</strong>
        </div>
        <div style="font-size: 0.8rem; color: #991b1b; margin-top: 0.3rem;">
            <em>Scope Boundary: {h_info['limitations']}</em>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Fetch recommendations
    with st.spinner("Querying candidate catalog..."):
        candidates = recommend_materials(
            use_case_id=selected_uc_id,
            top_n=top_n,
            measured_only=False,
            use_full_pool=use_full_pool
        )

    st.markdown(f"### Top {len(candidates)} Band-Gap-Aligned Candidate Materials")
    st.caption("Candidates are ranked strictly by unrounded internal band-gap desirability. Scores are displayed to 4 decimal places to diagnose ties. Tied candidates share the same rank because ranking reflects band-gap alignment alone. Equal desirability scores do not imply equal device performance, luminescence efficiency, or carrier mobility.")

    for cand in candidates:
        rank_num = cand.get("rank", 1)
        score_val = cand.get("score", 0.0)
        score_disp = cand.get("score_display", round(score_val, 4))
        score_pct = int(min(1.0, max(0.0, score_val)) * 100)
        tag_badge = '<span class="tag-measured">MEASURED EXPERIMENTAL</span>' if cand["tag"] == "measured" else '<span class="tag-predicted">MODEL PREDICTED</span>'

        # Tie badge
        if cand.get("is_tied", False):
            tie_badge = f'<span class="badge-tied">TIED ({cand.get("tie_count", 2)} materials)</span>'
        else:
            tie_badge = '<span class="badge-unique">UNIQUE SCORE</span>'

        # Score interpretation
        if score_val >= 0.90:
            verdict_text = "Optimal Band-Gap Alignment"
            verdict_color = "#065f46"
        elif score_val >= 0.70:
            verdict_text = "Strong Band-Gap Alignment"
            verdict_color = "#15803d"
        elif score_val >= 0.40:
            verdict_text = "Moderate Viability"
            verdict_color = "#b45309"
        else:
            verdict_text = "Sub-optimal / Edge Alignment"
            verdict_color = "#991b1b"

        # Band-gap deviation narrative
        bg_val = cand["resolved_bandgap"]
        bg_narrative = ""
        if bg_val is not None:
            # Check target for selected use case
            opt_targets = {"solar": 1.34, "semiconductor": 1.25, "led": 2.50}
            target_opt = opt_targets.get(selected_uc_id, 1.34)
            delta = bg_val - target_opt
            if abs(delta) < 0.01:
                bg_narrative = f"Experimental band gap ({bg_val:.2f} eV) matches the application theoretical optimum ({target_opt:.2f} eV) exactly."
            elif delta > 0:
                bg_narrative = f"Experimental band gap ({bg_val:.2f} eV) is +{delta:.2f} eV above the optimum ({target_opt:.2f} eV), yielding {score_disp:.4f} suitability."
            else:
                bg_narrative = f"Experimental band gap ({bg_val:.2f} eV) is {delta:.2f} eV below the optimum ({target_opt:.2f} eV), yielding {score_disp:.4f} suitability."

        formula_html = format_formula_html(cand['formula'])

        with st.container():
            st.markdown(f"""
            <div class="card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <div style="display: flex; align-items: center; gap: 0.75rem;">
                        <span style="font-size: 1.25rem; font-weight: 800; color: #1e293b;">#{rank_num}</span>
                        <span style="font-size: 1.3rem; font-weight: 700; color: #0f172a;">{formula_html}</span>
                        <span style="color: #64748b; font-size: 0.85rem;">(System: {cand['chem_sys']})</span>
                    </div>
                    <div style="display: flex; align-items: center;">{tag_badge} {tie_badge}</div>
                </div>
                <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 0.75rem;">
                    <div style="flex-grow: 1;">
                        <div style="background-color: #f1f5f9; border-radius: 6px; height: 10px; overflow: hidden;">
                            <div style="background: linear-gradient(90deg, #059669 0%, #10b981 100%); width: {score_pct}%; height: 100%;"></div>
                        </div>
                    </div>
                    <span style="font-weight: 800; font-size: 1.15rem; color: {verdict_color};">{score_disp:.4f}</span>
                    <span style="font-size: 0.82rem; font-weight: 600; color: {verdict_color};">({verdict_text})</span>
                </div>
            """, unsafe_allow_html=True)

            # Property chips & narrative
            chips = []
            if bg_val is not None:
                provenance_str = "measured experimental" if cand["tag"] == "measured" else "predicted"
                chips.append(f"Band Gap: <strong>{bg_val:.2f} eV</strong> ({provenance_str})")
            if selected_uc_id == "led" and bg_val is not None and bg_val > 0:
                approx_wl = 1239.84 / bg_val
                chips.append(f"Approx. Peak Photon Energy Emission: <strong>~{approx_wl:.0f} nm</strong> <em>(rough photon-energy conversion: λ ≈ hc/Eg)</em>")
            if bg_narrative:
                chips.append(f"<span style='color: #475569;'>{bg_narrative}</span>")

            st.markdown(" • ".join(chips), unsafe_allow_html=True)

            # Scientific Evidence & Data Coverage (Band-Gap Energy primary field)
            provenance_label = "Verified Measured Ground Truth" if cand["tag"] == "measured" else "Model Predicted Value"
            st.markdown(f"""
            <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 0.6rem 0.9rem; margin-top: 0.6rem; font-size: 0.8rem;">
                <div style="font-weight: 600; color: #334155; margin-bottom: 0.2rem;">Scientific Evidence & Data Coverage:</div>
                <div style="color: #475569;">
                    <strong>Band-Gap Energy:</strong> {provenance_label} ({bg_val:.2f} eV)
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Scope boundary alert for each candidate
            st.markdown(f"""
            <div style="background: #fffbeb; border: 1px solid #fef3c7; border-radius: 6px; padding: 0.5rem 0.8rem; margin-top: 0.5rem; font-size: 0.78rem; color: #92400e;">
                <strong>Band-Gap Scope Boundary:</strong> Band-gap-aligned candidate. Overall device suitability has not been established because additional material and device properties (mobility, recombination lifetime, dopability, and thermal conductivity) have not been evaluated.
            </div>
            """, unsafe_allow_html=True)

            # On-demand explanation toggle
            with st.expander("Mechanistic Explanation & Limitations"):
                s_dict = score_material_for_usecase(cand["formula"], uc_info)
                expl = synthesize_explanation(s_dict)
                st.write(expl)
                st.caption(f"**Scientific Limitation:** {h_info['limitations']}")

            st.markdown("</div>", unsafe_allow_html=True)

# ==============================================================================
# MODE 2: MATERIAL -> USE CASES
# ==============================================================================
else:
    st.subheader("Mode 2: Characterize Chemical Composition / CIF across Semiconductor Applications")
    st.caption("Input an arbitrary chemical composition or CIF file to generate on-the-fly 132-feature Random Forest band-gap predictions, tree dispersion spreads, and SHAP physical drivers.")

    # Mode 2 banner clarifying predictive nature and scientific boundaries
    st.info(r"**Mode 2 Overview:** Generates **model predictions on arbitrary formulas** using the 132-feature Random Forest regressor. The 4,604-record benchmark catalog consists of **multielement compounds**; single-element systems (e.g. Si, Ge) are out-of-domain and trigger uncertainty warnings. Uncertainty is reported as **uncalibrated ensemble tree dispersion** ($\pm \sigma_{\\text{trees}}$), not a confidence interval. A predicted band gap within a target window indicates band alignment feasibility only; **it does not establish carrier mobility, dopability, recombination lifetime, or device efficiency**.")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("#### Material Input")
        input_type = st.radio("Input Format:", ["Chemical Formula", "CIF Structure"], horizontal=True)

        formula_input = ""
        cif_content = None

        if input_type == "Chemical Formula":
            @st.cache_data
            def get_dropdown_options():
                pool = get_candidate_pool(use_full_pool=False)
                bench_p = project_root / "validation_results" / "phase2d" / "corrected_benchmark.csv"
                bench_df = pd.read_csv(bench_p) if bench_p.exists() else pd.DataFrame()
                
                bench_meta = {}
                if not bench_df.empty:
                    for _, r in bench_df.iterrows():
                        f = str(r["formula"]).strip()
                        tier_label = "primary verified" if r["evidence_tier"] == "verified_primary" else "secondary verified"
                        bench_meta[f] = f"{float(r['band_gap_eV']):.2f} eV [{tier_label}]"
                
                pool_meta = {}
                for _, r in pool.iterrows():
                    f = str(r["formula"]).strip()
                    bg = r.get("measured_bandgap")
                    if pd.notna(bg):
                        pool_meta[f] = f"{float(bg):.2f} eV [measured catalog]"
                    else:
                        pool_meta[f] = "[catalog]"

                priority_list = ["GaAs", "Si", "CdTe", "TiO2", "GaN", "InP", "AlN", "ZnSe", "ZnTe", "In5CuS8"]
                opts = []
                f_map = {}

                for f in priority_list:
                    if f in bench_meta:
                        lbl = f"{f} — {bench_meta[f]}"
                    elif f in pool_meta:
                        lbl = f"{f} — {pool_meta[f]}"
                    else:
                        lbl = f"{f} [custom formula]"
                    if lbl not in f_map:
                        opts.append(lbl)
                        f_map[lbl] = f

                for f, meta in bench_meta.items():
                    lbl = f"{f} — {meta}"
                    if lbl not in f_map:
                        opts.append(lbl)
                        f_map[lbl] = f

                for f, meta in pool_meta.items():
                    lbl = f"{f} — {meta}"
                    if lbl not in f_map:
                        opts.append(lbl)
                        f_map[lbl] = f

                return opts, f_map

            options_list, formula_map = get_dropdown_options()

            selected_option = st.selectbox(
                "Select from catalog or enter custom formula:",
                options=options_list,
                index=0,
                accept_new_options=True,
                help="Type to search verified catalog materials or type any custom chemical formula (e.g. Cs2AgBiBr6, In0.53Ga0.47As)."
            )

            # Extract clean chemical formula
            if selected_option in formula_map:
                formula_input = formula_map[selected_option]
                st.caption(f"✓ Selected from verified catalog: **{formula_input}** ({selected_option.split('—')[-1].strip() if '—' in selected_option else ''})")
            else:
                formula_input = str(selected_option).split("—")[0].split("[")[0].strip()
                st.caption(f"Custom formula entered: **{formula_input}** (will be characterized on-the-fly via 132 Magpie descriptors)")

            # Preset semiconductor quick buttons
            st.markdown("<small>Quick Presets:</small>", unsafe_allow_html=True)
            cols_preset = st.columns(4)
            if cols_preset[0].button("Si"):
                formula_input = "Si"
            if cols_preset[1].button("GaAs"):
                formula_input = "GaAs"
            if cols_preset[2].button("CdTe"):
                formula_input = "CdTe"
            if cols_preset[3].button("TiO2"):
                formula_input = "TiO2"

        else:
            uploaded_cif = st.file_uploader("Upload Crystallographic Information File (.cif)", type=["cif"])
            if uploaded_cif is not None:
                cif_content = uploaded_cif.read().decode("utf-8")
                st.info("Uploaded CIF ready for parsing.")
            st.caption("ℹ️ *Note on CIF Structures: The model featurizes composition only. 3D coordinates, space group symmetry, and polymorph distinctions are not utilized in prediction.*")

        st.markdown("---")
        enable_xgboost = st.toggle(
            "Parallel XGBoost Analysis",
            value=True,
            help="Toggle to run the auxiliary 5-fold XGBoost model side-by-side with the production Random Forest."
        )

        run_btn = st.button("Run Analysis", type="primary", use_container_width=True)

    with col2:
        if run_btn:
            eval_target = cif_content if (input_type == "CIF Structure" and cif_content) else formula_input
            is_cif = (input_type == "CIF Structure")

            if not eval_target:
                st.warning("Please provide a chemical formula or upload a CIF file.")
            else:
                with st.spinner("Featurizing 132 Magpie descriptors & evaluating ensembles..."):
                    try:
                        ranked_results = score_material_all_usecases(eval_target, is_cif=is_cif, active_only=True)
                    except Exception as e:
                        import traceback
                        tb_str = traceback.format_exc()
                        st.error(f"Analysis failed: {e}")
                        with st.expander("Diagnostic Details"):
                            st.code(tb_str, language="text")
                        ranked_results = []

                if ranked_results:
                    first_res = ranked_results[0]
                    canon_form = first_res["material"]
                    canon_form_html = format_formula_html(canon_form)

                    st.markdown(f"### Results for **{canon_form_html}**", unsafe_allow_html=True)

                    if first_res.get("cif_warning"):
                        st.warning(first_res["cif_warning"])
                    if first_res.get("ood_warning"):
                        st.warning(first_res["ood_warning"])

                    # Parallel XGBoost Diagnostic Comparison Card
                    if enable_xgboost:
                        xgb_model_file = project_root / "models" / "xgboost_bandgap" / "xgboost_ensemble.joblib"
                        if xgb_model_file.exists():
                            try:
                                import joblib
                                import shap
                                from src.features import featurize_composition, parse_material_input
                                from src.config import MAGPIE_FEATURES
                                from src.explain import humanize_feature_name

                                _, comp_xgb, _ = parse_material_input(canon_form)
                                feats_xgb = featurize_composition(comp_xgb)
                                X_xgb = feats_xgb[MAGPIE_FEATURES].values

                                xgb_models = joblib.load(xgb_model_file)
                                xgb_preds = [float(m.predict(X_xgb)[0]) for m in xgb_models]
                                xgb_mean = float(np.mean(xgb_preds))
                                xgb_std = float(np.std(xgb_preds))

                                rf_pred_val = first_res["properties"]["bandgap"]["value"]
                                rf_tag = first_res["properties"]["bandgap"]["tag"]
                                rf_std_val = first_res["properties"]["bandgap"]["std"]

                                st.markdown(f"""
                                <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1.25rem; margin-bottom: 1.25rem;">
                                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;">
                                        <h4 style="margin: 0; font-size: 1.05rem; font-weight: 600; color: #0f172a;">Model Band-Gap Comparison: Production Random Forest vs. Auxiliary XGBoost</h4>
                                        <span class="tag-predicted">ENSEMBLE COMPARISON</span>
                                    </div>
                                    <p style="margin: 0 0 0.85rem 0; font-size: 0.85rem; color: #64748b;">
                                        Side-by-side evaluation of the 100-tree Random Forest regressor and 5-fold cross-validated XGBoost gradient booster across identical 132 Magpie elemental features.
                                    </p>
                                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                                        <div style="background: #f8fafc; padding: 0.85rem 1rem; border-radius: 6px; border: 1px solid #e2e8f0; border-left: 3px solid #334155;">
                                            <div style="font-size: 0.75rem; color: #64748b; font-weight: 600; text-transform: uppercase;">Production Random Forest</div>
                                            <div style="font-size: 1.5rem; font-weight: 700; color: #0f172a; margin-top: 0.15rem;">{rf_pred_val:.2f} eV <span style="font-size: 0.8rem; color: #64748b; font-weight: 500;">[{rf_tag}]</span></div>
                                            <div style="font-size: 0.76rem; color: #64748b; margin-top: 0.2rem;">Ensemble tree dispersion: ±{rf_std_val:.2f} eV (not a confidence interval)</div>
                                        </div>
                                        <div style="background: #f0fdfa; padding: 0.85rem 1rem; border-radius: 6px; border: 1px solid #ccfbf1; border-left: 3px solid #0f766e;">
                                            <div style="font-size: 0.75rem; color: #0f766e; font-weight: 600; text-transform: uppercase;">Auxiliary XGBoost Ensemble</div>
                                            <div style="font-size: 1.5rem; font-weight: 700; color: #0f766e; margin-top: 0.15rem;">{xgb_mean:.2f} eV <span style="font-size: 0.8rem; color: #0d9488; font-weight: 500;">[predicted]</span></div>
                                            <div style="font-size: 0.76rem; color: #0f766e; margin-top: 0.2rem;">5-fold spread: ±{xgb_std:.2f} eV</div>
                                        </div>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)

                                # Concurrent Visualizations
                                import plotly.graph_objects as go
                                plot_col1, plot_col2 = st.columns(2)

                                # Chart 1: Band Gap & Ensemble Uncertainty Comparison
                                with plot_col1:
                                    fig_comp = go.Figure()
                                    fig_comp.add_trace(go.Bar(
                                        name="Production RF",
                                        x=["Random Forest"],
                                        y=[rf_pred_val],
                                        error_y=dict(type='data', array=[rf_std_val], visible=True, color='#a5b4fc'),
                                        marker_color='#4f46e5',
                                        text=[f"{rf_pred_val:.2f} eV"],
                                        textposition="auto"
                                    ))
                                    fig_comp.add_trace(go.Bar(
                                        name="Auxiliary XGBoost",
                                        x=["XGBoost (5 Folds)"],
                                        y=[xgb_mean],
                                        error_y=dict(type='data', array=[xgb_std], visible=True, color='#86efac'),
                                        marker_color='#10b981',
                                        text=[f"{xgb_mean:.2f} eV"],
                                        textposition="auto"
                                    ))
                                    fig_comp.update_layout(
                                        template="plotly_white",
                                        title=dict(text="<b>Band Gap & Ensemble Spread</b>", font=dict(size=13, color="#0f172a")),
                                        yaxis_title="Band Gap (eV)",
                                        showlegend=False,
                                        margin=dict(l=30, r=20, t=40, b=30),
                                        height=290,
                                        paper_bgcolor="#ffffff",
                                        plot_bgcolor="#0f172a"
                                    )
                                    st.plotly_chart(fig_comp, use_container_width=True)

                                # Compute XGBoost SHAP Drivers
                                xgb_explainer = shap.TreeExplainer(xgb_models[0])
                                xgb_shap_vals = xgb_explainer(X_xgb).values[0]
                                xgb_top_indices = np.argsort(np.abs(xgb_shap_vals))[::-1][:6]
                                
                                xgb_drivers = []
                                chart_labels = []
                                chart_impacts = []
                                chart_colors = []

                                for idx in xgb_top_indices:
                                    raw_f = MAGPIE_FEATURES[idx]
                                    imp = float(xgb_shap_vals[idx])
                                    val = float(feats_xgb.iloc[0][raw_f])
                                    h_name = humanize_feature_name(raw_f)
                                    xgb_drivers.append({
                                        "Elemental Descriptor": h_name,
                                        "Material Value": round(val, 2),
                                        "XGBoost SHAP Impact (eV)": round(imp, 3),
                                        "Effect": "Increased Gap" if imp > 0 else "Decreased Gap"
                                    })
                                    chart_labels.append(h_name)
                                    chart_impacts.append(imp)
                                    chart_colors.append("#10b981" if imp > 0 else "#ef4444")

                                # Chart 2: XGBoost SHAP Impact Waterfall / Horizontal Bar
                                with plot_col2:
                                    fig_shap = go.Figure()
                                    fig_shap.add_trace(go.Bar(
                                        x=chart_impacts[::-1],
                                        y=chart_labels[::-1],
                                        orientation='h',
                                        marker_color=chart_colors[::-1],
                                        text=[f"{v:+.2f} eV" for v in chart_impacts[::-1]],
                                        textposition="auto"
                                    ))
                                    fig_shap.update_layout(
                                        template="plotly_white",
                                        title=dict(text="<b>XGBoost SHAP Feature Impacts</b>", font=dict(size=13, color="#0f172a")),
                                        xaxis_title="SHAP Impact on Eg (eV)",
                                        margin=dict(l=30, r=20, t=40, b=30),
                                        height=290,
                                        paper_bgcolor="#ffffff",
                                        plot_bgcolor="#0f172a"
                                    )
                                    st.plotly_chart(fig_shap, use_container_width=True)

                                # XGBoost Natural Language Scientific Explanation
                                top_pos = [d["Elemental Descriptor"] for d in xgb_drivers if d["XGBoost SHAP Impact (eV)"] > 0][:2]
                                top_neg = [d["Elemental Descriptor"] for d in xgb_drivers if d["XGBoost SHAP Impact (eV)"] < 0][:2]
                                
                                expl_pos = f"elevated by high **{', '.join(top_pos)}**" if top_pos else ""
                                expl_neg = f"moderated downward by **{', '.join(top_neg)}**" if top_neg else ""
                                full_diag_expl = f"**XGBoost Model Explanation:** For **{canon_form}**, the gradient boosted ensemble predicts **{xgb_mean:.2f} eV** (ensemble standard deviation ±{xgb_std:.2f} eV across 5 folds). The primary physical drivers pushing the gap higher are {expl_pos}{' and ' if expl_pos and expl_neg else ''}{expl_neg}. In contrast to the Random Forest's {rf_pred_val:.2f} eV prediction, XGBoost minimizes tail truncation, yielding closer tracking to verified experimental bounds."

                                st.info(f"{full_diag_expl}")

                                with st.expander("View XGBoost SHAP Table"):
                                    st.dataframe(pd.DataFrame(xgb_drivers), use_container_width=True, hide_index=True)

                            except Exception as xgb_err:
                                st.caption(f"XGBoost auxiliary diagnostic unavailable: {xgb_err}")

                    # =========================================================================
                    # CONCURRENT APPLICATION USABILITY ANALYSIS: SOLAR, SEMICONDUCTOR, QUANTUM/LED
                    # =========================================================================
                    st.markdown("""
                    <div style="margin-top: 2rem; margin-bottom: 1.2rem;">
                        <div style="display: flex; justify-content: space-between; align-items: flex-end;">
                            <div>
                                <h3 style="margin: 0; font-size: 1.4rem; font-weight: 700; color: #f8fafc; letter-spacing: -0.02em;">
                                    Application Suitability: Solar • Semiconductor • Optoelectronics
                                </h3>
                                <p style="margin: 0.3rem 0 0 0; font-size: 0.88rem; color: #94a3b8;">
                                    Comparative suitability scoring and physical mechanics evaluated concurrently under Random Forest and 5-fold XGBoost ensembles.
                                </p>
                            </div>
                            <span style="background: rgba(99, 102, 241, 0.2); color: #c7d2fe; border: 1px solid rgba(99, 102, 241, 0.35); padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 600;">
                                DUAL-MODEL COMPARATIVE ENGINE
                            </span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Compute concurrent suitability across all 3 active domains
                    rf_bg = float(first_res["properties"]["bandgap"]["value"])
                    rf_tag_label = first_res["properties"]["bandgap"]["tag"]
                    rf_tree_disp = float(first_res["properties"]["bandgap"]["std"])

                    # If XGBoost is enabled, use its predictions; otherwise fallback to rf_bg
                    xgb_bg_val = xgb_mean if ('xgb_mean' in locals() and xgb_mean is not None) else rf_bg
                    xgb_disp_val = xgb_std if ('xgb_std' in locals() and xgb_std is not None) else 0.0

                    app_specs = [
                        {
                            "id": "solar",
                            "name": "Solar Photovoltaics (Absorber)",
                            "domain": "Energy & Clean Tech",
                            "icon": "",
                            "opt_eg": 1.34,
                            "window": "1.10 – 1.50 eV (Shockley-Queisser Limit)",
                            "band_desc": "AM1.5 Solar Absorption Window",
                            "eval_func": REGISTRY["solar"].criteria[0].evaluate,
                            "caveat": REGISTRY["solar"].caveats
                        },
                        {
                            "id": "semiconductor",
                            "name": "Semiconductor Electronic Switching",
                            "domain": "Logic & Power Electronics",
                            "icon": "",
                            "opt_eg": 1.25,
                            "window": "0.20 – 2.80 eV (FET / Power Switching)",
                            "band_desc": "Room-Temperature Thermal Leakage / Ionization Window",
                            "eval_func": REGISTRY["semiconductor"].criteria[0].evaluate,
                            "caveat": REGISTRY["semiconductor"].caveats
                        },
                        {
                            "id": "led",
                            "name": "Quantum Emitters & Optoelectronics / LED",
                            "domain": "Photonics & Quantum Wells",
                            "icon": "",
                            "opt_eg": 2.50,
                            "window": "2.00 – 3.50 eV (Visible / Near-UV Emission)",
                            "band_desc": "Direct Radiative Recombination & Exciton Binding",
                            "eval_func": REGISTRY["led"].criteria[0].evaluate,
                            "caveat": REGISTRY["led"].caveats
                        }
                    ]

                    # Calculate scores for all applications
                    scored_apps = []
                    for spec in app_specs:
                        s_rf = float(spec["eval_func"](rf_bg))
                        s_xgb = float(spec["eval_func"](xgb_bg_val))
                        scored_apps.append({
                            **spec,
                            "score_rf": s_rf,
                            "score_xgb": s_xgb,
                            "delta": s_xgb - s_rf
                        })

                    # Graph 1 & 2: Interactive Comparative Usability Visualizations
                    import plotly.graph_objects as go
                    chart_col1, chart_col2 = st.columns([1.1, 0.9])

                    with chart_col1:
                        # Grouped Bar Chart of RF vs. XGBoost Usability across Solar, Semi, Quantum
                        fig_usability = go.Figure()
                        app_names = [a["name"].split('(')[0].replace('Quantum Emitters & Optoelectronics / ', 'Opto/Quantum: ') for a in scored_apps]
                        
                        fig_usability.add_trace(go.Bar(
                            name="Production Random Forest",
                            x=app_names,
                            y=[a["score_rf"] for a in scored_apps],
                            marker_color='#6366f1',
                            text=[f"{a['score_rf']:.2f}" for a in scored_apps],
                            textposition='auto',
                            marker=dict(line=dict(color='rgba(255,255,255,0.15)', width=1))
                        ))
                        
                        fig_usability.add_trace(go.Bar(
                            name="Auxiliary XGBoost (5 Folds)",
                            x=app_names,
                            y=[a["score_xgb"] for a in scored_apps],
                            marker_color='#06b6d4',
                            text=[f"{a['score_xgb']:.2f}" for a in scored_apps],
                            textposition='auto',
                            marker=dict(line=dict(color='rgba(255,255,255,0.15)', width=1))
                        ))

                        fig_usability.update_layout(
                            template="plotly_white",
                            title=dict(
                                text="<b>Application Suitability Desirability: RF vs. XGBoost</b>",
                                font=dict(size=13, color="#0f172a")
                            ),
                            barmode='group',
                            yaxis=dict(title="Desirability (0.00 – 1.00)", range=[0, 1.05], gridcolor='rgba(255,255,255,0.06)'),
                            xaxis=dict(gridcolor='rgba(255,255,255,0.02)'),
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=1.02,
                                xanchor="right",
                                x=1,
                                font=dict(size=11)
                            ),
                            margin=dict(l=40, r=20, t=55, b=40),
                            height=310,
                            paper_bgcolor="#ffffff",
                            plot_bgcolor="#0f172a"
                        )
                        st.plotly_chart(fig_usability, use_container_width=True)

                    with chart_col2:
                        # Radar Chart Comparison of Multi-Domain Alignment
                        categories = ['Solar PV', 'Semiconductor (FET)', 'Opto / Quantum LED']
                        r_rf = [a["score_rf"] for a in scored_apps]
                        r_xgb = [a["score_xgb"] for a in scored_apps]
                        # Close the loop
                        categories_closed = categories + [categories[0]]
                        r_rf_closed = r_rf + [r_rf[0]]
                        r_xgb_closed = r_xgb + [r_xgb[0]]

                        fig_radar = go.Figure()
                        fig_radar.add_trace(go.Scatterpolar(
                            r=r_rf_closed,
                            theta=categories_closed,
                            fill='toself',
                            name='Production RF',
                            line=dict(color='#818cf8', width=2),
                            fillcolor='rgba(99, 102, 241, 0.25)'
                        ))
                        fig_radar.add_trace(go.Scatterpolar(
                            r=r_xgb_closed,
                            theta=categories_closed,
                            fill='toself',
                            name='Auxiliary XGBoost',
                            line=dict(color='#22d3ee', width=2),
                            fillcolor='rgba(6, 182, 212, 0.25)'
                        ))

                        fig_radar.update_layout(
                            template="plotly_white",
                            title=dict(
                                text="<b>Multi-Domain Usability Profile</b>",
                                font=dict(size=13, color="#0f172a")
                            ),
                            polar=dict(
                                radialaxis=dict(visible=True, range=[0, 1.0], gridcolor='rgba(255,255,255,0.1)', tickfont=dict(size=9)),
                                angularaxis=dict(gridcolor='rgba(255,255,255,0.1)', tickfont=dict(size=11, color='#cbd5e1'))
                            ),
                            showlegend=True,
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=1.02,
                                xanchor="right",
                                x=1,
                                font=dict(size=11)
                            ),
                            margin=dict(l=40, r=40, t=55, b=40),
                            height=310,
                            paper_bgcolor="#ffffff",
                            plot_bgcolor="#0f172a"
                        )
                        st.plotly_chart(fig_radar, use_container_width=True)

                    # Detailed Scientific Breakdown & Mechanics per Application Card
                    st.markdown("#### Application Usability Evaluations & Physical Mechanics")
                    
                    for app in scored_apps:
                        app_id = app["id"]
                        s_rf = app["score_rf"]
                        s_xgb = app["score_xgb"]
                        delta = app["delta"]
                        pct_rf = int(s_rf * 100)
                        pct_xgb = int(s_xgb * 100)

                        # Qualitative interpretation for both models
                        def get_qualitative_label(score):
                            if score >= 0.85:
                                return ("Highly Viable / Optimal", "#10b981", "rgba(16, 185, 129, 0.15)")
                            elif score >= 0.60:
                                return ("Viable / Moderate Alignment", "#3b82f6", "rgba(59, 130, 246, 0.15)")
                            elif score >= 0.30:
                                return ("Marginal / Partial Alignment", "#f59e0b", "rgba(245, 158, 11, 0.15)")
                            else:
                                return ("Unfavorable / Out of Alignment", "#ef4444", "rgba(239, 68, 68, 0.15)")

                        rf_lbl, rf_color, rf_bg_chip = get_qualitative_label(s_rf)
                        xgb_lbl, xgb_color, xgb_bg_chip = get_qualitative_label(s_xgb)

                        # Detailed physics explanation tailored to the XGBoost prediction
                        if app_id == "solar":
                            if xgb_bg_val < 0.8:
                                xgb_app_mechanics = f"At {xgb_bg_val:.2f} eV, the gap is excessively narrow for single-junction PV absorber layers, leading to drastic open-circuit voltage (Voc) degradation and severe thermalization losses under the AM1.5 solar spectrum."
                            elif 1.0 <= xgb_bg_val <= 1.6:
                                xgb_app_mechanics = f"At {xgb_bg_val:.2f} eV, XGBoost positions {canon_form} directly within the theoretical Shockley-Queisser radiative limit window (peak 1.34 eV), maximizing solar photon flux absorption while suppressing sub-bandgap transmission and thermalization."
                            else:
                                xgb_app_mechanics = f"At {xgb_bg_val:.2f} eV, the gap exceeds optimal single-junction absorber windows (>1.6 eV), causing high transmission loss in the infrared solar spectrum. While suboptimal as a single-junction absorber, it may serve as a wide-gap top-cell candidate in tandem configurations."
                        elif app_id == "semiconductor":
                            if xgb_bg_val < 0.2:
                                xgb_app_mechanics = f"With Eg={xgb_bg_val:.2f} eV, excessive intrinsic thermal carrier generation at 300 K creates high off-state leakage current (Ioff), rendering this material poorly suited for standard room-temperature transistor switching."
                            elif 0.8 <= xgb_bg_val <= 2.2:
                                xgb_app_mechanics = f"With Eg={xgb_bg_val:.2f} eV, {canon_form} sits squarely in the ideal electronic switching regime (comparable to Si at 1.12 eV and GaAs at 1.42 eV). It achieves robust Ion/Ioff switching ratios and suppresses thermal sub-threshold leakage at ambient operating temperatures."
                            else:
                                xgb_app_mechanics = f"With Eg={xgb_bg_val:.2f} eV, this material behaves as a wide-bandgap (WBG) semiconductor (akin to SiC or GaN). It offers exceptional critical electric breakdown field strength for high-voltage power electronics, though dopability and ohmic contact resistance must be experimentally verified."
                        else: # led / quantum
                            if xgb_bg_val < 1.6:
                                approx_wl = 1239.84 / xgb_bg_val if xgb_bg_val > 0.05 else 0
                                xgb_app_mechanics = f"At {xgb_bg_val:.2f} eV (equivalent photon wavelength ~{approx_wl:.0f} nm), emission falls into the near-infrared / telecom band, failing to satisfy visible LED/emitter criteria."
                            elif 1.8 <= xgb_bg_val <= 3.4:
                                approx_wl = 1239.84 / xgb_bg_val
                                xgb_app_mechanics = f"At {xgb_bg_val:.2f} eV, this corresponds to an optical photon emission wavelength of **~{approx_wl:.0f} nm**, positioning {canon_form} right in the active visible/near-UV optoelectronic and quantum-well light emission window. (Note: Radiative efficiency requires direct band-gap alignment)."
                            else:
                                xgb_app_mechanics = f"At {xgb_bg_val:.2f} eV, emission shifts deep into the ultraviolet / deep-UV regime, suitable for UV germicidal/optical barriers rather than conventional visible optoelectronics."

                        card_html = f"""<div class="app-matrix-card">
<div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.8rem;">
<div>
<div class="app-title">
<span>{app['icon']}</span>
<span>{app['name']}</span>
<span style="font-size: 0.75rem; color: #94a3b8; font-weight: 500;">({app['domain']})</span>
</div>
<div class="app-subtitle">
Target Optimum: <strong>{app['opt_eg']} eV</strong> • Active Window: {app['window']}
</div>
</div>
<div style="display: flex; gap: 0.5rem;">
<span class="tag-predicted">RF: {s_rf:.2f}</span>
<span class="tag-xgboost">XGB: {s_xgb:.2f}</span>
</div>
</div>
<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.2rem; margin: 1rem 0;">
<div class="model-score-box rf">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;">
<span style="font-size: 0.78rem; font-weight: 700; color: #a5b4fc;">PRODUCTION RANDOM FOREST</span>
<span style="font-size: 0.85rem; font-weight: 800; color: #f8fafc;">{s_rf:.3f}</span>
</div>
<div style="background-color: rgba(15, 23, 42, 0.8); border-radius: 9999px; height: 8px; overflow: hidden; margin-bottom: 0.4rem;">
<div style="background: linear-gradient(90deg, #4f46e5 0%, #818cf8 100%); width: {pct_rf}%; height: 100%; border-radius: 9999px;"></div>
</div>
<div style="display: flex; justify-content: space-between; font-size: 0.74rem;">
<span style="color: #94a3b8;">Eg: {rf_bg:.2f} eV (±{rf_tree_disp:.2f})</span>
<span style="color: {rf_color}; font-weight: 600;">{rf_lbl}</span>
</div>
</div>
<div class="model-score-box xgb">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;">
<span style="font-size: 0.78rem; font-weight: 700; color: #67e8f9;">AUXILIARY XGBOOST (5 FOLDS)</span>
<span style="font-size: 0.85rem; font-weight: 800; color: #f8fafc;">{s_xgb:.3f}</span>
</div>
<div style="background-color: rgba(15, 23, 42, 0.8); border-radius: 9999px; height: 8px; overflow: hidden; margin-bottom: 0.4rem;">
<div style="background: linear-gradient(90deg, #0891b2 0%, #22d3ee 100%); width: {pct_xgb}%; height: 100%; border-radius: 9999px;"></div>
</div>
<div style="display: flex; justify-content: space-between; font-size: 0.74rem;">
<span style="color: #94a3b8;">Eg: {xgb_bg_val:.2f} eV (±{xgb_disp_val:.2f})</span>
<span style="color: {xgb_color}; font-weight: 600;">{xgb_lbl}</span>
</div>
</div>
</div>
<div class="expl-box-xgb">
<strong>XGBoost Analysis:</strong> {xgb_app_mechanics}
</div>
<div style="font-size: 0.76rem; color: #94a3b8; margin-top: 0.6rem; font-style: italic;">
Scope boundary: {app['caveat']}
</div>
</div>"""
                        with st.container():
                            st.markdown(card_html, unsafe_allow_html=True)

                    # Expandable SHAP Feature Attribution Table for Deeper Inspection
                    with st.expander("Why did the model predict this? (SHAP Feature Attribution)"):
                        try:
                            exp = explain_prediction(canon_form, "bandgap", top_k=6)
                            drivers_df = pd.DataFrame(exp["drivers"])
                            st.dataframe(
                                drivers_df[["friendly_name", "value", "impact", "direction"]],
                                column_config={
                                    "friendly_name": "Elemental Descriptor",
                                    "value": "Material Value",
                                    "impact": "SHAP Impact on Eg (eV)",
                                    "direction": "Effect on Band Gap"
                                },
                                use_container_width=True,
                                hide_index=True
                            )
                        except Exception as shap_err:
                            st.caption(f"SHAP drivers inspection unavailable: {shap_err}")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #94a3b8; font-size: 0.85rem; padding: 1rem;">
    SemiScope Semiconductor Intelligence Engine • 4,604-Record Band-Gap Benchmark & Candidate Catalog • Leakage-Free Grouped-CV Random Forest
</div>
""", unsafe_allow_html=True)
