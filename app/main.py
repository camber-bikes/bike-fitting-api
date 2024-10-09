from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from app.api.main import api_router

from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware, allowed_hosts=["*"]
)

app = FastAPI(title="Bike Fitting API", openapi_url="/api/openapi.json")

app.include_router(api_router, prefix="/api")
