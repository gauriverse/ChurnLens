from fastapi import APIRouter

from backend.app.api.v1 import customers, insights, model, segments,simulate

api_router = APIRouter()
api_router.include_router(customers.router)
api_router.include_router(insights.router)
api_router.include_router(segments.router)
api_router.include_router(model.router)
api_router.include_router(simulate.router)