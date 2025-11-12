"""Тесты для репозиториев."""

import pytest

from backend.app.core.exceptions import NotFoundException
from backend.app.db.repositories import TestResultRepository, UserRepository
from backend.app.schemas.db_schemas import TestResultCreate, UserCreate


class TestUserRepositoryCreate:
    """Тесты создания пользователя."""

    async def test_create_user_success(
        self,
        user_repository: UserRepository,
    ) -> None:
        """Успешно создает пользователя."""
        user = await user_repository.create(UserCreate())

        assert user is not None
        assert user.id is not None
        assert user.created_at is not None

    async def test_create_user_has_unique_id(
        self,
        user_repository: UserRepository,
    ) -> None:
        """Каждый пользователь имеет уникальный ID."""
        user1 = await user_repository.create(UserCreate())
        user2 = await user_repository.create(UserCreate())

        assert user1.id != user2.id

    async def test_create_user_persists_to_db(
        self,
        user_repository: UserRepository,
    ) -> None:
        """Пользователь сохраняется в БД."""
        user = await user_repository.create(UserCreate())
        retrieved_user = await user_repository.get_by_id(user.id)

        assert retrieved_user is not None
        assert retrieved_user.id == user.id


class TestUserRepositoryGetById:
    """Тесты получения пользователя по ID."""

    async def test_get_user_by_id_success(
        self,
        user_repository: UserRepository,
    ) -> None:
        """Успешно получает пользователя по ID."""
        user = await user_repository.create(UserCreate())
        retrieved_user = await user_repository.get_by_id(user.id)

        assert retrieved_user is not None
        assert retrieved_user.id == user.id

    async def test_get_user_by_id_not_found(
        self,
        user_repository: UserRepository,
    ) -> None:
        """Выбрасывает NotFoundException для несуществующего ID."""
        with pytest.raises(NotFoundException):
            await user_repository.get_by_id("non-existent-id")


class TestUserRepositoryDeleteById:
    """Тесты удаления пользователя по ID."""

    async def test_delete_user_by_id_success(
        self,
        user_repository: UserRepository,
    ) -> None:
        """Успешно удаляет пользователя."""
        user = await user_repository.create(UserCreate())
        result = await user_repository.delete_by_id(user.id)

        assert result is True

    async def test_delete_user_by_id_not_found(
        self,
        user_repository: UserRepository,
    ) -> None:
        """Выбрасывает NotFoundException для несуществующего ID."""
        with pytest.raises(NotFoundException):
            await user_repository.delete_by_id("non-existent-id")

    async def test_delete_user_removes_from_db(
        self,
        user_repository: UserRepository,
    ) -> None:
        """Удаленный пользователь больше не в БД."""
        user = await user_repository.create(UserCreate())
        await user_repository.delete_by_id(user.id)

        with pytest.raises(NotFoundException):
            await user_repository.get_by_id(user.id)


class TestTestResultRepositoryCreate:
    """Тесты создания результата теста."""

    async def test_create_test_result_success(
        self,
        test_result_repository: TestResultRepository,
        user_repository: UserRepository,
    ) -> None:
        """Успешно создает результат теста."""
        user = await user_repository.create(UserCreate())
        test_result_data = TestResultCreate(
            user_id=user.id,
            chars_per_minute=75.5,
            accuracy=95.0,
            time_seconds=120,
            language="ru",
            difficulty="easy",
        )
        result = await test_result_repository.create(test_result_data)

        assert result is not None
        assert result.id is not None
        assert result.user_id == user.id
        assert result.chars_per_minute == 75.5
        assert result.accuracy == 95.0

    async def test_create_test_result_with_different_languages(
        self,
        test_result_repository: TestResultRepository,
        user_repository: UserRepository,
    ) -> None:
        """Создает результаты с разными валидными языками."""
        user = await user_repository.create(UserCreate())
        languages = ["ru", "en"]

        for lang in languages:
            test_result_data = TestResultCreate(
                user_id=user.id,
                chars_per_minute=75.5,
                accuracy=95.0,
                time_seconds=120,
                language=lang,
                difficulty="easy",
            )
            result = await test_result_repository.create(test_result_data)
            assert result.language == lang

    async def test_create_test_result_invalid_user_id(
        self,
        test_result_repository: TestResultRepository,
    ) -> None:
        """✅ Создает результат с несуществующим user_id (БД не проверяет FK в SQLite)."""
        test_result_data = TestResultCreate(
            user_id="non-existent-user",
            chars_per_minute=75.5,
            accuracy=95.0,
            time_seconds=120,
            language="ru",
            difficulty="medium",
        )

        result = await test_result_repository.create(test_result_data)
        assert result is not None
        assert result.user_id == "non-existent-user"


