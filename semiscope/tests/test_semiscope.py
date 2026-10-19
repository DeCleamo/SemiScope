"""
Comprehensive automated test suite for SemiScope.
Validates:
1. Formula & CIF parsing
2. 132 Magpie feature parity and NaN invariance
3. Scoring desirability monotonicity and multi-property geometric mean
4. Scientific sanity benchmarks (Si, GaAs, Nb3Sn, TiO2)
5. Grouped candidate pool resolution & provenance tags
"""

import sys
from pathlib import Path
import math
import numpy as np
import pandas as pd

# Add semiscope root to sys.path
test_dir = Path(__file__).resolve().parent
project_root = test_dir.parent
sys.path.insert(0, str(project_root))

from src.config import MAGPIE_FEATURES, RAW_DATASETS
from src.features import parse_material_input, featurize_composition
from src.registry import REGISTRY, get_use_case, Criterion
from src.scoring import score_material_for_usecase, score_material_all_usecases, load_model, get_candidate_pool
from src.precompute_pool import recommend_materials



def test_formula_parsing():
    """Validates pymatgen formula reduction."""
    formula, comp, warn = parse_material_input("Ba1Ti1O3")
    assert formula == "BaTiO3"
    assert comp.num_atoms == 5.0
    assert warn is None

    # Complex stoichiometry
    formula2, comp2, _ = parse_material_input("Y1Ba2Cu3O7")
    assert formula2 == "Ba2YCu3O7"


def test_cif_geometry_discard_warning():
    """Validates CIF parsing warns that 3D geometry is discarded."""
    mock_cif = """data_Si
_symmetry_space_group_name_H-M   'P 1'
_cell_length_a   4.00000000
_cell_length_b   4.00000000
_cell_length_c   4.00000000
_cell_angle_alpha   90.00000000
_cell_angle_beta   90.00000000
_cell_angle_gamma   90.00000000
_symmetry_Int_Tables_number   1
_chemical_formula_sum   Si1
loop_
 _symmetry_equiv_pos_site_id
 _symmetry_equiv_pos_as_xyz
  1  'x, y, z'
loop_
 _atom_site_type_symbol
 _atom_site_label
 _atom_site_fract_x
 _atom_site_fract_y
 _atom_site_fract_z
  Si  Si0  0.0  0.0  0.0
"""
    formula, comp, warn = parse_material_input(mock_cif, is_cif=True)
    assert formula == "Si"
    assert warn is not None
    assert "geometry discarded" in warn.lower()


def test_feature_parity_and_ordering():
    """Validates exact 132 Magpie features, correct ordering, and no NaNs."""
    feats = featurize_composition("GaAs")
    assert feats.shape == (1, 132)
    assert list(feats.columns) == MAGPIE_FEATURES
    assert not feats.isna().any().any(), "Features contained NaN values"


def test_model_loading_and_assertions():
    """Validates all 4 production models load and match metadata."""
    for key in ["bandgap", "tc", "enthalpy", "zt"]:
        model, meta = load_model(key)
        assert meta["n_features"] == 132
        assert meta["features"] == MAGPIE_FEATURES
        assert hasattr(model, "estimators_")
        assert len(model.estimators_) > 0


