from backend.app.db.database import Base, engine


async def create_tables():
    """Создание всех таблиц"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Таблицы успешно созданы")


async def drop_tables():
    """Удаление всех таблиц"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    print("Таблицы успешно удалены")
