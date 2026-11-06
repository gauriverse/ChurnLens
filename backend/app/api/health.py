from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db
from backend.app.schemas.health import DatabaseHealth, Health

router = APIRouter(tags=["health"])


@router.get("/health", response_model=Health)
def liveness():
    return Health(status="ok")

@router.get("/health/db", response_model=DatabaseHealth)
def readiness(db:Session = Depends(get_db)):
    try:
        db.execute(text("select 1"))
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="database unavailable")
    return DatabaseHealth(status="ok", database="connected")