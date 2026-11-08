from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import User


def normalize_email(email: str) -> str:
    return email.strip().lower()


def find_user_by_email(db: Session, email: str) -> User | None:
    normalized_email = normalize_email(email)
    matches = (
        db.query(User)
        .filter(func.lower(func.trim(User.email)) == normalized_email)
        .limit(2)
        .all()
    )

    if len(matches) > 1:
        raise HTTPException(
            status_code=409,
            detail=(
                "Multiple user profiles match this email. "
                "Please contact support."
            ),
        )

    return matches[0] if matches else None