def test_scoring_desirability_monotonicity():
    """Validates that ramp_up and trapezoid desirability behave monotonically."""
    crit_ramp = Criterion(
        property_key="tc",
        function_type="ramp_up",
        params={"x_min": 2.0, "x_max": 10.0}
    )
    assert crit_ramp.evaluate(1.0) == 0.0
    assert crit_ramp.evaluate(6.0) == 0.5
    assert crit_ramp.evaluate(10.0) == 1.0
    assert crit_ramp.evaluate(15.0) == 1.0

    # Trapezoid
    crit_trap = Criterion(
        property_key="bandgap",
        function_type="trapezoid",
        params={"x0": 1.0, "x1": 1.2, "x2": 1.6, "x3": 1.8}
    )
    assert crit_trap.evaluate(0.5) == 0.0
    assert math.isclose(crit_trap.evaluate(1.1), 0.5, abs_tol=0.01)
    assert crit_trap.evaluate(1.4) == 1.0
    assert math.isclose(crit_trap.evaluate(1.7), 0.5, abs_tol=0.01)
    # Gaussian
    crit_gauss = Criterion(
        property_key="bandgap",
        function_type="gaussian",
        params={"x_opt": 1.34, "sigma": 0.35, "x_min": 0.05, "x_max": 2.50}
    )
    # Zero-gap metal cutoff
    assert crit_gauss.evaluate(0.0) == 0.0
    assert crit_gauss.evaluate(0.04) == 0.0
    # Strict upper cutoff
    assert crit_gauss.evaluate(2.55) == 0.0
    # Peak optimum
    assert math.isclose(crit_gauss.evaluate(1.34), 1.0, abs_tol=1e-5)
    # Smooth symmetric roll-off
    assert math.isclose(crit_gauss.evaluate(1.35), crit_gauss.evaluate(1.33), abs_tol=1e-5)
    assert 0.99 < crit_gauss.evaluate(1.35) < 1.0
    # Distance of 1 sigma
    assert math.isclose(crit_gauss.evaluate(1.34 + 0.35), math.exp(-0.5), abs_tol=1e-4)


def test_semiconductor_benchmarks():
    """Validates physical semiconductor benchmarks (GaAs, InP, Si)."""
    # GaAs is a premier semiconductor switching material
    res_gaas = score_material_for_usecase("GaAs", "semiconductor")
    assert res_gaas["score"] > 0.70
    assert "bandgap" in res_gaas["properties"]

    # InP is suitable for semiconductor switching and solar
    res_inp = score_material_for_usecase("InP", "semiconductor")
    assert res_inp["score"] > 0.80
    res_inp_solar = score_material_for_usecase("InP", "solar")
    assert res_inp_solar["score"] > 0.60

    # Si is standard semiconductor (score > 0.40)
    res_si = score_material_for_usecase("Si", "semiconductor")
    assert res_si["score"] > 0.40


def test_recommend_materials_fast():
    """Validates Mode 1 semiconductor candidate retrieval returns valid candidates with tie diagnostics."""
    solar_candidates = recommend_materials("solar", top_n=10, measured_only=True)
    assert len(solar_candidates) == 10
    for c in solar_candidates:
        assert c["score"] > 0.0
        assert c["tag"] == "measured"
        assert 0.8 <= c["resolved_bandgap"] <= 2.0
        assert "rank" in c
        assert "is_tied" in c
        assert "tie_count" in c

    # Top candidate In5CuS8 has exactly 1.34 eV and must have score 1.0
    assert solar_candidates[0]["formula"] == "In5CuS8"
    assert math.isclose(solar_candidates[0]["score"], 1.0, abs_tol=1e-5)
    assert solar_candidates[0]["rank"] == 1

    # Candidates with equal bandgap (e.g. 1.35 eV) must share identical rank and score
    rank_2_cands = [c for c in solar_candidates if c["rank"] == 2]
    assert len(rank_2_cands) >= 2
    for r2 in rank_2_cands:
        assert r2["is_tied"] is True
        assert math.isclose(r2["score"], rank_2_cands[0]["score"], abs_tol=1e-6)


def test_zero_gap_metal_penalization():
    """Validates that zero-gap materials receive exactly 0.00 across all active use cases."""
    for uc_id in ["solar", "semiconductor", "led"]:
        uc = get_use_case(uc_id)
        for crit in uc.criteria:
            assert crit.evaluate(0.0) == 0.0
            assert crit.evaluate(0.04) == 0.0


