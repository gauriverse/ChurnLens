from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db
from backend.app.schemas.predict import CustomerFeatures, PredictionResult
from backend.app.services.model_loader import ModelUnavailable
from backend.app.services.predict import InvalidFeatures, predict_customer

router = APIRouter(prefix="/predict", tags=["predict"])


@router.post("", response_model=PredictionResult)
def predict(features: CustomerFeatures, db: Session = Depends(get_db)):
    """Score one customer with the active model. Nothing is saved."""
    try:
        return predict_customer(db, features.model_dump())
    except InvalidFeatures as error:
        raise HTTPException(status_code=422, detail=error.problems)
    except ModelUnavailable as error:
        raise HTTPException(status_code=503, detail=str(error))