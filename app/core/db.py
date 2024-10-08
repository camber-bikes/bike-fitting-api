from sqlalchemy.ext.asyncio import create_async_engine
import os

engine = create_async_engine(
    f"postgresql+asyncpg://{os.getenv("POSTGRES_USER")}:{os.getenv("POSTGRES_PASSWORD")}@{os.getenv("POSTGRES_ENDPOINT")}/{os.getenv("POSTGRES_DB")}"
)
