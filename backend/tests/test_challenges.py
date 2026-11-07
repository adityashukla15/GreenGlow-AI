
from contextlib import contextmanager

import pytest

from app.database import get_db
from app.models import Challenge, ChallengeCompletion, User
from app.schemas.ai import GeneratedChallenge
from app.services.grok_service import GroqServiceError


@contextmanager
def db_session(client):
    db_generator = client.app.dependency_overrides[get_db]()
    db = next(db_generator)

    try:
        yield db
    finally:
        db.close()
        db_generator.close()


def create_user_and_challenges(
    client,
    email="test@example.com",
    username="test_user",
    challenge_count=5,
):
    with db_session(client) as db:
        user = User(
            username=username,
            email=email,
            score=0,
        )
        db.add(user)
        db.flush()

        challenges = [
            Challenge(
                title=f"Seed Challenge {i}",
                description=f"Complete sustainable activity number {i}.",
                points=10,
                is_active=True,
            )
            for i in range(1, challenge_count + 1)
        ]

        db.add_all(challenges)
        db.commit()

        return user.id, [challenge.id for challenge in challenges]


def fake_generated_challenges(count=3):
    return [
        GeneratedChallenge(
            title=f"Fresh Eco Challenge {i}",
            description=f"Complete this fresh eco-friendly activity number {i}.",
        )
        for i in range(1, count + 1)
    ]


def patch_challenge_generator(monkeypatch, challenges=None, error=None):
    from app.routes import challenges as challenge_routes

    calls = []

    async def fake_generator():
        calls.append(True)

        if error:
            raise error

        return challenges if challenges is not None else fake_generated_challenges()

    monkeypatch.setattr(
        challenge_routes,
        "generate_challenge_content",
        fake_generator,
        raising=False,
    )

    return calls


# --------------------------------------------------
# GET CHALLENGES
# --------------------------------------------------

def test_get_challenges_returns_active_challenges(client):
    create_user_and_challenges(client)

    response = client.get("/api/v1/challenges/")

    assert response.status_code == 200
    assert len(response.json()) == 5


def test_get_challenges_excludes_inactive_challenges(client):
    _, challenge_ids = create_user_and_challenges(client)

    with db_session(client) as db:
        challenge = db.query(Challenge).filter(
            Challenge.id == challenge_ids[0]
        ).first()

        challenge.is_active = False
        db.commit()

    response = client.get("/api/v1/challenges/")

    assert response.status_code == 200
    assert len(response.json()) == 4

    returned_ids = {item["id"] for item in response.json()}
    assert challenge_ids[0] not in returned_ids


# --------------------------------------------------
# CHALLENGE COMPLETION
# --------------------------------------------------

