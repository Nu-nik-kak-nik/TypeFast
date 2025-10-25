from pathlib import Path
from typing import Literal, TypedDict
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()


class WordLengthConfig(TypedDict):
    min: int | None
    max: int | None


class TextGenerationConfig(TypedDict):
    count_words: int
    level: Literal["easy", "medium", "hard"]


class DatabaseConfig(TypedDict):
    url: str
    echo: bool
    future: bool


class Settings(BaseModel):
    """Настройки приложения"""

    # App settings
    app_module: str = Field(default="backend.app.main:app")
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000)
    app_reload: bool = Field(default=True)

    # Path settings
    base_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parents[3])

    # File paths
    en_filepath: Path = Field(default=Path("backend/app/words_data/words_alpha.txt"))
    ru_filepath: Path = Field(
        default=Path("backend/app/words_data/singular_and_plural.txt")
    )
    default_filepath: Path = Field(
        default=Path("backend/app/words_data/singular_and_plural.txt")
    )

    # Frontend settings
    static_dir_name: str = Field(default="css")
    static_js_dir_name: str = Field(default="js")
    frontend_dir: Path = Field(default=Path("frontend"))
    html_dir: Path = Field(default=Path("frontend/html"))
    static_dir: Path = Field(default=Path("frontend/css"))
    static_js_dir: Path = Field(default=Path("frontend/js"))
    mount_css: str = Field(default="/static/css")
    mount_js: str = Field(default="/static/js")

    html_index_path: Path = Field(default=Path("frontend/html/index.html"))
    html_statistics_path: Path = Field(default=Path("frontend/html/statistics.html"))

    # Database settings
    database_name: str = Field(default="typing_test.db")
    database_url: str = Field(default="sqlite+aiosqlite:///typing_test.db")
    database_echo: bool = Field(default=True)
    database_future: bool = Field(default=True)

    # Application constants
    allowed_levels: list[Literal["easy", "medium", "hard", "test"]] = Field(
        default=["easy", "medium", "hard", "test"]
    )
    allowed_origins: list[str] = Field(
        default=["http://localhost:8000", "http://127.0.0.1:8000"]
    )
    allowed_languages: list[Literal["ru", "en"]] = Field(default=["ru", "en"])
    api_prefix: str = Field(default="/api")

    default_count_words: int = Field(default=50)
    default_level: Literal["easy", "medium", "hard"] = Field(default="easy")

    # Patterns
    language_pattern: str = Field(default="^(ru|en)$")
    difficulty_pattern: str = Field(default="^(easy|medium|hard)$")

    # Field constants
    chars_per_minute: str = Field(default="chars_per_minute")
    accuracy: str = Field(default="accuracy")
    time_seconds: str = Field(default="time_seconds")
    language: str = Field(default="language")
    difficulty: str = Field(default="difficulty")

    # Вычисляемые свойства
    _probability: dict[Literal["easy", "medium", "hard", "test"], float] = {
        "easy": -1.0,
        "medium": 0.15,
        "hard": 0.3,
        "test": 0.2,
    }

    _punctuation: dict[Literal["easy", "medium", "hard", "test"], list[str]] = {
        "easy": [" "],
        "medium": [" ", ". ", ", ", "! "],
        "hard": [" ", "! ", " — ", ". ", ", ", "; ", ": ", "? "],
        "test": ["! ", " - ", ". ", ", ", "; ", ": ", "? "],
    }

    _word_lengths: dict[Literal["easy", "medium", "hard", "test"], WordLengthConfig] = {
        "easy": {"min": None, "max": 6},
        "medium": {"min": 3, "max": 10},
        "hard": {"min": 5, "max": None},
        "test": {"min": None, "max": 5},
    }

    _number_of_words: dict[Literal["easy", "medium", "hard", "test"], int] = {
        "easy": 30,
        "medium": 35,
        "hard": 40,
        "test": 50,
    }

    class Config:
        validate_assignment = True
        arbitrary_types_allowed = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._calculate_paths()

    def _calculate_paths(self) -> None:
        """Вычисляем абсолютные пути на основе base_dir"""
        self.frontend_dir = self.base_dir / self.frontend_dir
        self.html_dir = self.base_dir / self.html_dir
        self.static_dir = self.base_dir / self.static_dir
        self.static_js_dir = self.base_dir / self.static_js_dir
        self.html_index_path = self.base_dir / self.html_index_path
        self.html_statistics_path = self.base_dir / self.html_statistics_path
        self.en_filepath = self.base_dir / self.en_filepath
        self.ru_filepath = self.base_dir / self.ru_filepath
        self.default_filepath = self.base_dir / self.default_filepath

        # Обновляем URL базы данных с абсолютным путем
        if "sqlite" in self.database_url and not self.database_url.startswith(
            "sqlite+aiosqlite:///"
        ):
            db_path = self.base_dir / self.database_name
            self.database_url = f"sqlite+aiosqlite:///{db_path}"

    @property
    def database_config(self) -> DatabaseConfig:
        return {
            "url": self.database_url,
            "echo": self.database_echo,
            "future": self.database_future,
        }

    @property
    def probability(self) -> dict[Literal["easy", "medium", "hard", "test"], float]:
        return self._probability

    @property
    def punctuation(self) -> dict[Literal["easy", "medium", "hard", "test"], list[str]]:
        return self._punctuation

    @property
    def word_lengths(
        self,
    ) -> dict[Literal["easy", "medium", "hard", "test"], WordLengthConfig]:
        return self._word_lengths

    @property
    def number_of_words(self) -> dict[Literal["easy", "medium", "hard", "test"], int]:
        return self._number_of_words

    @property
    def language_filepath(self) -> dict[Literal["ru", "en"], Path]:
        return {
            "ru": self.ru_filepath,
            "en": self.en_filepath,
        }

    @property
    def text_generation_config(
        self,
    ) -> dict[
        Literal["ru", "en"],
        dict[Literal["easy", "medium", "hard"], TextGenerationConfig],
    ]:
        return {
            "ru": {
                "easy": {"count_words": self.number_of_words["easy"], "level": "easy"},
                "medium": {
                    "count_words": self.number_of_words["medium"],
                    "level": "medium",
                },
                "hard": {"count_words": self.number_of_words["hard"], "level": "hard"},
            },
            "en": {
                "easy": {"count_words": self.number_of_words["easy"], "level": "easy"},
                "medium": {
                    "count_words": self.number_of_words["medium"],
                    "level": "medium",
                },
                "hard": {"count_words": self.number_of_words["hard"], "level": "hard"},
            },
        }


# Глобальный экземпляр настроек
settings = Settings()
