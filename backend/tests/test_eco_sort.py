from concurrent.futures import ThreadPoolExecutor

from sqlalchemy.orm import Session as SQLAlchemySession
from sqlalchemy.sql.dml import Update

from app.database import get_db
from app.models import EcoSortGameSession, User
from app.services.eco_sort_service import ITEMS_BY_ID


def create_user(client, email="sorter@example.com", score=0):
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


def start_game(client, email="sorter@example.com"):
    response = client.post(
        "/api/v1/eco-sort/start",
        json={"email": email},
    )
    assert response.status_code == 200
    return response.json()


def make_answers(game, *, incorrect_item_id=None):
    answers = []
    for item in game["items"]:
        item_id = item["id"]
        category = ITEMS_BY_ID[item_id].category
        if item_id == incorrect_item_id:
            category = next(
                candidate
                for candidate in ("wet", "dry", "recyclable")
                if candidate != category
            )
        answers.append(
            {"item_id": item_id, "selected_category": category}
        )
    return answers


def submit_game(client, game, answers, email="sorter@example.com"):
    return client.post(
        "/api/v1/eco-sort/submit",
        json={
            "email": email,
            "session_token": game["session_token"],
            "answers": answers,
        },
    )


def test_get_items_does_not_expose_correct_categories(client):
    response = client.get("/api/v1/eco-sort/items")

    assert response.status_code == 200
    assert len(response.json()) == 12
    assert all(
        "category" not in item and "correct_category" not in item
        for item in response.json()
    )


def test_start_game_persists_issued_items_for_existing_user(client):
    user_id = create_user(client)

    game = start_game(client)

    assert len(game["session_token"]) >= 40
    assert len(game["items"]) == 10
    db_generator = client.app.dependency_overrides[get_db]()
    db = next(db_generator)
    try:
        session = (
            db.query(EcoSortGameSession)
            .filter(EcoSortGameSession.token == game["session_token"])
            .one()
        )
        assert session.user_id == user_id
        assert set(session.item_ids) == {
            item["id"] for item in game["items"]
        }
        assert session.submitted_at is None
        assert session.awarded_score == 0
    finally:
        db.close()
        db_generator.close()


def test_correct_sorting_awards_backend_calculated_score(client):
    create_user(client)
    game = start_game(client)

    response = submit_game(client, game, make_answers(game))

    assert response.status_code == 200
    assert response.json()["correct_answers"] == 10
    assert response.json()["score_awarded"] == 100
    assert response.json()["total_score"] == 100
    assert all(result["is_correct"] for result in response.json()["results"])


def test_incorrect_sorting_does_not_award_points_for_wrong_answers(client):
    create_user(client)
    game = start_game(client)
    wrong_id = game["items"][0]["id"]

    response = submit_game(
        client,
        game,
        make_answers(game, incorrect_item_id=wrong_id),
    )

    assert response.status_code == 200
    assert response.json()["correct_answers"] == 9
    assert response.json()["score_awarded"] == 90
    wrong_result = next(
        result
        for result in response.json()["results"]
        if result["item_id"] == wrong_id
    )
    assert wrong_result["is_correct"] is False
    assert wrong_result["explanation"]


def test_unknown_item_id_is_rejected(client):
    create_user(client)
    game = start_game(client)
    answers = make_answers(game)
    answers[0]["item_id"] = 999

    response = submit_game(client, game, answers)

    assert response.status_code == 422


def test_unsupported_category_is_rejected(client):
    create_user(client)
    game = start_game(client)
    answers = make_answers(game)
    answers[0]["selected_category"] = "compost"

    response = submit_game(client, game, answers)

    assert response.status_code == 422


def test_duplicate_item_submission_is_rejected(client):
    create_user(client)
    game = start_game(client)
    answers = make_answers(game)
    answers[-1]["item_id"] = answers[0]["item_id"]

    response = submit_game(client, game, answers)

    assert response.status_code == 422


def test_incomplete_submission_is_rejected(client):
    create_user(client)
    game = start_game(client)

    response = submit_game(client, game, make_answers(game)[:-1])

    assert response.status_code == 422


def test_unknown_user_cannot_start_game(client):
    response = client.post(
        "/api/v1/eco-sort/start",
        json={"email": "unknown@example.com"},
    )

    assert response.status_code == 404


def test_mismatched_email_is_rejected(client):
    create_user(client)
    create_user(client, email="other@example.com")
    game = start_game(client)

    response = submit_game(
        client,
        game,
        make_answers(game),
        email="other@example.com",
    )

    assert response.status_code == 403


def test_unknown_session_is_rejected(client):
    create_user(client)

    response = client.post(
        "/api/v1/eco-sort/submit",
        json={
            "email": "sorter@example.com",
            "session_token": "unknown-session-token-value",
            "answers": [
                {"item_id": 1, "selected_category": "wet"}
            ],
        },
    )

    assert response.status_code == 404


def test_repeated_submission_cannot_award_points_twice(client):
    create_user(client)
    game = start_game(client)
    answers = make_answers(game)

    first = submit_game(client, game, answers)
    second = submit_game(client, game, answers)

    assert first.status_code == 200
    assert second.status_code == 409
    assert first.json()["total_score"] == 100


def test_score_accumulates_with_existing_user_score(client):
    create_user(client, score=25)
    game = start_game(client)

    response = submit_game(client, game, make_answers(game))

    assert response.status_code == 200
    assert response.json()["total_score"] == 125


def test_failed_score_update_rolls_back_session_claim(client, monkeypatch):
    create_user(client)
    game = start_game(client)

    original_execute = SQLAlchemySession.execute

    def reject_user_score_update(self, statement, *args, **kwargs):
        if (
            isinstance(statement, Update)
            and getattr(statement.table, "name", None) == User.__tablename__
        ):
            return type("FailedUpdateResult", (), {"rowcount": 0})()
        return original_execute(self, statement, *args, **kwargs)

    monkeypatch.setattr(
        SQLAlchemySession,
        "execute",
        reject_user_score_update,
    )

    response = submit_game(client, game, make_answers(game))

    assert response.status_code == 404
    db_generator = client.app.dependency_overrides[get_db]()
    db = next(db_generator)
    try:
        session = (
            db.query(EcoSortGameSession)
            .filter(EcoSortGameSession.token == game["session_token"])
            .one()
        )
        assert session.submitted_at is None
        assert session.awarded_score == 0
    finally:
        db.close()
        db_generator.close()


def test_concurrent_submissions_award_points_at_most_once(client):
    create_user(client)
    game = start_game(client)
    answers = make_answers(game)

    def submit():
        return submit_game(client, game, answers)

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(executor.map(lambda _: submit(), range(2)))

    assert sum(response.status_code == 200 for response in responses) == 1
    assert all(response.status_code in {200, 409, 503} for response in responses)

    db_generator = client.app.dependency_overrides[get_db]()
    db = next(db_generator)
    try:
        user = db.query(User).filter(User.email == "sorter@example.com").one()
        session = (
            db.query(EcoSortGameSession)
            .filter(EcoSortGameSession.token == game["session_token"])
            .one()
        )
        assert user.score == 100
        assert session.awarded_score == 100
        assert session.submitted_at is not None
    finally:
        db.close()
        db_generator.close()


def test_existing_quiz_challenge_and_assistant_routes_remain_available(
    client,
    monkeypatch,
):
    async def mock_eco_response(message):
        return "Use reusable decorations."

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