def test_complete_challenge_successfully(client):
    create_user_and_challenges(client)

    response = client.post(
        "/api/v1/challenges/1/complete",
        json={"email": "test@example.com"},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Challenge completed successfully"
    assert response.json()["points_awarded"] == 10
    assert response.json()["total_score"] == 10


def test_complete_challenge_awards_correct_points(client):
    _, challenge_ids = create_user_and_challenges(client)

    with db_session(client) as db:
        challenge = db.query(Challenge).filter(
            Challenge.id == challenge_ids[0]
        ).first()

        challenge.points = 25
        db.commit()

    response = client.post(
        f"/api/v1/challenges/{challenge_ids[0]}/complete",
        json={"email": "test@example.com"},
    )

    assert response.status_code == 200
    assert response.json()["points_awarded"] == 25
    assert response.json()["total_score"] == 25


def test_complete_challenge_creates_completion_record(client):
    _, challenge_ids = create_user_and_challenges(client)

    response = client.post(
        f"/api/v1/challenges/{challenge_ids[0]}/complete",
        json={"email": "test@example.com"},
    )

    assert response.status_code == 200

    with db_session(client) as db:
        completion = db.query(ChallengeCompletion).first()

        assert completion is not None
        assert completion.points_awarded == 10


def test_complete_challenge_updates_user_score(client):
    create_user_and_challenges(client)

    client.post(
        "/api/v1/challenges/1/complete",
        json={"email": "test@example.com"},
    )

    with db_session(client) as db:
        user = db.query(User).filter(
            User.email == "test@example.com"
        ).first()

        assert user.score == 10


# --------------------------------------------------
# DUPLICATE COMPLETION
# --------------------------------------------------

def test_duplicate_challenge_completion_returns_409(client):
    create_user_and_challenges(client)

    payload = {"email": "test@example.com"}

    first = client.post(
        "/api/v1/challenges/1/complete",
        json=payload,
    )

    second = client.post(
        "/api/v1/challenges/1/complete",
        json=payload,
    )

    assert first.status_code == 200
    assert second.status_code == 409


def test_duplicate_completion_does_not_increase_score(client):
    create_user_and_challenges(client)

    payload = {"email": "test@example.com"}

    client.post("/api/v1/challenges/1/complete", json=payload)
    client.post("/api/v1/challenges/1/complete", json=payload)

    with db_session(client) as db:
        user = db.query(User).filter(
            User.email == "test@example.com"
        ).first()

        assert user.score == 10

        count = db.query(ChallengeCompletion).filter(
            ChallengeCompletion.user_id == user.id
        ).count()

        assert count == 1


# --------------------------------------------------
# INVALID REQUESTS
# --------------------------------------------------

def test_complete_nonexistent_challenge_returns_404(client):
    create_user_and_challenges(client)

    response = client.post(
        "/api/v1/challenges/99999/complete",
        json={"email": "test@example.com"},
    )

    assert response.status_code == 404


def test_complete_inactive_challenge_returns_404(client):
    _, challenge_ids = create_user_and_challenges(client)

    with db_session(client) as db:
        challenge = db.query(Challenge).filter(
            Challenge.id == challenge_ids[0]
        ).first()

        challenge.is_active = False
        db.commit()

    response = client.post(
        f"/api/v1/challenges/{challenge_ids[0]}/complete",
        json={"email": "test@example.com"},
    )

    assert response.status_code == 404


def test_complete_challenge_with_unknown_user_returns_404(client):
    create_user_and_challenges(client)

    response = client.post(
        "/api/v1/challenges/1/complete",
        json={"email": "unknown@example.com"},
    )

    assert response.status_code == 404


def test_complete_challenge_rejects_invalid_email(client):
    create_user_and_challenges(client)

    response = client.post(
        "/api/v1/challenges/1/complete",
        json={"email": "invalid-email"},
    )

    assert response.status_code == 422


# --------------------------------------------------
# REPLENISHMENT THRESHOLD
# --------------------------------------------------

def test_does_not_replenish_when_three_challenges_remain(
    client,
    monkeypatch,
):
    _, challenge_ids = create_user_and_challenges(client)

    calls = patch_challenge_generator(
        monkeypatch,
        fake_generated_challenges(),
    )

    for challenge_id in challenge_ids[:2]:
        response = client.post(
            f"/api/v1/challenges/{challenge_id}/complete",
            json={"email": "test@example.com"},
        )
        assert response.status_code == 200

    assert len(calls) == 0


def test_replenishes_when_remaining_challenges_drop_below_three(
    client,
    monkeypatch,
):
    _, challenge_ids = create_user_and_challenges(client)

    calls = patch_challenge_generator(
        monkeypatch,
        fake_generated_challenges(3),
    )

    for challenge_id in challenge_ids[:3]:
        response = client.post(
            f"/api/v1/challenges/{challenge_id}/complete",
            json={"email": "test@example.com"},
        )
        assert response.status_code == 200

    assert len(calls) == 1

    with db_session(client) as db:
        generated = db.query(Challenge).filter(
            Challenge.title.like("Fresh Eco Challenge%")
        ).all()

        assert len(generated) == 3


def test_generated_challenges_receive_backend_assigned_points(
    client,
    monkeypatch,
):
    _, challenge_ids = create_user_and_challenges(client)

    patch_challenge_generator(
        monkeypatch,
        fake_generated_challenges(3),
    )

    for challenge_id in challenge_ids[:3]:
        client.post(
            f"/api/v1/challenges/{challenge_id}/complete",
            json={"email": "test@example.com"},
        )

    with db_session(client) as db:
        generated = db.query(Challenge).filter(
            Challenge.title.like("Fresh Eco Challenge%")
        ).all()

        assert len(generated) == 3
        assert all(item.points == 10 for item in generated)


# --------------------------------------------------
# DUPLICATE AI CONTENT
# --------------------------------------------------

def test_replenishment_filters_duplicate_titles(
    client,
    monkeypatch,
):
    _, challenge_ids = create_user_and_challenges(client)

    generated = [
        GeneratedChallenge(
            title="Seed Challenge 4",
            description="A completely different eco-friendly activity.",
        ),
        GeneratedChallenge(
            title="Fresh Unique Challenge",
            description="Complete a unique sustainable activity today.",
        ),
        GeneratedChallenge(
            title="Another Unique Challenge",
            description="Try another sustainable activity with your family.",
        ),
    ]

    patch_challenge_generator(monkeypatch, generated)

    for challenge_id in challenge_ids[:3]:
        client.post(
            f"/api/v1/challenges/{challenge_id}/complete",
            json={"email": "test@example.com"},
        )

    with db_session(client) as db:
        duplicate_count = db.query(Challenge).filter(
            Challenge.title == "Seed Challenge 4"
        ).count()

        assert duplicate_count == 1


def test_replenishment_filters_duplicate_descriptions(
    client,
    monkeypatch,
):
    _, challenge_ids = create_user_and_challenges(client)

    generated = [
        GeneratedChallenge(
            title="New Title One",
            description="Complete sustainable activity number 4.",
        ),
        GeneratedChallenge(
            title="New Title Two",
            description="A completely new sustainable activity for families.",
        ),
        GeneratedChallenge(
            title="New Title Three",
            description="Explore another reusable decoration idea today.",
        ),
    ]

    patch_challenge_generator(monkeypatch, generated)

    for challenge_id in challenge_ids[:3]:
        client.post(
            f"/api/v1/challenges/{challenge_id}/complete",
            json={"email": "test@example.com"},
        )

    with db_session(client) as db:
        duplicate_count = db.query(Challenge).filter(
            Challenge.description == "Complete sustainable activity number 4."
        ).count()

        assert duplicate_count == 1


# --------------------------------------------------
# GROQ FAILURE HANDLING
# --------------------------------------------------

def test_groq_failure_does_not_fail_challenge_completion(
    client,
    monkeypatch,
):
    _, challenge_ids = create_user_and_challenges(
        client,
        challenge_count=3,
    )

    patch_challenge_generator(
        monkeypatch,
        error=GroqServiceError("Groq unavailable"),
    )

    response = client.post(
        f"/api/v1/challenges/{challenge_ids[0]}/complete",
        json={"email": "test@example.com"},
    )

    assert response.status_code == 200
    assert response.json()["points_awarded"] == 10
    assert response.json()["total_score"] == 10

    with db_session(client) as db:
        completion = db.query(ChallengeCompletion).first()
        assert completion is not None


# --------------------------------------------------
# USER-SPECIFIC COMPLETION HISTORY
# --------------------------------------------------

def test_replenishment_uses_user_specific_completion_history(
    client,
    monkeypatch,
):
    _, challenge_ids = create_user_and_challenges(client)

    with db_session(client) as db:
        second_user = User(
            username="second_user",
            email="second@example.com",
            score=0,
        )
        db.add(second_user)
        db.commit()

    calls = patch_challenge_generator(
        monkeypatch,
        fake_generated_challenges(3),
    )

    # First user completes three challenges.
    for challenge_id in challenge_ids[:3]:
        client.post(
            f"/api/v1/challenges/{challenge_id}/complete",
            json={"email": "test@example.com"},
        )

    assert len(calls) == 1

    # Second user still has the original challenges available.
    response = client.post(
        f"/api/v1/challenges/{challenge_ids[0]}/complete",
        json={"email": "second@example.com"},
    )

    assert response.status_code == 200
    assert len(calls) == 1


# --------------------------------------------------
# INACTIVE CHALLENGE COUNTING
# --------------------------------------------------

def test_inactive_challenges_are_not_counted_as_remaining(
    client,
    monkeypatch,
):
    _, challenge_ids = create_user_and_challenges(client)

    with db_session(client) as db:
        for challenge_id in challenge_ids[3:]:
            challenge = db.query(Challenge).filter(
                Challenge.id == challenge_id
            ).first()

            challenge.is_active = False

        db.commit()

    calls = patch_challenge_generator(
        monkeypatch,
        fake_generated_challenges(3),
    )

    response = client.post(
        f"/api/v1/challenges/{challenge_ids[0]}/complete",
        json={"email": "test@example.com"},
    )

    assert response.status_code == 200
    assert len(calls) == 1
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Challenge, ChallengeCompletion, User
from app.schemas.challenge import (
    ChallengeResponse,
    ChallengeCompleteRequest,
    ChallengeCompleteResponse,
)
from app.services.ai_content_service import generate_challenge_content
from app.services.grok_service import GroqServiceError


router = APIRouter(
    prefix="/api/v1/challenges",
    tags=["Challenges"],
)


def normalize_text(value: str) -> str:
    """Normalize text for duplicate detection."""
    return " ".join(value.split()).casefold()


async def replenish_challenges_for_user(
    db: Session,
    user_id: int,
) -> None:
    """
    Generate fresh global challenges when this user's remaining
    active, incomplete challenges drop below three.

    Challenge records are global, but completion history is user-specific.
    """

    remaining_count = (
        db.query(Challenge.id)
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
        # AI availability must not block challenge completion.
        return

    # Include inactive challenges too, so old content is not regenerated.
    existing_challenges = (
        db.query(Challenge.title, Challenge.description)
        .all()
    )

    existing_titles = {
        normalize_text(challenge.title)
        for challenge in existing_challenges
    }

    existing_descriptions = {
        normalize_text(challenge.description)
        for challenge in existing_challenges
    }

    new_challenges = []

    for generated in generated_challenges:
        normalized_title = normalize_text(generated.title)
        normalized_description = normalize_text(generated.description)

        if normalized_title in existing_titles:
            continue

        if normalized_description in existing_descriptions:
            continue

        # Add accepted content to the sets to prevent duplicates
        # within the same generated batch.
        existing_titles.add(normalized_title)
        existing_descriptions.add(normalized_description)

        new_challenges.append(
            Challenge(
                title=generated.title,
                description=generated.description,
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
        # Replenishment failure must not undo the completed challenge.


@router.get("/", response_model=list[ChallengeResponse])
def get_challenges(db: Session = Depends(get_db)):
    challenges = (
        db.query(Challenge)
        .filter(Challenge.is_active.is_(True))
        .order_by(Challenge.id.asc())
        .all()
    )

    return challenges


@router.post(
    "/{challenge_id}/complete",
    response_model=ChallengeCompleteResponse,
)
async def complete_challenge(
    challenge_id: int,
    request: ChallengeCompleteRequest,
    db: Session = Depends(get_db),
):
    # Find the requested active challenge.
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

    # Find the user using their registered email.
    user = (
        db.query(User)
        .filter(User.email == request.email)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found. Complete the quiz first.",
        )

    # Prevent duplicate challenge completion.
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

    # Record completion and award points.
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

    # Replenish only after the completion and score are safely committed.
    # This operation does not change the completion response.
    await replenish_challenges_for_user(
        db=db,
        user_id=user.id,
    )

    return {
        "message": "Challenge completed successfully",
        "challenge_title": challenge.title,
        "points_awarded": challenge.points,
        "total_score": user.score,
    }
