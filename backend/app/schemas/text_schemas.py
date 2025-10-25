from pydantic import BaseModel, Field, field_validator
from backend.app.core.config import settings


class TextRequest(BaseModel):
    lang: str = Field(default="ru", description="Язык текста (ru/en)")
    difficulty: str = Field(
        default="easy", description="Уровень сложности (easy/medium/hard)"
    )

    @field_validator("lang")
    @classmethod
    def validate_language(cls, v: str) -> str:
        if v not in settings.allowed_languages:
            raise ValueError(
                f"Invalid language. Allowed values: {settings.allowed_languages}"
            )
        return v

    @field_validator("difficulty")
    @classmethod
    def validate_difficulty(cls, v: str) -> str:
        if v not in settings.allowed_levels:
            raise ValueError(
                f"Invalid difficulty. Allowed values: {settings.allowed_levels}"
            )
        return v

    class Config:
        json_schema_extra: dict[str, dict[str, str]] = {
            "example": {"lang": "ru", "difficulty": "medium"}
        }


class TextResponse(BaseModel):
    text: str = Field(..., description="Сгенерированный текст для печати")
    language: str = Field(..., description="Язык текста")
    difficulty: str = Field(..., description="Уровень сложности")

    class Config:
        json_schema_extra: dict[str, dict[str, str]] = {
            "example": {
                "text": "привет мир это пример текста для тренировки печати",
                "language": "ru",
                "difficulty": "easy",
            }
        }
