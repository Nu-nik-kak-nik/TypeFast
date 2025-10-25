import uuid
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime, timezone
from typing import override
from backend.app.db.database import Base


class User(Base):
    """Модель пользователя"""

    __tablename__: str = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    test_results: Mapped[list["TestResult"]] = relationship(
        "TestResult", back_populates="user", cascade="all, delete-orphan"
    )

    @override
    def __repr__(self) -> str:
        return f"<User(id={self.id}, created_at={self.created_at})>"


class TestResult(Base):
    """Модель результата теста печати"""

    __tablename__: str = "test_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    chars_per_minute: Mapped[float] = mapped_column(Float, nullable=False)
    accuracy: Mapped[float] = mapped_column(Float, nullable=False)
    time_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    language: Mapped[str] = mapped_column(String(10), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(10), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    user: Mapped["User"] = relationship("User", back_populates="test_results")

    __table_args__: tuple[Index, Index] = (
        Index("ix_test_results_user_created", "user_id", "created_at"),
        Index("ix_test_results_language_difficulty", "language", "difficulty"),
    )

    @override
    def __repr__(self) -> str:
        return f"<TestResult(id={self.id}, user_id={self.user_id}, cpm={self.chars_per_minute}, accuracy={self.accuracy}%)>"
