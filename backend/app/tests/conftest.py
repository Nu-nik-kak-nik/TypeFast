"""Глобальные фиксчуры для всех тестов."""

import asyncio
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# Устанавливаем режим тестирования
os.environ["TESTING"] = "1"

from backend.app.core.config_test import test_settings
from backend.app.db.models import Base, TestResult
from backend.app.main import app

# ============================================================================
# КОНСТАНТЫ ДЛЯ ТЕСТОВ
# ============================================================================

TEST_USER_ID = "test_user_123"
TEST_USER_ID_2 = "test_user_456"
TEST_RESULT_ID = "test_result_1"
TEST_RESULT_ID_2 = "test_result_2"

TEST_WORDS = [
    "привет",
    "мир",
    "тест",
    "слово",
    "пример",
    "текст",
    "данные",
    "проверка",
    "результат",
    "успех",
    "ошибка",
    "файл",
    "словарь",
    "программа",
    "компьютер",
    "интернет",
    "сеть",
    "сервер",
    "клиент",
    "протокол",
]

TEST_WORDS_WITH_COMMENTS = [
    "привет",
    "-комментарий",
    "мир",
    "тест",
    "-еще комментарий",
    "слово",
    "пример",
]

# ============================================================================
# MOCK МОДЕЛИ
# ============================================================================


@dataclass
class MockUser:
    """Mock пользователя для тестов."""

    id: str = TEST_USER_ID
    name: str = "Test User"
    created_at: datetime | None = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class MockTestResult:
    """Mock результата теста для тестов."""

    id: str = TEST_RESULT_ID
    user_id: str = TEST_USER_ID
    chars_per_minute: float = 85.5
    accuracy: float = 95.2
    time_seconds: float = 60.0
    language: str = "ru"
    difficulty: str = "easy"
    created_at: datetime | None = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

    def dict(self):
        """Преобразовать в словарь."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "chars_per_minute": self.chars_per_minute,
            "accuracy": self.accuracy,
            "time_seconds": self.time_seconds,
            "language": self.language,
            "difficulty": self.difficulty,
            "created_at": self.created_at,
        }


# ============================================================================
# ФИКСЧУРЫ - КОНФИГУРАЦИЯ И ПРИЛОЖЕНИЕ
# ============================================================================


@pytest.fixture
def settings():
    """Фиксчура для получения тестовых настроек."""
    return test_settings


@pytest.fixture
def app_fixture():
    """Фиксчура для приложения."""
    return app


# ============================================================================
# ФИКСЧУРЫ - EVENT LOOP И БД
# ============================================================================


@pytest.fixture(scope="session")
def event_loop():
    """Создает event loop для всех тестов."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def engine():
    """Создает асинхронный движок БД."""
    engine = create_async_engine(
        test_settings.database_url,
        echo=test_settings.database_echo,
        connect_args={"check_same_thread": False},
    )

    # Создаем таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Очищаем таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def async_session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Создает асинхронную сессию БД."""
    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()


# ============================================================================
# ФИКСЧУРЫ - HTTP КЛИЕНТ
# ============================================================================


