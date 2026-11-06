from fastapi import APIRouter

from backend.app.api.v1 import customers, insights

api_router = APIRouter()
api_router.include_router(customers.router)
api_router.include_router(insights.router)