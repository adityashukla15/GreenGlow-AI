from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.green_score import GreenScoreDashboard, GreenScoreQueryParam
from app.services.green_score_service import (
    GreenScoreUserNotFoundError,
    get_green_score_dashboard,
)


router = APIRouter(
    prefix="/api/v1/green-score",
    tags=["My Green Score"],
)


@router.get("", response_model=GreenScoreDashboard)
def get_green_score(
    query: GreenScoreQueryParam,
    db: Session = Depends(get_db),
) -> GreenScoreDashboard:
    try:
        return get_green_score_dashboard(db, query.email)
    except GreenScoreUserNotFoundError as exc:
        raise HTTPException(status_code=404, detail="User not found") from exc
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=503,
            detail="Unable to load the Green Score dashboard right now.",
        ) from exc
