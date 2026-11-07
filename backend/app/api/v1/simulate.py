from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db
from backend.app.schemas.simulate import SimulationRequest, SimulationResponse
from backend.app.services.runs import resolve_run_id
from backend.app.services.simulate import load_population, simulate_scenario

router = APIRouter(prefix="/simulate", tags=["simulator"])


@router.post("", response_model=SimulationResponse)
def simulate(request: SimulationRequest, db: Session = Depends(get_db)):
    """Hypothetical retention campaigns. Nothing is saved; every figure rests on your assumptions."""
    run_id = resolve_run_id(db, request.analysis_run_id)
    if run_id is None:
        raise HTTPException(status_code=404, detail="no completed analysis run found")

    population = load_population(db, run_id)
    if population.empty:
        raise HTTPException(status_code=404, detail="no predictions found for this analysis run")

    try:
        results = [simulate_scenario(population, s) for s in request.scenarios]
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))

    return SimulationResponse(
        analysis_run_id=run_id, customers_considered=len(population), scenarios=results
    )