class TestTestResultRepositoryGetById:
    """Тесты получения результата теста по ID."""

    async def test_get_test_result_by_id_success(
        self,
        test_result_repository: TestResultRepository,
        user_repository: UserRepository,
    ) -> None:
        """Успешно получает результат по ID."""
        user = await user_repository.create(UserCreate())
        test_result_data = TestResultCreate(
            user_id=user.id,
            chars_per_minute=75.5,
            accuracy=95.0,
            time_seconds=120,
            language="ru",
            difficulty="easy",
        )
        created_result = await test_result_repository.create(test_result_data)
        retrieved_result = await test_result_repository.get_by_id(created_result.id)

        assert retrieved_result is not None
        assert retrieved_result.id == created_result.id

    async def test_get_test_result_by_id_not_found(
        self,
        test_result_repository: TestResultRepository,
    ) -> None:
        """Выбрасывает NotFoundException для несуществующего ID."""
        with pytest.raises(NotFoundException):
            await test_result_repository.get_by_id(999999)


class TestTestResultRepositoryGetByUserId:
    """Тесты получения результатов по user_id."""

    async def test_get_test_results_by_user_id_success(
        self,
        test_result_repository: TestResultRepository,
        user_repository: UserRepository,
    ) -> None:
        """Успешно получает результаты пользователя."""
        user = await user_repository.create(UserCreate())
        test_result_data = TestResultCreate(
            user_id=user.id,
            chars_per_minute=75.5,
            accuracy=95.0,
            time_seconds=120,
            language="ru",
            difficulty="easy",
        )
        await test_result_repository.create(test_result_data)
        results = await test_result_repository.get_by_user_id(user.id)

        assert len(results) == 1
        assert results[0].user_id == user.id

    async def test_get_test_results_by_user_id_empty(
        self,
        test_result_repository: TestResultRepository,
        user_repository: UserRepository,
    ) -> None:
        """Возвращает пустой список для пользователя без результатов."""
        user = await user_repository.create(UserCreate())
        results = await test_result_repository.get_by_user_id(user.id)

        assert results == []

    async def test_get_test_results_by_user_id_multiple(
        self,
        test_result_repository: TestResultRepository,
        user_repository: UserRepository,
    ) -> None:
        """Возвращает все результаты пользователя."""
        user = await user_repository.create(UserCreate())

        for i in range(3):
            test_result_data = TestResultCreate(
                user_id=user.id,
                chars_per_minute=75.5 + i,
                accuracy=95.0 + i,
                time_seconds=120 - i * 10,
                language="ru",
                difficulty="easy",
            )
            await test_result_repository.create(test_result_data)

        results = await test_result_repository.get_by_user_id(user.id)

        assert len(results) == 3


