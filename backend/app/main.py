import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError

from backend.app.api import health
from backend.app.api.v1.router import api_router
from backend.app.core.config import get_cors_origins

logger = logging.getLogger("uvicorn.error")

def create_app() -> FastAPI:
    app = FastAPI(
        title="ChurnLens API",
        version="0.1.0",
        description=(
             "Explainable customer churn intelligence. Predictions are calibrated "
            "probabilities, not certainties. Retention figures are hypothetical, "
            "based on assumed offer cost and success rate."
        ),
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_cors_origins(),
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    @app.exception_handler(OperationalError)
    async def database_unavailable(request: Request, exc: OperationalError):
        
        logger.error(
            "database unavailable during %s %s: %s", request.method, request.url.path, exc.orig
        )
        return JSONResponse(
            status_code=503,
            content={"detail": "database temporarily unavailable, please retry"},
            headers={"Retry-After": "5"},
        )


    app.include_router(health.router)
    app.include_router(api_router, prefix="/api/v1")
    return app

app = create_app()