from datetime import datetime, timedelta, timezone

from app.database import get_db
from app.models import (
    Challenge,
    ChallengeCompletion,
    EcoSortGameSession,
    QuizAttempt,
    QuizSession,
    User,
)


def create_user(client, email="green@example.com", score=0):
    db_generator = client.app.dependency_overrides[get_db]()
    db = next(db_generator)
    try:
        user = User(
            username=email.split("@")[0],
            email=email,
            score=score,
        )
        db.add(user)
        db.commit()
        return user.id
    finally:
        db.close()
        db_generator.close()


def read_green_score(client, email="green@example.com"):
    return client.get(
        "/api/v1/green-score",
        params={"email": email},
    )


def add_activity_records(client):
    db_generator = client.app.dependency_overrides[get_db]()
    db = next(db_generator)
    try:
        user = db.query(User).filter(User.email == "green@example.com").one()
        challenge = Challenge(
            title="Reusable lights",
            description="Choose reusable lighting decorations.",
            points=15,
            is_active=True,
        )
        quiz_session = QuizSession(
            token="fixture-quiz-session",
            email=user.email,
            question_ids=[],
            submitted_at=datetime.now(timezone.utc),
        )
        db.add_all([challenge, quiz_session])
        db.flush()

        now = datetime.now(timezone.utc)
        db.add_all(
            [
                QuizAttempt(
                    user_id=user.id,
                    quiz_session_id=quiz_session.id,
                    total_questions=10,
                    correct_answers=8,
                    score=80,
                    created_at=now - timedelta(minutes=3),
                ),
                ChallengeCompletion(
                    user_id=user.id,
                    challenge_id=challenge.id,
                    points_awarded=15,
                    completed_at=now - timedelta(minutes=2),
                ),
                EcoSortGameSession(
                    token="fixture-eco-sort-complete",
                    user_id=user.id,
                    item_ids=[1],
                    submitted_at=now - timedelta(minutes=1),
                    awarded_score=10,
                ),
                EcoSortGameSession(
                    token="fixture-eco-sort-incomplete",
                    user_id=user.id,
                    item_ids=[2],
                    submitted_at=None,
                    awarded_score=0,
                ),
            ]
        )
        db.commit()
        user.score += 105
        db.commit()
    finally:
        db.close()
        db_generator.close()


def test_unknown_email_returns_404(client):
    response = read_green_score(client, "unknown@example.com")

    assert response.status_code == 404


def test_new_user_has_zero_points_and_no_earned_achievements(client):
    create_user(client)

    response = read_green_score(client)

    assert response.status_code == 200
    data = response.json()
    assert data["total_points"] == 0
    assert data["total_completed_activities"] == 0
    assert data["achievement_count"] == 0
    assert not any(item["earned"] for item in data["achievements"])
    assert data["recent_activity"] == []


def test_quiz_challenge_and_submitted_eco_sort_points_are_aggregated(client):
    create_user(client)
    add_activity_records(client)

    response = read_green_score(client)

    assert response.status_code == 200
    data = response.json()
    assert data["total_points"] == 105
    assert data["score_breakdown"] == {
        "quiz_points": 80,
        "challenge_points": 15,
        "eco_sort_points": 10,
        "reconciliation_difference": 0,
    }


def test_incomplete_eco_sort_sessions_are_excluded(client):
    create_user(client)
    add_activity_records(client)

    data = read_green_score(client).json()

    assert data["activity_summary"]["completed_eco_sort_games"] == 1
    assert data["score_breakdown"]["eco_sort_points"] == 10


def test_abandoned_quiz_session_is_not_counted_as_completed(client):
    create_user(client)
    db_generator = client.app.dependency_overrides[get_db]()
    db = next(db_generator)
    try:
        db.add(
            QuizSession(
                token="abandoned-quiz-session",
                email="green@example.com",
                question_ids=[1, 2, 3],
                submitted_at=None,
            )
        )
        db.commit()
    finally:
        db.close()
        db_generator.close()

    data = read_green_score(client).json()

    assert data["total_completed_activities"] == 0
    assert data["activity_summary"]["completed_quizzes"] == 0
    assert data["score_breakdown"]["quiz_points"] == 0


def test_dashboard_reads_do_not_change_user_score_or_activity_records(client):
    create_user(client)
    add_activity_records(client)

    first = read_green_score(client).json()
    second = read_green_score(client).json()

    assert first == second
    db_generator = client.app.dependency_overrides[get_db]()
    db = next(db_generator)
    try:
        user = db.query(User).filter(User.email == "green@example.com").one()
        assert user.score == 105
        assert db.query(QuizAttempt).count() == 1
        assert db.query(ChallengeCompletion).count() == 1
        assert db.query(EcoSortGameSession).count() == 2
    finally:
        db.close()
        db_generator.close()


def test_achievement_conditions_and_progress(client):
    create_user(client)
    add_activity_records(client)

    data = read_green_score(client).json()
    achievements = {item["id"]: item for item in data["achievements"]}

    assert data["achievement_count"] == 3
    assert achievements["eco-beginner"]["earned"] is True
    assert achievements["eco-beginner"]["progress"] == 50
    assert achievements["eco-beginner"]["target"] == 50
    assert achievements["green-explorer"]["earned"] is False
    assert achievements["green-explorer"]["progress"] == 1
    assert achievements["challenge-starter"]["earned"] is True
    assert achievements["eco-sort-learner"]["earned"] is True
    assert achievements["green-champion"]["progress"] == 105
    assert achievements["eco-champion"]["progress"] == 3


def test_recent_activities_are_newest_first(client):
    create_user(client)
    add_activity_records(client)

    activities = read_green_score(client).json()["recent_activity"]

    assert [activity["activity_type"] for activity in activities] == [
        "eco_sort",
        "challenge",
        "quiz",
    ]
    assert activities[0]["points_earned"] == 10
    assert activities[1]["points_earned"] == 15
    assert activities[2]["points_earned"] == 80


def test_score_mismatch_is_explicitly_reconciled(client):
    create_user(client, score=120)
    add_activity_records(client)

    data = read_green_score(client).json()

    assert data["total_points"] == 225
    assert (
        data["score_breakdown"]["quiz_points"]
        + data["score_breakdown"]["challenge_points"]
        + data["score_breakdown"]["eco_sort_points"]
        == 105
    )
    assert data["score_breakdown"]["reconciliation_difference"] == 120


def test_existing_quiz_challenge_ai_and_eco_sort_routes_remain_available(
    client,
    monkeypatch,
):
    async def mock_eco_response(message):
        return "Choose reusable decorations."

    monkeypatch.setattr(
        "app.routes.ai.generate_eco_response",
        mock_eco_response,
    )

    assert client.get("/api/v1/quiz/questions").status_code == 200
    assert client.get("/api/v1/challenges/").status_code == 200
    assert client.post(
        "/api/v1/ai/assistant",
        json={"message": "Eco Diwali?"},
    ).status_code == 200
    assert client.get("/api/v1/eco-sort/items").status_code == 200