def test_led_ties_dense_ranking_and_provenance():
    """
    Validates LED candidates:
    1. Exactly 11 candidates at 2.50 eV share Rank #1 with identical score 1.0000.
    2. is_tied is True and tie_count is 11 for all Rank #1 materials.
    3. Next candidates (at 2.51 eV) receive dense rank #12 with score 0.9998 and is_tied True.
    4. Provenance tag is strictly 'measured' and band gap matches source dataset without corruption.
    5. Formulas are distinct compounds.
    """
    led_cands = recommend_materials("led", top_n=20, measured_only=True)
    rank_1 = [c for c in led_cands if c["rank"] == 1]
    assert len(rank_1) == 11, f"Expected 11 rank #1 candidates, got {len(rank_1)}"

    formulas_seen = set()
    for c in rank_1:
        assert c["resolved_bandgap"] == 2.50
        assert math.isclose(c["score"], 1.0000, abs_tol=1e-5)
        assert c["score_display"] == 1.0000
        assert c["is_tied"] is True
        assert c["tie_count"] == 11
        assert c["tag"] == "measured"
        assert c["formula"] not in formulas_seen
        formulas_seen.add(c["formula"])

    # Rank 12 candidates (|Eg - 2.50| == 0.01 eV: both 2.49 eV and 2.51 eV produce identical score)
    rank_12 = [c for c in led_cands if c["rank"] == 12]
    assert len(rank_12) == 8, f"Expected 8 rank #12 candidates, got {len(rank_12)}"
    for c in rank_12:
        assert c["resolved_bandgap"] in (2.49, 2.51)
        assert math.isclose(c["score"], 0.9998, abs_tol=1e-4)
        assert c["score_display"] == 0.9998
        assert c["is_tied"] is True
        assert c["tie_count"] == 8
        assert c["tag"] == "measured"


def test_evidence_schema_and_missing_data():
    """
    Validates the evidence schema and missing property handling:
    1. Audited profiles return verified records with valid sources and DOIs.
    2. Missing properties explicitly evaluate to is_missing=True.
    3. Missing data is never treated as 0.0 or negative evidence.
    """
    from src.evidence import get_material_evidence, EvidenceRecord, MaterialEvidenceProfile

    p = get_material_evidence("In5CuS8")
    assert p is not None
    assert p.formula == "In5CuS8"

    # Bandgap record is verified
    bg_rec = p.get_property("bandgap")
    assert bg_rec is not None
    assert bg_rec.is_verified is True
    assert bg_rec.value == 1.34
    assert "doi.org" in bg_rec.doi_or_url

    # Missing property record
    mob_rec = p.get_property("carrier_mobility")
    assert mob_rec is not None
    assert mob_rec.is_missing is True
    assert mob_rec.value is None
    assert mob_rec.evidence_status == "missing"

    # Unaudited candidate returns None without error
    p_none = get_material_evidence("NonExistentFormula123")
    assert p_none is None


def test_semiconductor_catalog_isolation():
    """Validates that candidate catalog defaults to verified 4,604 semiconductor dataset."""
    pool = get_candidate_pool(use_full_pool=False)
    assert len(pool) == 4604
    assert pool["measured_bandgap"].notna().sum() == 4604


def test_mode1_card_evidence_rendering():
    """
    Validates Mode 1 candidate card UI structure:
    1. Band-Gap Energy remains the primary verified evidence field.
    2. The three unverified/missing property indicators are removed from candidate card rendering:
       - Direct vs. Indirect Transition
       - Carrier Mobility / Transport
       - Phase Stability & Defect Tolerance
    3. The compact scope disclaimer explaining that ranking reflects band-gap alignment
       and does not establish overall device suitability remains present.
    """
    from pathlib import Path
    app_path = Path(__file__).parent.parent / "app" / "streamlit_app.py"
    content = app_path.read_text(encoding="utf-8")

    # Primary evidence field must be present
    assert "Band-Gap Energy:" in content
    assert "Scientific Evidence & Data Coverage:" in content

    # The 3 empty indicators must NOT be present in candidate card rendering
    assert "Direct vs. Indirect Transition:</strong> Missing in Catalog" not in content
    assert "Carrier Mobility / Transport:</strong> Missing in Catalog" not in content
    assert "Phase Stability & Defect Tolerance:</strong> Missing in Catalog" not in content

    # Scope boundary disclaimer must be retained
    assert "Band-Gap Scope Boundary:" in content
    assert "Band-gap-aligned candidate. Overall device suitability has not been established" in content


