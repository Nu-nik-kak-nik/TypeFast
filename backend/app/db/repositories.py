import uuid
from datetime import datetime, timezone
from sqlalchemy import select, delete, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, DBAPIError
from backend.app.db.models import User, TestResult
from backend.app.core.exceptions import DatabaseException, NotFoundException
from backend.app.schemas.db_schemas import (
    UserCreate,
    TestResultCreate,
    UserBestTestStatistics,
    UserAvgTestStatistics,
    UserLastTestStatistics,
)


class UserRepository:
    session: AsyncSession

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_data: UserCreate) -> User:
        try:
            user = User(id=str(uuid.uuid4()), created_at=datetime.now(timezone.utc))
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)
            return user
        except IntegrityError as e:
            await self.session.rollback()
            raise DatabaseException(
                "Failed to create user - integrity constraint violated", e
            )
        except (SQLAlchemyError, DBAPIError) as e:
            await self.session.rollback()
            raise DatabaseException("Failed to create user", e)

    async def get_by_id(self, user_id: str) -> User | None:
        try:
            query = select(User).where(User.id == user_id)
            result = await self.session.execute(query)
            user = result.scalar_one_or_none()

            if not user:
                raise NotFoundException("User", user_id)

            return user

        except (SQLAlchemyError, DBAPIError) as e:
            await self.session.rollback()
            raise DatabaseException(f"Failed to get user with id {user_id}", e)

    async def delete_by_id(self, user_id: str) -> bool:
        try:
            user = await self.get_by_id(user_id)
            if user:
                await self.session.delete(user)
                await self.session.commit()
                return True

            return False

        except NotFoundException:
            raise
        except (SQLAlchemyError, DBAPIError) as e:
            await self.session.rollback()
            raise DatabaseException(f"Failed to delete user with id {user_id}", e)


class TestResultRepository:
    session: AsyncSession

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, test_result_data: TestResultCreate) -> TestResult:
        try:
            test_result = TestResult(**test_result_data.model_dump())
            self.session.add(test_result)
            await self.session.commit()
            await self.session.refresh(test_result)
            return test_result

        except IntegrityError as e:
            await self.session.rollback()
            raise DatabaseException(
                "Failed to create test result - integrity constraint violated", e
            )
        except (SQLAlchemyError, DBAPIError) as e:
            await self.session.rollback()
            raise DatabaseException("Failed to create test result", e)

    async def get_by_id(self, test_result_id: int) -> TestResult | None:
        try:
            query = select(TestResult).where(TestResult.id == test_result_id)
            result = await self.session.execute(query)
            test_result = result.scalar_one_or_none()

            if not test_result:
                raise NotFoundException("TestResult", str(test_result_id))

            return test_result

        except (SQLAlchemyError, DBAPIError) as e:
            await self.session.rollback()
            raise DatabaseException(
                f"Failed to get test result with id {test_result_id}", e
            )

    async def get_by_user_id(self, user_id: str) -> list[TestResult]:
        try:
            query = select(TestResult).where(TestResult.user_id == user_id)
            result = await self.session.execute(query)
            return list(result.scalars().all())

        except (SQLAlchemyError, DBAPIError) as e:
            await self.session.rollback()
            raise DatabaseException(f"Failed to get test results for user {user_id}", e)

    async def get_filtered(
        self, language: str | None = None, difficulty: str | None = None
    ) -> list[TestResult]:
        try:
            query = select(TestResult)

            if language:
                query = query.where(TestResult.language == language)

            if difficulty:
                query = query.where(TestResult.difficulty == difficulty)

            result = await self.session.execute(query)
            return list(result.scalars().all())

        except (SQLAlchemyError, DBAPIError) as e:
            raise DatabaseException("Failed to get filtered test results", e)

    async def delete_by_id(self, test_result_id: int) -> bool:
        try:
            test_result = await self.get_by_id(test_result_id)
            if test_result:
                await self.session.delete(test_result)
                await self.session.commit()
                return True
            return False

        except NotFoundException:
            raise
        except (SQLAlchemyError, DBAPIError) as e:
            await self.session.rollback()
            raise DatabaseException(
                f"Failed to delete test result with id {test_result_id}", e
            )

    async def delete_by_user_id(self, user_id: str) -> bool:
        try:
            query = delete(TestResult).where(TestResult.user_id == user_id)
            result = await self.session.execute(query)
            await self.session.commit()
            return True if result else False

        except (SQLAlchemyError, DBAPIError) as e:
            await self.session.rollback()
            raise DatabaseException(
                f"Failed to delete test results for user {user_id}", e
            )

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

        except NotFoundException:
            raise
        except (SQLAlchemyError, DBAPIError) as e:
            raise DatabaseException(f"Failed to get last result for user {user_id}", e)

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

        except NotFoundException:
            raise
        except (SQLAlchemyError, DBAPIError) as e:
            raise DatabaseException(
                f"Failed to get best performance for user {user_id}", e
            )

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

        except NotFoundException:
            raise
        except (SQLAlchemyError, DBAPIError) as e:
            raise DatabaseException(f"Failed to get statistics for user {user_id}", e)