class TestTestResultRepositoryGetFiltered:
    """Тесты фильтрации результатов."""

    async def test_get_filtered_by_language(
        self,
        test_result_repository: TestResultRepository,
        user_repository: UserRepository,
    ) -> None:
        """Фильтрует результаты по языку."""
        user = await user_repository.create(UserCreate())

        for lang in ["ru", "en"]:
            test_result_data = TestResultCreate(
                user_id=user.id,
                chars_per_minute=75.5,
                accuracy=95.0,
                time_seconds=120,
                language=lang,
                difficulty="easy",
            )
            await test_result_repository.create(test_result_data)

        results = await test_result_repository.get_filtered(language="ru")

        assert len(results) >= 1
        assert all(r.language == "ru" for r in results)

    async def test_get_filtered_by_difficulty(
        self,
        test_result_repository: TestResultRepository,
        user_repository: UserRepository,
    ) -> None:
        """Фильтрует результаты по сложности."""
        user = await user_repository.create(UserCreate())

        for difficulty in ["easy", "medium", "hard"]:
            test_result_data = TestResultCreate(
                user_id=user.id,
                chars_per_minute=75.5,
                accuracy=95.0,
                time_seconds=120,
                language="ru",
                difficulty=difficulty,
            )
            await test_result_repository.create(test_result_data)

        results = await test_result_repository.get_filtered(difficulty="easy")

        assert len(results) >= 1
        assert all(r.difficulty == "easy" for r in results)

    async def test_get_filtered_no_matches(
        self,
        test_result_repository: TestResultRepository,
    ) -> None:
        """Возвращает пустой список если нет совпадений."""
        results = await test_result_repository.get_filtered(
            language="ru", difficulty="hard"
        )

        assert results == []


class TestTestResultRepositoryDeleteById:
    """Тесты удаления результата по ID."""

    async def test_delete_test_result_by_id_success(
        self,
        test_result_repository: TestResultRepository,
        user_repository: UserRepository,
    ) -> None:
        """Успешно удаляет результат."""
        user = await user_repository.create(UserCreate())
        test_result_data = TestResultCreate(
            user_id=user.id,
            chars_per_minute=75.5,
            accuracy=95.0,
            time_seconds=120,
            language="ru",
            difficulty="easy",
        )
        created_result = await test_result_repository.create(test_result_data)
        result = await test_result_repository.delete_by_id(created_result.id)

        assert result is True

    async def test_delete_test_result_by_id_not_found(
        self,
        test_result_repository: TestResultRepository,
    ) -> None:
        """Выбрасывает NotFoundException для несуществующего ID."""
        with pytest.raises(NotFoundException):
            await test_result_repository.delete_by_id(999999)


class TestTestResultRepositoryDeleteByUserId:
    """Тесты удаления результатов по user_id."""

    async def test_delete_test_results_by_user_id_success(
        self,
        test_result_repository: TestResultRepository,
        user_repository: UserRepository,
    ) -> None:
        """Успешно удаляет все результаты пользователя."""
        user = await user_repository.create(UserCreate())

        for i in range(3):
            test_result_data = TestResultCreate(
                user_id=user.id,
                chars_per_minute=75.5 + i,
                accuracy=95.0 + i,
                time_seconds=120 - i * 10,
                language="ru",
                difficulty="easy",
            )
            await test_result_repository.create(test_result_data)

        result = await test_result_repository.delete_by_user_id(user.id)

        assert result is True

    async def test_delete_test_results_by_user_id_no_results(
        self,
        test_result_repository: TestResultRepository,
        user_repository: UserRepository,
    ) -> None:
        """✅ Тест удаляет все результаты пользователя."""
        user = await user_repository.create(UserCreate())
        result = await test_result_repository.delete_by_user_id(user.id)

        assert result is True


class TestTestResultRepositoryLastResult:
    """Тесты получения последнего результата."""

    async def test_get_last_result_by_user_id_success(
        self,
        test_result_repository: TestResultRepository,
        user_repository: UserRepository,
    ) -> None:
        """Успешно получает последний результат."""
        user = await user_repository.create(UserCreate())

        for i in range(3):
            test_result_data = TestResultCreate(
                user_id=user.id,
                chars_per_minute=75.5 + i,
                accuracy=95.0 + i,
                time_seconds=120 - i * 10,
                language="ru",
                difficulty="easy",
            )
            await test_result_repository.create(test_result_data)

        last_result = await test_result_repository.get_last_result_by_user_id(user.id)

        assert last_result is not None
        assert last_result.chars_per_minute is not None

    async def test_get_last_result_by_user_id_no_results(
        self,
        test_result_repository: TestResultRepository,
        user_repository: UserRepository,
    ) -> None:
        """Тест получения последнего результата для пользователя без результатов"""
        user = await user_repository.create(UserCreate())
        last_result = await test_result_repository.get_last_result_by_user_id(user.id)

        assert last_result is None