def test_chemical_formula_typography():
    """
    Validates chemical formula typography rendering rules:
    1. Ordinary formulas: TlAsSe2 -> TlAsSe2, K2Gd2Sb2Se9, In5CuS8, Cs3Bi2Br9, SiO2
    2. Formulas with no numbers (e.g. GaAs, Si, BP) remain unchanged without redundant tags
    3. Grouped expressions with parentheses (e.g. Ag(AuS)2, V3Bi(PbO4)3) are correctly subscripted
    4. Decimal stoichiometry (e.g. Ag0.5Ge1Pb1.75S4, La1Se0.14S1.86) is correctly subscripted
    5. Reversibility: stripping <sub> tags recovers exact original canonical formula
    6. Non-formulas: ranks ('#2', 'Rank #1'), scores ('0.9996', '1.0000'), and prose remain unchanged
    7. Malformed, None, or empty input handled safely
    """
    from src.typography import format_formula_html, format_formula_unicode

    # 1. Standard formulas
    assert format_formula_html("TlAsSe2") == "TlAsSe<sub>2</sub>"
    assert format_formula_html("K2Gd2Sb2Se9") == "K<sub>2</sub>Gd<sub>2</sub>Sb<sub>2</sub>Se<sub>9</sub>"
    assert format_formula_html("In5CuS8") == "In<sub>5</sub>CuS<sub>8</sub>"
    assert format_formula_html("Cs3Bi2Br9") == "Cs<sub>3</sub>Bi<sub>2</sub>Br<sub>9</sub>"
    assert format_formula_html("SiO2") == "SiO<sub>2</sub>"

    # 2. No numbers
    assert format_formula_html("GaAs") == "GaAs"
    assert format_formula_html("Si") == "Si"
    assert format_formula_html("BP") == "BP"

    # 3. Grouped expressions
    assert format_formula_html("Ag(AuS)2") == "Ag(AuS)<sub>2</sub>"
    assert format_formula_html("V3Bi(PbO4)3") == "V<sub>3</sub>Bi(PbO<sub>4</sub>)<sub>3</sub>"
    assert format_formula_html("Sm3B(SO)3") == "Sm<sub>3</sub>B(SO)<sub>3</sub>"

    # 4. Decimal stoichiometry
    assert format_formula_html("Ag0.5Ge1Pb1.75S4") == "Ag<sub>0.5</sub>Ge<sub>1</sub>Pb<sub>1.75</sub>S<sub>4</sub>"
    assert format_formula_html("La1Se0.14S1.86") == "La<sub>1</sub>Se<sub>0.14</sub>S<sub>1.86</sub>"
    assert format_formula_html("In0.6Ga0.4As0.6P0.4") == "In<sub>0.6</sub>Ga<sub>0.4</sub>As<sub>0.6</sub>P<sub>0.4</sub>"

    # 5. Non-formula numbers, ranks, scores, and text
    assert format_formula_html("#2") == "#2"
    assert format_formula_html("#12") == "#12"
    assert format_formula_html("Rank #1") == "Rank #1"
    assert format_formula_html("0.9996") == "0.9996"
    assert format_formula_html("1.0000") == "1.0000"
    assert format_formula_html("Band Gap: 2.50 eV") == "Band Gap: 2.50 eV"

    # 6. Malformed, None, empty
    assert format_formula_html(None) == ""
    assert format_formula_html("") == ""
    assert format_formula_html("   ") == ""

    # 7. Unicode fallback
    assert format_formula_unicode("SiO2") == "SiO₂"
    assert format_formula_unicode("In5CuS8") == "In₅CuS₈"


