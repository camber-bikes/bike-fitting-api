from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from app.api.main import api_router


app = FastAPI(title="Bike Fitting API", openapi_url="/api/openapi.json")

app.include_router(api_router, prefix="/api")
