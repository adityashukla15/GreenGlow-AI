from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    UniqueConstraint,
    func
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    quiz_session_id: Mapped[int | None] = mapped_column(
        ForeignKey("quiz_sessions.id", ondelete="SET NULL"),
        nullable=True
    )

    total_questions: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    correct_answers: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    score: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "quiz_session_id",
            name="uq_quiz_attempt_session"
        ),
    )