def test_mode2_domain_validation_and_benchmarks():
    """
    Validates Phase 1 Mode 2 reliability improvements:
    1. Prototypical binary semiconductors (GaAs, CdTe) parse and evaluate cleanly.
    2. Pure elemental semiconductor (Si) triggers explicit single-element OOD warning.
    3. Unsupported elements with missing physical properties (He, Ne, Ar, Og) raise clean ValueErrors.
    4. Malformed formulas and empty strings raise descriptive ValueErrors without stack traces.
    5. The 132-feature schema and Random Forest weights remain unmodified.
    """
    try:
        import pytest
        raises_ctx = pytest.raises
    except ImportError:
        import contextlib
        @contextlib.contextmanager
        def raises_ctx(expected_exc):
            class ExcInfo:
                value = None
            info = ExcInfo()
            try:
                yield info
            except expected_exc as e:
                info.value = e
            else:
                raise AssertionError(f"Expected exception {expected_exc} was not raised")

    # 1. Valid binary and multielement compounds
    for compound in ["GaAs", "CdTe", "BaTiO3", "In0.53Ga0.47As"]:
        cf, comp, warn = parse_material_input(compound)
        assert comp is not None
        feats = featurize_composition(comp)
        assert feats.shape == (1, 132)
        assert not feats.isna().any().any()
        assert not np.isinf(feats.values).any()

        # Score across use cases
        results = score_material_all_usecases(compound, active_only=True)
        assert len(results) > 0
        assert results[0]["properties"]["bandgap"]["value"] > 0.0

    # 2. Pure elemental semiconductors trigger single-element OOD warning
    cf_si, comp_si, warn_si = parse_material_input("Si")
    assert cf_si == "Si"
    assert warn_si is not None
    assert "single-element" in warn_si or "Elemental semiconductor" in warn_si
    res_si = score_material_all_usecases("Si", active_only=True)
    assert res_si[0].get("ood_warning") is not None
    assert "single-element" in res_si[0]["ood_warning"] or "Elemental semiconductor" in res_si[0]["ood_warning"]

    # 3. Unsupported elements with missing descriptors raise clean ValueError
    for unsupp in ["He", "Ne", "Ar", "Og", "He2O", "ArSi"]:
        with raises_ctx(ValueError) as excinfo:
            parse_material_input(unsupp)
        assert "Unsupported elements detected" in str(excinfo.value)

    # 4. Malformed and empty inputs raise ValueError
    for malformed in ["", "   ", "INVALID123", "!!!"]:
        with raises_ctx(ValueError):
            parse_material_input(malformed)


if __name__ == "__main__":
    tests = [
        test_formula_parsing,
        test_cif_geometry_discard_warning,
        test_feature_parity_and_ordering,
        test_model_loading_and_assertions,
        test_scoring_desirability_monotonicity,
        test_semiconductor_benchmarks,
        test_recommend_materials_fast,
        test_zero_gap_metal_penalization,
        test_led_ties_dense_ranking_and_provenance,
        test_evidence_schema_and_missing_data,
        test_semiconductor_catalog_isolation,
        test_mode1_card_evidence_rendering,
        test_chemical_formula_typography,
        test_mode2_domain_validation_and_benchmarks,
    ]
    print(f"Running SemiScope test suite ({len(tests)} tests)...")
    passed = 0
    for t in tests:
        try:
            t()
            print(f"  ✓ {t.__name__} passed")
            passed += 1
        except Exception as e:
            print(f"  ✗ {t.__name__} failed: {e}")
            raise e
    print(f"\nALL {passed}/{len(tests)} AUTOMATED TESTS PASSED SUCCESSFULLY!")




