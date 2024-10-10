from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from app.api.main import api_router

app = FastAPI(title="Bike Fitting API", openapi_url="/api/openapi.json")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "http://0.0.0.0:8081"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
