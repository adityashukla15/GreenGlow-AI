
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Challenge, ChallengeCompletion
from app.schemas.challenge import (
    ChallengeResponse,
    ChallengeCompleteRequest,
    ChallengeCompleteResponse,
    ChallengeCompletionStatusResponse,
)
from app.services.ai_content_service import generate_challenge_content
from app.services.grok_service import GroqServiceError
from app.services.user_service import find_user_by_email, normalize_email


router = APIRouter(
    prefix="/api/v1/challenges",
    tags=["Challenges"],
)


def normalize_text(value: str) -> str:
    return " ".join(value.split()).casefold()


async def replenish_challenges_for_user(
    db: Session,
    user_id: int,
) -> None:
    """Generate fresh challenges when fewer than three remain for a user."""

    remaining_count = (
        db.query(Challenge)
        .outerjoin(
            ChallengeCompletion,
            (ChallengeCompletion.challenge_id == Challenge.id)
            & (ChallengeCompletion.user_id == user_id),
        )
        .filter(
            Challenge.is_active.is_(True),
            ChallengeCompletion.id.is_(None),
        )
        .count()
    )

    if remaining_count >= 3:
        return

    try:
        generated_challenges = await generate_challenge_content()
    except GroqServiceError:
        # Completion is already committed. AI failure must not undo it.
        return

    existing_challenges = db.query(Challenge).all()

    existing_titles = {
        normalize_text(challenge.title)
        for challenge in existing_challenges
    }

    existing_descriptions = {
        normalize_text(challenge.description)
        for challenge in existing_challenges
    }

    new_challenges = []

    for item in generated_challenges:
        title = normalize_text(item.title)
        description = normalize_text(item.description)

        if title in existing_titles or description in existing_descriptions:
            continue

        existing_titles.add(title)
        existing_descriptions.add(description)

        new_challenges.append(
            Challenge(
                title=item.title.strip(),
                description=item.description.strip(),
                points=10,
                is_active=True,
            )
        )

    if not new_challenges:
        return

    try:
        db.add_all(new_challenges)
        db.commit()
    except SQLAlchemyError:
        db.rollback()


@router.get("/", response_model=list[ChallengeResponse])
def get_challenges(db: Session = Depends(get_db)):
    challenges = (
        db.query(Challenge)
        .filter(Challenge.is_active.is_(True))
        .order_by(Challenge.id.asc())
        .all()
    )

    return challenges


@router.get(
    "/completions",
    response_model=ChallengeCompletionStatusResponse,
)
def get_challenge_completions(
    email: str = Query(min_length=5, max_length=255),
    db: Session = Depends(get_db),
) -> ChallengeCompletionStatusResponse:
    normalized_email = normalize_email(email)
    if "@" not in normalized_email or "." not in normalized_email.split("@")[-1]:
        raise HTTPException(status_code=422, detail="Invalid email address")

    try:
        user = find_user_by_email(db, normalized_email)
        if user is None:
            return ChallengeCompletionStatusResponse(
                profile_exists=False,
                completed_challenge_ids=[],
            )

        completed_challenge_ids = [
            challenge_id
            for (challenge_id,) in (
                db.query(ChallengeCompletion.challenge_id)
                .filter(ChallengeCompletion.user_id == user.id)
                .order_by(ChallengeCompletion.challenge_id)
                .all()
            )
        ]
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=503,
            detail="Unable to load challenge completion status right now.",
        ) from exc

    return ChallengeCompletionStatusResponse(
        profile_exists=True,
        completed_challenge_ids=completed_challenge_ids,
    )


@router.post(
    "/{challenge_id}/complete",
    response_model=ChallengeCompleteResponse,
)
async def complete_challenge(
    challenge_id: int,
    request: ChallengeCompleteRequest,
    db: Session = Depends(get_db),
):
    challenge = (
        db.query(Challenge)
        .filter(
            Challenge.id == challenge_id,
            Challenge.is_active.is_(True),
        )
        .first()
    )

    if not challenge:
        raise HTTPException(
            status_code=404,
            detail="Challenge not found or inactive",
        )

    user = find_user_by_email(db, normalize_email(request.email))

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found. Complete the quiz first.",
        )

    existing_completion = (
        db.query(ChallengeCompletion)
        .filter(
            ChallengeCompletion.user_id == user.id,
            ChallengeCompletion.challenge_id == challenge.id,
        )
        .first()
    )

    if existing_completion:
        raise HTTPException(
            status_code=409,
            detail="You have already completed this challenge",
        )

    completion = ChallengeCompletion(
        user_id=user.id,
        challenge_id=challenge.id,
        points_awarded=challenge.points,
    )

    user.score += challenge.points
    db.add(completion)

    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="You have already completed this challenge",
        )

    # Replenishment happens after the completion is safely committed.
    await replenish_challenges_for_user(db, user.id)

    return {
        "message": "Challenge completed successfully",
        "challenge_title": challenge.title,
        "points_awarded": challenge.points,
        "total_score": user.score,
    }
