from dotenv import load_dotenv
from fastapi import FastAPI
from app.api.main import api_router

load_dotenv()

app = FastAPI(title="Bike Fitting API", openapi_url="/api/openapi.json")

app.include_router(api_router, prefix="/api")
