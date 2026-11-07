import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import EcoSortGameSession, User
from app.schemas.eco_sort import (
    EcoSortAnswerResult,
    EcoSortEmailRequest,
    EcoSortGameStartResponse,
    EcoSortGameSubmitResponse,
    EcoSortSubmitRequest,
    EcoSortWasteItem,
)
from app.services.eco_sort_service import (
    GAME_ITEM_COUNT,
    ITEMS_BY_ID,
    POINTS_PER_CORRECT_ANSWER,
    get_public_items,
    select_game_item_ids,
)


router = APIRouter(
    prefix="/api/v1/eco-sort",
    tags=["Eco Sort Game"],
)


@router.get("/items", response_model=list[EcoSortWasteItem])
def list_eco_sort_items():
    return get_public_items()


@router.post("/start", response_model=EcoSortGameStartResponse)
def start_eco_sort_game(
    request: EcoSortEmailRequest,
    db: Session = Depends(get_db),
) -> EcoSortGameStartResponse:
    user = db.query(User).filter(User.email == request.email).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    item_ids = select_game_item_ids()
    session = EcoSortGameSession(
        token=secrets.token_urlsafe(32),
        user_id=user.id,
        item_ids=item_ids,
    )
    db.add(session)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=503,
            detail="Unable to start a game right now. Please try again.",
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=503,
            detail="Unable to start a game right now. Please try again.",
        ) from exc

    return EcoSortGameStartResponse(
        session_token=session.token,
        items=get_public_items(item_ids),
    )


@router.post("/submit", response_model=EcoSortGameSubmitResponse)
def submit_eco_sort_game(
    request: EcoSortSubmitRequest,
    db: Session = Depends(get_db),
) -> EcoSortGameSubmitResponse:
    game_session = (
        db.query(EcoSortGameSession)
        .filter(EcoSortGameSession.token == request.session_token)
        .first()
    )
    if game_session is None:
        raise HTTPException(status_code=404, detail="Game session not found")

    if game_session.user_id != (
        db.query(User.id).filter(User.email == request.email).scalar()
    ):
        raise HTTPException(status_code=403, detail="Email does not match game session")

    if game_session.submitted_at is not None:
        raise HTTPException(
            status_code=409,
            detail="Game session has already been submitted",
        )

    issued_ids = set(game_session.item_ids)
    submitted_ids = {answer.item_id for answer in request.answers}

    if len(request.answers) != GAME_ITEM_COUNT:
        raise HTTPException(
            status_code=422,
            detail="Submit exactly the items issued for this game",
        )

    if submitted_ids != issued_ids:
        raise HTTPException(
            status_code=422,
            detail="Submitted item IDs must exactly match the issued items",
        )

    results = []
    correct_count = 0
    for answer in request.answers:
        item = ITEMS_BY_ID.get(answer.item_id)
        if item is None:
            raise HTTPException(
                status_code=422,
                detail="One or more submitted item IDs are invalid",
            )

        is_correct = answer.selected_category == item.category
        if is_correct:
            correct_count += 1

        results.append(
            EcoSortAnswerResult(
                item_id=item.id,
                selected_category=answer.selected_category,
                correct_category=item.category,
                is_correct=is_correct,
                explanation=item.explanation,
            )
        )

    score = correct_count * POINTS_PER_CORRECT_ANSWER
    user_id = game_session.user_id

    try:
        claim = db.execute(
            update(EcoSortGameSession)
            .where(
                EcoSortGameSession.id == game_session.id,
                EcoSortGameSession.submitted_at.is_(None),
            )
            .values(
                submitted_at=func.current_timestamp(),
                awarded_score=score,
            )
        )
        if claim.rowcount != 1:
            db.rollback()
            raise HTTPException(
                status_code=409,
                detail="Game session has already been submitted",
            )

        score_update = db.execute(
            update(User)
            .where(User.id == user_id)
            .values(score=User.score + score)
        )
        if score_update.rowcount != 1:
            db.rollback()
            raise HTTPException(status_code=404, detail="User not found")

        total_score = db.execute(
            select(User.score).where(User.id == user_id)
        ).scalar_one()

        db.commit()
    except HTTPException:
        raise
    except OperationalError as exc:
        db.rollback()
        current_session = (
            db.query(EcoSortGameSession)
            .filter(EcoSortGameSession.token == request.session_token)
            .first()
        )
        if current_session is not None and current_session.submitted_at is not None:
            raise HTTPException(
                status_code=409,
                detail="Game session has already been submitted",
            ) from exc

        raise HTTPException(
            status_code=503,
            detail="Unable to record the game result. Please try again.",
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=503,
            detail="Unable to record the game result. Please try again.",
        ) from exc

    return EcoSortGameSubmitResponse(
        correct_answers=correct_count,
        total_items=len(results),
        score_awarded=score,
        total_score=total_score,
        results=results,
    )
