from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User

router = APIRouter(
    prefix="/api/v1/leaderboard",
    tags=["Leaderboard"]
)


@router.get("/")
def get_leaderboard(
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    users = (
        db.query(User)
        .order_by(
            User.score.desc(),
            User.id.asc()
        )
        .limit(limit)
        .all()
    )

    return [
        {
            "rank": index + 1,
            "username": user.username,
            "score": user.score
        }
        for index, user in enumerate(users)
    ]