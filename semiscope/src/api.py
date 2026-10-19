"""
FastAPI REST API Service for SemiScope.
Exposes endpoints for:
- Health checking and metadata (/health)
- Use case registry enumeration (/usecases)
- Mode 2 Material analysis (/analyze)
- Mode 1 Material recommendation (/recommend)
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.registry import list_use_cases, get_use_case, REGISTRY
from src.scoring import score_material_all_usecases, score_material_for_usecase, get_candidate_pool
from src.precompute_pool import recommend_materials
from src.explain import synthesize_explanation, explain_prediction

app = FastAPI(
    title="SemiScope API",
    description="Explainable materials discovery engine for semiconductor band-gap screening, solar absorbers, and optoelectronics.",
    version="1.0.0"
)


class AnalyzeRequest(BaseModel):
    material: str = Field(..., example="GaAs", description="Chemical formula or CIF string")
    is_cif: bool = Field(False, description="True if input is CIF text or file path")
    explain: bool = Field(True, description="Generate natural language explanation and SHAP drivers")
    active_only: bool = Field(True, description="Limit analysis to active semiconductor use cases")


class RecommendRequest(BaseModel):
    use_case_id: str = Field(..., example="solar", description="Target use case ID (solar, semiconductor, led)")
    top_n: int = Field(10, ge=1, le=100, description="Number of top candidate materials to return")
    measured_only: bool = Field(False, description="Only return materials with experimental measurements")
    explain: bool = Field(False, description="Synthesize natural language explanation for top results")
    use_full_pool: bool = Field(False, description="Search archived 21.5k multi-domain pool instead of canonical 4,604 Band-Gap Benchmark and Candidate Catalog")


@app.get("/health")
def health_check():
    pool = get_candidate_pool(use_full_pool=False)
    return {
        "status": "healthy",
        "system": "SemiScope Semiconductor Discovery Engine v1.0",
        "primary_catalog": "Band-Gap Benchmark and Candidate Catalog",
        "primary_catalog_size": len(pool),
        "active_use_cases": ["solar", "semiconductor", "led"],
        "primary_model": "bandgap"
    }


@app.get("/usecases")
def get_use_cases_list(active_only: bool = True):
    return list_use_cases(active_only=active_only)


@app.post("/analyze")
def analyze_material(payload: AnalyzeRequest):
    """
    Mode 2: Material -> Semiconductor Applications.
    Evaluates one composition or CIF structure across semiconductor use cases.
    """
    try:
        ranked_results = score_material_all_usecases(
            material_input=payload.material,
            is_cif=payload.is_cif,
            active_only=payload.active_only
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Material evaluation error: {str(e).splitlines()[0]}")

    if payload.explain:
        for item in ranked_results:
            item["explanation"] = synthesize_explanation(item)

    return {
        "material": ranked_results[0]["material"] if ranked_results else payload.material,
        "results": ranked_results
    }
@app.post("/recommend")
def recommend_candidates(payload: RecommendRequest):
    """
    Mode 1: Application -> Top Candidate Semiconductors.
    Screens the canonical 4,604 semiconductor catalog and returns the highest scoring candidates.
    """
    try:
        candidates = recommend_materials(
            use_case_id=payload.use_case_id,
            top_n=payload.top_n,
            measured_only=payload.measured_only,
            use_full_pool=payload.use_full_pool
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if payload.explain:
        uc = get_use_case(payload.use_case_id)
        for cand in candidates:
            # Generate detailed score dict for explanation synthesis
            s_dict = score_material_for_usecase(cand["formula"], uc)
            cand["explanation"] = synthesize_explanation(s_dict)

    return {
        "use_case_id": payload.use_case_id,
        "catalog": "archived_21k_pool" if payload.use_full_pool else "canonical_4604_semiconductors",
        "total_returned": len(candidates),
        "candidates": candidates
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
