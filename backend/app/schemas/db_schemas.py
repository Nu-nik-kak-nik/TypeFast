from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import ClassVar
from backend.app.core.config import settings


class UserBase(BaseModel):
    id: str | None = None
    created_at: datetime | None = None


class UserCreate(BaseModel):
    pass


class UserResponse(UserBase):
    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)


class TestResultBase(BaseModel):
    user_id: str
    chars_per_minute: float = Field(gt=0, description="Символов в минуту")
    accuracy: float = Field(ge=0, le=100, description="Точность в процентах")
    time_seconds: float = Field(gt=0, description="Время выполнения в секундах")
    language: str = Field(pattern=settings.language_pattern, description="Язык теста")
    difficulty: str = Field(
        pattern=settings.difficulty_pattern, description="Сложность теста"
    )
    created_at: datetime | None = None


class TestResultCreate(TestResultBase):
    pass


class TestResultResponse(TestResultBase):
    id: int

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)


class TestResultWithUser(TestResultResponse):
    user: UserResponse


class UserBestTestStatistics(BaseModel):
    time: float | None = None
    accuracy: float | None = None
    chars_per_minute: float | None = None


class UserLastTestStatistics(UserBestTestStatistics):
    language: str | None = None
    difficulty: str | None = None


class UserAvgTestStatistics(UserBestTestStatistics):
    total_tests: int = 0
