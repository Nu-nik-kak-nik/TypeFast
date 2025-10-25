from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.database import new_session
from backend.app.db.database import Base, engine


async def get_session():
    async with new_session() as session:
        yield session


async def init_models():
    """Инициализация моделей"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


SessionDependency = Annotated[AsyncSession, Depends(get_session)]
