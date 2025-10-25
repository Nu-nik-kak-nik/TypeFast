from sqlalchemy import select, delete, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from backend.app.db.models import User, TestResult
from backend.app.schemas.db_schemas import (
    UserCreate,
    TestResultCreate,
    UserBestTestStatistics,
    UserAvgTestStatistics,
    UserLastTestStatistics,
)
import uuid
from datetime import datetime, timezone


class UserRepository:
    session: AsyncSession

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_data: UserCreate) -> User:
        user = User(id=str(uuid.uuid4()), created_at=datetime.now(timezone.utc))
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_by_id(self, user_id: str) -> User | None:
        query = select(User).where(User.id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def delete_by_id(self, user_id: str) -> bool:
        user = await self.get_by_id(user_id)
        if user:
            await self.session.delete(user)
            await self.session.commit()
            return True
        return False


class TestResultRepository:
    session: AsyncSession

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, test_result_data: TestResultCreate) -> TestResult:
        test_result = TestResult(**test_result_data.model_dump())
        self.session.add(test_result)
        await self.session.commit()
        await self.session.refresh(test_result)
        return test_result

    async def get_by_id(self, test_result_id: int) -> TestResult | None:
        query = select(TestResult).where(TestResult.id == test_result_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: str) -> list[TestResult]:
        query = select(TestResult).where(TestResult.user_id == user_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_filtered(
        self, language: str | None = None, difficulty: str | None = None
    ) -> list[TestResult]:
        query = select(TestResult)

        if language:
            query = query.where(TestResult.language == language)

        if difficulty:
            query = query.where(TestResult.difficulty == difficulty)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def delete_by_id(self, test_result_id: int) -> bool:
        test_result = await self.get_by_id(test_result_id)
        if test_result:
            await self.session.delete(test_result)
            await self.session.commit()
            return True
        return False

    async def delete_by_user_id(self, user_id: str) -> bool:
        query = delete(TestResult).where(TestResult.user_id == user_id)
        result = await self.session.execute(query)
        await self.session.commit()
        return True if result else False

    async def get_last_result_by_user_id(
        self, user_id: str
    ) -> UserLastTestStatistics | None:
        query = (
            select(TestResult)
            .where(TestResult.user_id == user_id)
            .order_by(desc(TestResult.created_at))
            .limit(1)
        )

        try:
            result = await self.session.execute(query)
            last_performance = result.scalar_one_or_none()

            if last_performance is None:
                return None

            return UserLastTestStatistics(
                time=last_performance.time_seconds,
                accuracy=last_performance.accuracy,
                chars_per_minute=last_performance.chars_per_minute,
                language=last_performance.language,
                difficulty=last_performance.difficulty,
            )

        except SQLAlchemyError as e:
            print(f"get_last_result_by_user_id ERROR: {e}")
            return None

    async def get_user_best_performance(
        self, user_id: str
    ) -> UserBestTestStatistics | None:
        query = select(
            func.min(TestResult.time_seconds).label("best_time"),
            func.max(TestResult.accuracy).label("max_accuracy"),
            func.max(TestResult.chars_per_minute).label("max_speed"),
        ).where(TestResult.user_id == user_id)

        try:
            result = await self.session.execute(query)
            best_performance = result.first()

            if best_performance is None:
                return None

            return UserBestTestStatistics(
                time=best_performance.best_time,
                accuracy=best_performance.max_accuracy,
                chars_per_minute=best_performance.max_speed,
            )

        except SQLAlchemyError as e:
            print(f"get_user_best_performance ERROR: {e}")
            return None

    async def get_user_test_result_statistics(
        self, user_id: str
    ) -> UserAvgTestStatistics | None:
        query = select(
            func.avg(TestResult.time_seconds).label("avg_time"),
            func.avg(TestResult.accuracy).label("avg_accuracy"),
            func.avg(TestResult.chars_per_minute).label("avg_chars_per_minute"),
            func.count(TestResult.id).label("total_tests"),
        ).where(TestResult.user_id == user_id)

        try:
            result = await self.session.execute(query)
            stats = result.first()

            if stats is None:
                return None

            return UserAvgTestStatistics(
                time=stats.avg_time,
                accuracy=stats.avg_accuracy,
                chars_per_minute=stats.avg_chars_per_minute,
                total_tests=stats.total_tests,
            )

        except SQLAlchemyError as e:
            print(f"get_user_test_result_statistics ERROR: {e}")
            return None
