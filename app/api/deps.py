from collections.abc import AsyncGenerator
from typing import Annotated
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import Depends
from app.core.db import engine


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(engine) as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_db)]
