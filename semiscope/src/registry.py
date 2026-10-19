"""
SemiScope Use-Case Registry and Criterion Definitions.
Defines target property windows, desirability transfer functions,
and evidence levels for all technological applications.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
import numpy as np


@dataclass
class Criterion:
    property_key: str          # 'bandgap', 'tc', 'enthalpy', 'zt'
    function_type: str         # 'trapezoid', 'ramp_up', 'ramp_down'
    params: Dict[str, float]   # parameters for transfer function
    weight: float = 1.0

    def evaluate(self, value: float) -> float:
        """Evaluates desirability d in [0, 1] for a single numeric value."""
        if value is None or np.isnan(value):
            return 0.0

        ftype = self.function_type
        p = self.params

        if ftype == "trapezoid":
            # x0: low cutoff, x1: plateau start, x2: plateau end, x3: high cutoff
            x0, x1, x2, x3 = p["x0"], p["x1"], p["x2"], p["x3"]
            if value <= x0 or value >= x3:
                return 0.0
            elif x1 <= value <= x2:
                return 1.0
            elif x0 < value < x1:
                return (value - x0) / (x1 - x0)
            else:  # x2 < value < x3
                return (x3 - value) / (x3 - x2)

        elif ftype == "gaussian":
            # x_opt: optimal center where desirability = 1.0
            # sigma: standard deviation controlling curvature/bandwidth
            # x_min: strict lower cutoff (below which d = 0.0, e.g. metal/sub-gap cutoff)
            # x_max: strict upper cutoff (above which d = 0.0)
            x_opt = p["x_opt"]
            sigma = p["sigma"]
            x_min = p.get("x_min", -np.inf)
            x_max = p.get("x_max", np.inf)

            if value <= x_min or value >= x_max:
                return 0.0
            diff = (value - x_opt) / sigma
            return float(np.exp(-0.5 * (diff ** 2)))

        elif ftype == "peak":
            # x0: low cutoff, x_opt: single peak (d=1.0), x1: high cutoff
            # Provides continuously differentiated desirability without flat plateaus
            x0, x_opt, x1 = p["x0"], p["x_opt"], p["x1"]
            if value <= x0 or value >= x1:
                return 0.0
            elif value <= x_opt:
                return (value - x0) / (x_opt - x0)
            else:
                return (x1 - value) / (x1 - x_opt)

        elif ftype == "ramp_up":
            # x_min: 0 desirability, x_max: 1 desirability
            x_min, x_max = p["x_min"], p["x_max"]
            if value <= x_min:
                return 0.0
            elif value >= x_max:
                return 1.0
            else:
                return (value - x_min) / (x_max - x_min)

        elif ftype == "ramp_down":
            # x_min: 1 desirability, x_max: 0 desirability
            x_min, x_max = p["x_min"], p["x_max"]
            if value <= x_min:
                return 1.0
            elif value >= x_max:
                return 0.0
            else:
                return (x_max - value) / (x_max - x_min)

        return 0.0


@dataclass
class UseCase:
    id: str
    name: str
    category: str              # 'Energy', 'Electronics', 'Quantum', 'Screening'
    description: str
    evidence_level: str        # 'Strong', 'Partial', 'Heuristic', 'Weak'
    primary_model: str         # 'bandgap', 'tc', 'enthalpy', 'zt'
    criteria: List[Criterion]
    caveats: str = ""
    active: bool = True        # Active in primary semiconductor focus


# Default Registry
REGISTRY: Dict[str, UseCase] = {
    "solar": UseCase(
        id="solar",
        name="Solar Photovoltaics (Absorber)",
        category="Energy",
        description="Shockley-Queisser optimal single-junction photovoltaic absorber candidate screening.",
        evidence_level="Strong",
        primary_model="bandgap",
        active=True,
        criteria=[
            Criterion(
                property_key="bandgap",
                function_type="gaussian",
                params={"x_opt": 1.34, "sigma": 0.35, "x_min": 0.05, "x_max": 2.50}
            )
        ],
        caveats="Continuous Gaussian desirability centered at the 1.34 eV Shockley-Queisser peak (sigma=0.35 eV, zero-gap cutoff <=0.05 eV). Evaluates optical band-gap alignment only. Does NOT establish carrier diffusion lengths, mobility, recombination lifetime, or device cell efficiency."
    ),
    "semiconductor": UseCase(
        id="semiconductor",
        name="Semiconductor (General)",
        category="Electronics",
        description="Active electronic switching, power electronics, and logic devices.",
        evidence_level="Strong",
        primary_model="bandgap",
        active=True,
        criteria=[
            Criterion(
                property_key="bandgap",
                function_type="gaussian",
                params={"x_opt": 1.25, "sigma": 0.70, "x_min": 0.05, "x_max": 3.50}
            )
        ],
        caveats="Continuous Gaussian desirability centered at 1.25 eV (optimal room-temperature switching / low off-state leakage, sigma=0.70 eV, zero-gap cutoff <=0.05 eV). Evaluates the electronic switching window only; does not establish carrier mobility, dopability, dielectric breakdown, or thermal stability."
    ),
    "led": UseCase(
        id="led",
        name="LED / Optoelectronic Emitter",
        category="Electronics",
        description="Visible to near-UV solid-state light emission / detection candidate screening.",
        evidence_level="Partial",
        primary_model="bandgap",
        active=True,
        criteria=[
            Criterion(
                property_key="bandgap",
                function_type="gaussian",
                params={"x_opt": 2.50, "sigma": 0.50, "x_min": 0.10, "x_max": 4.00}
            )
        ],
        caveats="Continuous Gaussian desirability centered at 2.50 eV (green-blue visible emission band, sigma=0.50 eV, non-emitter cutoff <=0.10 eV). Dataset lacks direct vs. indirect band gap classification. Indirect gap materials exhibit low radiative emission efficiency without phonon assistance."
    ),
    # Archived / Deferred Tracks (Preserved in registry but deactivated from active semiconductor workflow)
    "quantum_superconductor": UseCase(
        id="quantum_superconductor",
        name="Quantum: Superconducting Film (Deferred)",
        category="Quantum",
        description="Superconducting resonators, coplanar waveguides, and Josephson junction electrodes.",
        evidence_level="Strong",
        primary_model="tc",
        active=False,
        criteria=[
            Criterion(
                property_key="tc",
                function_type="ramp_up",
                params={"x_min": 1.5, "x_max": 9.2}  # 9.2 K corresponds to elemental Nb benchmark
            ),
            Criterion(
                property_key="bandgap",
                function_type="ramp_down",
                params={"x_min": 0.0, "x_max": 0.15} # Must be metallic / non-insulating in normal state
            )
        ],
        caveats="Deferred track. Normal state must be zero-gap metal. Surface loss tangent dominates qubit coherence."
    ),
    "quantum_insulator": UseCase(
        id="quantum_insulator",
        name="Quantum: Insulator / Barrier (Deferred)",
        category="Quantum",
        description="Low-loss substrate dielectric or tunnel junction barrier (e.g., Al2O3-like).",
        evidence_level="Heuristic",
        primary_model="bandgap",
        active=False,
        criteria=[
            Criterion(
                property_key="bandgap",
                function_type="ramp_up",
                params={"x_min": 3.2, "x_max": 5.0}
            )
        ],
        caveats="Deferred track. Wide band gap heuristic for suppressing two-level fluctuators (TLS) and leakage current."
    ),
    "stability_screen": UseCase(
        id="stability_screen",
        name="Thermodynamic Stability Screen (Deferred)",
        category="Screening",
        description="Thermodynamic formation favorability screen for battery and catalyst candidates.",
        evidence_level="Weak (Stability Screen Only)",
        primary_model="enthalpy",
        active=False,
        criteria=[
            Criterion(
                property_key="enthalpy",
                function_type="ramp_down",
                params={"x_min": -0.6, "x_max": -0.1}
            )
        ],
        caveats="Deferred track. Strictly a thermodynamic stability filter; does NOT evaluate electrochemical performance or catalytic turnover."
    ),
    "thermoelectric": UseCase(
        id="thermoelectric",
        name="Thermoelectric Power Generation (Deferred)",
        category="Energy",
        description="Waste heat recovery and Peltier solid-state thermal cooling.",
        evidence_level="Gated / Stretch",
        primary_model="zt",
        active=False,
        criteria=[
            Criterion(
                property_key="zt",
                function_type="ramp_up",
                params={"x_min": 0.5, "x_max": 1.5}
            )
        ],
        caveats="Deferred track due to limited sample size (197 materials)."
    )
}


def get_use_case(use_case_id: str) -> UseCase:
    if use_case_id not in REGISTRY:
        raise ValueError(f"Unknown use case '{use_case_id}'. Available: {list(REGISTRY.keys())}")
    return REGISTRY[use_case_id]


def list_use_cases(active_only: bool = True) -> List[Dict[str, Any]]:
    return [
        {
            "id": u.id,
            "name": u.name,
            "category": u.category,
            "description": u.description,
            "evidence_level": u.evidence_level,
            "primary_model": u.primary_model,
            "active": u.active,
            "caveats": u.caveats
        }
        for u in REGISTRY.values()
        if not active_only or u.active
    ]