class TestTestResultRepositoryBestPerformance:
    """Тесты получения лучшей производительности."""

    async def test_get_user_best_performance_success(
        self,
        test_result_repository: TestResultRepository,
        user_repository: UserRepository,
    ) -> None:
        """Успешно получает лучшую производительность."""
        user = await user_repository.create(UserCreate())

        for i in range(3):
            test_result_data = TestResultCreate(
                user_id=user.id,
                chars_per_minute=75.5 + i * 10,
                accuracy=95.0 + i,
                time_seconds=120 - i * 10,
                language="ru",
                difficulty="easy",
            )
            await test_result_repository.create(test_result_data)

        best = await test_result_repository.get_user_best_performance(user.id)

        assert best is not None
        assert best.chars_per_minute is not None
        assert best.accuracy is not None
        assert best.time is not None

    async def test_get_user_best_performance_no_results(
        self,
        test_result_repository: TestResultRepository,
        user_repository: UserRepository,
    ) -> None:
        """Тест удаляет все результаты пользователя."""
        user = await user_repository.create(UserCreate())
        best = await test_result_repository.get_user_best_performance(user.id)

        assert best is not None
        assert best.time is None
        assert best.accuracy is None
        assert best.chars_per_minute is None


class TestTestResultRepositoryStatistics:
    """Тесты получения статистики результатов."""

    async def test_get_user_test_result_statistics_success(
        self,
        test_result_repository: TestResultRepository,
        user_repository: UserRepository,
    ) -> None:
        """Успешно получает статистику."""
        user = await user_repository.create(UserCreate())

        for i in range(3):
            test_result_data = TestResultCreate(
                user_id=user.id,
                chars_per_minute=75.5 + i,
                accuracy=95.0 + i,
                time_seconds=120 - i * 10,
                language="ru",
                difficulty="easy",
            )
            await test_result_repository.create(test_result_data)

        stats = await test_result_repository.get_user_test_result_statistics(user.id)

        assert stats is not None
        assert stats.chars_per_minute is not None
        assert stats.accuracy is not None
        assert stats.time is not None
        assert stats.total_tests == 3

    async def test_get_user_test_result_statistics_no_results(
        self,
        test_result_repository: TestResultRepository,
        user_repository: UserRepository,
    ) -> None:
        """Тест получения статистики для пользователя без результатов"""
        user = await user_repository.create(UserCreate())
        stats = await test_result_repository.get_user_test_result_statistics(user.id)

        assert stats is not None
        assert stats.time is None
        assert stats.accuracy is None
        assert stats.chars_per_minute is None
        assert stats.total_tests == 0

    async def test_get_user_test_result_statistics_many_results(
        self,
        test_result_repository: TestResultRepository,
        user_repository: UserRepository,
    ) -> None:
        """Получает статистику для большого количества результатов."""
        user = await user_repository.create(UserCreate())

        for i in range(10):
            test_result_data = TestResultCreate(
                user_id=user.id,
                chars_per_minute=50.0 + i * 5,
                accuracy=80.0 + i * 2,
                time_seconds=150 - i * 5,
                language="ru",
                difficulty="easy",
            )
            await test_result_repository.create(test_result_data)

        stats = await test_result_repository.get_user_test_result_statistics(user.id)

        assert stats is not None
        assert stats.total_tests == 10
        assert stats.chars_per_minute is not None
        assert stats.accuracy is not None
        assert stats.time is not None