@pytest_asyncio.fixture
async def async_client():
    """Async HTTP клиент для тестов."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


# ============================================================================
# ФИКСЧУРЫ - РЕПОЗИТОРИИ (СИНХРОННЫЕ!)
# ============================================================================


@pytest.fixture
def user_repository(async_session):
    """Репозиторий пользователей - СИНХРОННАЯ фиксчура!"""
    from backend.app.db.repositories import UserRepository

    return UserRepository(async_session)


@pytest.fixture
def test_result_repository(async_session):
    """Репозиторий результатов тестов - СИНХРОННАЯ фиксчура!"""
    from backend.app.db.repositories import TestResultRepository

    return TestResultRepository(async_session)


# ============================================================================
# ФИКСЧУРЫ - ТЕСТОВЫЕ ДАННЫЕ
# ============================================================================


@pytest.fixture
def valid_test_result_data(settings):
    """Валидные данные для теста результата."""
    return {
        "user_id": TEST_USER_ID,
        "chars_per_minute": 85.5,
        "accuracy": 95.2,
        "time_seconds": 60.0,
        "language": "ru",
        "difficulty": "easy",
    }


# ============================================================================
# ФИКСЧУРЫ - РЕЗУЛЬТАТЫ ТЕСТОВ (ОДИНОЧНЫЕ И НАБОРЫ)
# ============================================================================


def _create_test_result(
    result_id: str,
    user_id: str,
    chars_per_minute: float,
    accuracy: float,
    time_seconds: float,
    difficulty: str = "easy",
    days_ago: int = 0,
) -> TestResult:
    """Создать объект TestResult для тестирования."""
    return TestResult(
        id=result_id,
        user_id=user_id,
        chars_per_minute=chars_per_minute,
        accuracy=accuracy,
        time_seconds=time_seconds,
        language="ru",
        difficulty=difficulty,
        created_at=datetime.now() - timedelta(days=days_ago),
    )


@pytest.fixture
def single_test_result() -> TestResult:
    """Один результат теста."""
    return _create_test_result("result_1", TEST_USER_ID, 50.0, 85.0, 120.0, days_ago=0)


@pytest.fixture
def two_test_results() -> list[TestResult]:
    """Два результата теста."""
    return [
        _create_test_result("result_1", TEST_USER_ID, 50.0, 85.0, 120.0, days_ago=1),
        _create_test_result("result_2", TEST_USER_ID, 60.0, 90.0, 100.0, days_ago=0),
    ]


@pytest.fixture
def improving_test_results() -> list[TestResult]:
    """Результаты с улучшением всех показателей."""
    return [
        _create_test_result("result_1", TEST_USER_ID, 40.0, 80.0, 150.0, days_ago=3),
        _create_test_result("result_2", TEST_USER_ID, 50.0, 85.0, 120.0, days_ago=2),
        _create_test_result("result_3", TEST_USER_ID, 60.0, 90.0, 100.0, days_ago=1),
        _create_test_result("result_4", TEST_USER_ID, 70.0, 95.0, 80.0, days_ago=0),
    ]


@pytest.fixture
def declining_test_results() -> list[TestResult]:
    """Результаты с ухудшением всех показателей."""
    return [
        _create_test_result(
            "result_1", TEST_USER_ID, 80.0, 95.0, 60.0, "medium", days_ago=3
        ),
        _create_test_result(
            "result_2", TEST_USER_ID, 70.0, 90.0, 80.0, "medium", days_ago=2
        ),
        _create_test_result(
            "result_3", TEST_USER_ID, 60.0, 85.0, 100.0, "medium", days_ago=1
        ),
        _create_test_result(
            "result_4", TEST_USER_ID, 50.0, 80.0, 120.0, "medium", days_ago=0
        ),
    ]


@pytest.fixture
def consistent_test_results() -> list[TestResult]:
    """Результаты со стабильными показателями."""
    return [
        _create_test_result(
            "result_1", TEST_USER_ID, 75.0, 92.0, 80.0, "medium", days_ago=3
        ),
        _create_test_result(
            "result_2", TEST_USER_ID, 76.0, 91.5, 79.5, "medium", days_ago=2
        ),
        _create_test_result(
            "result_3", TEST_USER_ID, 74.5, 92.5, 80.5, "medium", days_ago=1
        ),
        _create_test_result(
            "result_4", TEST_USER_ID, 75.5, 92.0, 80.0, "medium", days_ago=0
        ),
    ]


@pytest.fixture
def inconsistent_test_results() -> list[TestResult]:
    """Результаты с нестабильными показателями."""
    return [
        _create_test_result(
            "result_1", TEST_USER_ID, 40.0, 70.0, 150.0, "hard", days_ago=3
        ),
        _create_test_result(
            "result_2", TEST_USER_ID, 90.0, 98.0, 50.0, "hard", days_ago=2
        ),
        _create_test_result(
            "result_3", TEST_USER_ID, 30.0, 60.0, 180.0, "hard", days_ago=1
        ),
        _create_test_result(
            "result_4", TEST_USER_ID, 95.0, 99.0, 45.0, "hard", days_ago=0
        ),
    ]


@pytest.fixture
def mixed_test_results() -> list[TestResult]:
    """Результаты с улучшением скорости и ухудшением точности."""
    return [
        _create_test_result("result_1", TEST_USER_ID, 50.0, 95.0, 120.0, days_ago=2),
        _create_test_result("result_2", TEST_USER_ID, 70.0, 85.0, 85.0, days_ago=0),
    ]


# ============================================================================
# ФИКСЧУРЫ - ФАЙЛЫ
# ============================================================================


@pytest.fixture
def temp_dictionary_file() -> Generator[str, None, None]:
    """Создать временный файл со словарём."""
    with tempfile.NamedTemporaryFile(
        mode="w", delete=False, suffix=".txt", encoding="utf-8"
    ) as f:
        for word in TEST_WORDS:
            f.write(word + "\n")
        temp_path = f.name

    yield temp_path

    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def empty_dictionary_file() -> Generator[str, None, None]:
    """Создать пустой файл словаря."""
    with tempfile.NamedTemporaryFile(
        mode="w", delete=False, suffix=".txt", encoding="utf-8"
    ) as f:
        temp_path = f.name

    yield temp_path

    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def dictionary_file_with_special_chars() -> Generator[str, None, None]:
    """Создать файл со специальными символами и комментариями."""
    with tempfile.NamedTemporaryFile(
        mode="w", delete=False, suffix=".txt", encoding="utf-8"
    ) as f:
        for word in TEST_WORDS_WITH_COMMENTS:
            f.write(word + "\n")
        temp_path = f.name

    yield temp_path

    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def non_empty_dictionary_file() -> Generator[str, None, None]:
    """Создать непустой файл со словарём."""
    words = ["тест", "слово", "пример"]

    with tempfile.NamedTemporaryFile(
        mode="w", delete=False, suffix=".txt", encoding="utf-8"
    ) as f:
        for word in words:
            f.write(word + "\n")
        temp_path = f.name

    yield temp_path

    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def large_dictionary_file() -> Generator[str, None, None]:
    """Создать большой файл со словарём (1000+ слов)."""
    with tempfile.NamedTemporaryFile(
        mode="w", delete=False, suffix=".txt", encoding="utf-8"
    ) as f:
        for i in range(1000):
            f.write(f"слово_{i}\n")
        temp_path = f.name

    yield temp_path

    if os.path.exists(temp_path):
        os.unlink(temp_path)


# ============================================================================
# ФИКСЧУРЫ - МОКИ
# ============================================================================


@pytest.fixture
def mock_user_repository():
    """Mock UserRepository."""
    with patch("backend.app.api.routes.UserRepository") as mock_class:
        mock_repo = AsyncMock()
        mock_user = MockUser(id=TEST_USER_ID)

        mock_repo.get_by_id = AsyncMock(return_value=mock_user)
        mock_repo.create = AsyncMock(return_value=mock_user)
        mock_repo.delete_by_id = AsyncMock(return_value=True)

        mock_class.return_value = mock_repo
        yield mock_repo


@pytest.fixture
def mock_test_result_repository():
    """Mock TestResultRepository."""
    with patch("backend.app.api.routes.TestResultRepository") as mock_class:
        mock_repo = AsyncMock()
        mock_result = MockTestResult(
            id=TEST_RESULT_ID,
            user_id=TEST_USER_ID,
            chars_per_minute=85.5,
            accuracy=95.2,
            time_seconds=60.0,
            language="ru",
            difficulty="easy",
        )

        mock_repo.create = AsyncMock(return_value=mock_result)
        mock_repo.get_by_id = AsyncMock(return_value=mock_result)
        mock_repo.get_by_user_id = AsyncMock(return_value=[mock_result])
        mock_repo.get_filtered = AsyncMock(return_value=[mock_result])
        mock_repo.delete_by_id = AsyncMock(return_value=True)
        mock_repo.delete_by_user_id = AsyncMock(return_value=True)
        mock_repo.get_last_result_by_user_id = AsyncMock(return_value=mock_result)
        mock_repo.get_user_best_performance = AsyncMock(return_value=mock_result)
        mock_repo.get_user_test_result_statistics = AsyncMock(return_value={})

        mock_class.return_value = mock_repo
        yield mock_repo


@pytest.fixture
def mock_settings(settings):
    """Mock settings."""
    with patch("backend.app.api.routes.settings") as mock:
        mock.database_url = settings.database_url
        mock.allowed_origins = settings.allowed_origins
        mock.default_count_words = settings.default_count_words
        mock.default_level_test = settings.default_level_test
        yield mock


@pytest.fixture
def mock_word_extractor():
    """Mock WordExtractor."""
    with patch("backend.app.api.routes.WordExtractor") as mock_class:
        mock_instance = MagicMock()
        mock_instance.generate_random_text = MagicMock(
            return_value="Это тестовый текст"
        )
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_progress_calculator():
    """Mock ProgressCalculator."""
    with patch(
        "backend.app.services.progress_calculator.UserProgressCalculator"
    ) as mock_class:
        mock_instance = MagicMock()
        mock_instance.calculate_progress = MagicMock(
            return_value={
                "speed_progress": 10.5,
                "accuracy_progress": 5.2,
                "time_progress": 8.3,
                "consistency_score": 85.0,
            }
        )
        mock_class.return_value = mock_instance
        yield mock_instance
