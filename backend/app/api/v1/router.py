from fastapi import APIRouter

from backend.app.api.v1 import customers

api_router = APIRouter()
api_router.include_router(customers.router)