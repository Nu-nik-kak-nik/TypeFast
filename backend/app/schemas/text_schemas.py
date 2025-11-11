from pydantic import BaseModel, Field, field_validator

from backend.app.core.config import settings


class TextRequest(BaseModel):
    lang: str = Field(default="ru")
    difficulty: str = Field(default="easy")

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


class TextResponse(BaseModel):
    text: str = Field(...)
    language: str = Field(...)
    difficulty: str = Field(...)
