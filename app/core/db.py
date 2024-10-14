from sqlalchemy.ext.asyncio import create_async_engine
import os


if os.getenv("ENV") == "PROD":
    engine = create_async_engine(
        f"postgresql+asyncpg://{os.getenv("POSTGRES_USER")}:{os.getenv("POSTGRES_PASSWORD")}@/{os.getenv("POSTGRES_DB")}"
        + f"?host=/cloudsql/{os.getenv("INSTANCE_CONNECTION_NAME")}",
    )
else:
    engine = create_async_engine(
        f"postgresql+asyncpg://{os.getenv("POSTGRES_USER")}:{os.getenv("POSTGRES_PASSWORD")}@{os.getenv("POSTGRES_ENDPOINT")}/{os.getenv("POSTGRES_DB")}",
    )
