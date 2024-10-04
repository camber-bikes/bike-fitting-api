from fastapi import APIRouter

from app.api.routes import persons, scans

api_router = APIRouter()

api_router.include_router(persons.router, prefix="/persons", tags=["person"])
api_router.include_router(scans.router, prefix="/scans", tags=["scan"])
