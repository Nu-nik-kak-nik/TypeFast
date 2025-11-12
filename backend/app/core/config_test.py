import logging
from pathlib import Path

from backend.app.core.config import Settings


class TestSettings(Settings):
    """Настройки для тестирования"""

    app_host: str = "127.0.0.1"
    app_port: int = 8001
    app_reload: bool = False

    database_name: str = ":memory:"
    database_url: str = "sqlite+aiosqlite:///:memory:"
    database_echo: bool = False
    database_future: bool = True

    logging_config_test: dict = {
        "logs_dir": Path("/tmp/test_logs"),
        "error_log_filename": "test_errors.log",
        "request_log_filename": "test_requests.log",
        "max_log_size_bytes": 1024 * 1024,
        "backup_count": 1,
        "log_level": logging.ERROR,
    }

    allowed_origins: list[str] = [
        "http://test",
        "http://localhost:8001",
        "http://127.0.0.1:8001",
    ]

    default_count_words: int = 10
    default_level_test: str = "easy"

    _number_of_words: dict = {
        "easy": 5,
        "medium": 8,
        "hard": 10,
        "test": 15,
    }

    class Config_Test:
        validate_assignment: bool = True
        arbitrary_types_allowed: bool = True


test_settings = TestSettings()
