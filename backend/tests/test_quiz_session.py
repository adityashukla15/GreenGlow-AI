
from app.schemas.ai import GeneratedQuizQuestion
from app.services.grok_service import GroqServiceError


def make_questions():
    return [
        GeneratedQuizQuestion(
            question=f"Which action helps protect the environment in scenario {i}?",
            options=[
                "Use reusable items",
                "Burn plastic waste",
                "Waste electricity",
                "Dump waste in rivers",
            ],
            correct_answer=0,
            explanation="Reusable items help reduce unnecessary waste.",
            category="Sustainability",
        )
        for i in range(10)
    ]


def test_start_quiz_session_generates_and_returns_10_questions(
    client, monkeypatch
):
    async def mock_generate_quiz_content():
        return make_questions()

    monkeypatch.setattr(
        "app.routes.quiz.generate_quiz_content",
        mock_generate_quiz_content,
    )

    response = client.post(
        "/api/v1/quiz/session/start",
        json={"email": "test@example.com"},
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data["questions"]) == 10
    assert len(data["session_token"]) == 36
    assert len({q["id"] for q in data["questions"]}) == 10


def test_start_quiz_session_returns_503_when_generation_fails(
    client, monkeypatch
):
    async def mock_generate_quiz_content():
        raise GroqServiceError("Mock Groq failure")

    monkeypatch.setattr(
        "app.routes.quiz.generate_quiz_content",
        mock_generate_quiz_content,
    )

    response = client.post(
        "/api/v1/quiz/session/start",
        json={"email": "test@example.com"},
    )

    assert response.status_code == 503
    assert "Unable to prepare 10 fresh quiz questions" in response.json()["detail"]


def test_start_quiz_session_uses_existing_questions_without_groq(
    client, monkeypatch
):
    from app.database import get_db
    from app.main import app
    from app.models import Quiz

    def fail_if_called():
        raise AssertionError("Groq should not be called")

    monkeypatch.setattr(
        "app.routes.quiz.generate_quiz_content",
        fail_if_called,
    )

    db_generator = app.dependency_overrides[get_db]()
    db = next(db_generator)

    try:
        for i in range(10):
            db.add(
                Quiz(
                    question=f"Existing eco question number {i}?",
                    options=["A", "B", "C", "D"],
                    correct_answer=0,
                    explanation="Test explanation",
                    category="Environment",
                )
            )

        db.commit()
    finally:
        db.close()
        db_generator.close()

    response = client.post(
        "/api/v1/quiz/session/start",
        json={"email": "existing@example.com"},
    )

    assert response.status_code == 200
    assert len(response.json()["questions"]) == 10


def test_start_quiz_session_excludes_previously_attempted_questions(
    client, monkeypatch
):
    from app.database import get_db
    from app.main import app
    from app.models import Quiz, User, QuizSession, QuizAttempt

    def fail_if_called():
        raise AssertionError("Groq should not be called")

    monkeypatch.setattr(
        "app.routes.quiz.generate_quiz_content",
        fail_if_called,
    )

    db_generator = app.dependency_overrides[get_db]()
    db = next(db_generator)

    try:
        user = User(
            username="history_user",
            email="history@example.com",
            score=70,
        )
        db.add(user)

        questions = [
            Quiz(
                question=f"Eco question number {i}?",
                options=["Option A", "Option B", "Option C", "Option D"],
                correct_answer=0,
                explanation="Test explanation",
                category="Environment",
            )
            for i in range(20)
        ]
        db.add_all(questions)
        db.commit()

        previous_question_ids = [
            question.id for question in questions[:10]
        ]

        previous_session = QuizSession(
            question_ids=previous_question_ids
        )
        db.add(previous_session)
        db.commit()

        previous_attempt = QuizAttempt(
            user_id=user.id,
            quiz_session_id=previous_session.id,
            total_questions=10,
            correct_answers=7,
            score=70,
        )
        db.add(previous_attempt)
        db.commit()

    finally:
        db.close()
        db_generator.close()

    response = client.post(
        "/api/v1/quiz/session/start",
        json={"email": "history@example.com"},
    )

    assert response.status_code == 200

    returned_ids = {
        question["id"] for question in response.json()["questions"]
    }

    assert len(returned_ids) == 10
    assert returned_ids.isdisjoint(previous_question_ids)


def test_start_quiz_session_stores_email(
    client, monkeypatch
):
    from app.database import get_db
    from app.main import app
    from app.models import QuizSession

    async def mock_generate_quiz_content():
        return make_questions()

    monkeypatch.setattr(
        "app.routes.quiz.generate_quiz_content",
        mock_generate_quiz_content,
    )

    response = client.post(
        "/api/v1/quiz/session/start",
        json={"email": "  EMAILTEST@example.com  "},
    )

    assert response.status_code == 200

    session_token = response.json()["session_token"]

    db_generator = app.dependency_overrides[get_db]()
    db = next(db_generator)

    try:
        session = (
            db.query(QuizSession)
            .filter(QuizSession.token == session_token)
            .first()
        )

        assert session is not None
        assert session.email == "emailtest@example.com"

    finally:
        db.close()
        db_generator.close()


def test_submit_quiz_session_successfully(client, monkeypatch):
    from app.database import get_db
    from app.main import app
    from app.models import QuizAttempt, QuizSession, User

    async def mock_generate_quiz_content():
        return make_questions()

    monkeypatch.setattr(
        "app.routes.quiz.generate_quiz_content",
        mock_generate_quiz_content,
    )

    # Start a new quiz session
    start_response = client.post(
        "/api/v1/quiz/session/start",
        json={"email": "submit@example.com"},
    )

    assert start_response.status_code == 200

    session_data = start_response.json()
    session_token = session_data["session_token"]
    questions = session_data["questions"]

    # Select option 0 for all questions (correct in make_questions)
    answers = [
        {
            "question_id": question["id"],
            "selected_option": 0,
        }
        for question in questions
    ]

    # Submit the quiz
    submit_response = client.post(
        "/api/v1/quiz/session/submit",
        json={
            "session_token": session_token,
            "username": "submit_user",
            "email": "submit@example.com",
            "answers": answers,
        },
    )

    assert submit_response.status_code == 200

    data = submit_response.json()

    assert data["username"] == "submit_user"
    assert data["total_questions"] == 10
    assert data["correct_answers"] == 10
    assert data["incorrect_answers"] == 0
    assert data["score"] == 100
    assert len(data["results"]) == 10
    assert all(result["is_correct"] for result in data["results"])

    # Verify database records
    db_generator = app.dependency_overrides[get_db]()
    db = next(db_generator)

    try:
        user = (
            db.query(User)
            .filter(User.email == "submit@example.com")
            .first()
        )

        session = (
            db.query(QuizSession)
            .filter(QuizSession.token == session_token)
            .first()
        )

        attempt = (
            db.query(QuizAttempt)
            .filter(QuizAttempt.quiz_session_id == session.id)
            .first()
        )

        assert user is not None
        assert user.score == 100

        assert session is not None
        assert session.submitted_at is not None

        assert attempt is not None
        assert attempt.total_questions == 10
        assert attempt.correct_answers == 10
        assert attempt.score == 100

    finally:
        db.close()
        db_generator.close()


def test_quiz_and_challenges_find_legacy_noncanonical_email(client, monkeypatch):
    from app.database import get_db
    from app.main import app
    from app.models import Challenge, Quiz, QuizSession, User

    async def mock_generate_quiz_content():
        return make_questions()

    monkeypatch.setattr(
        "app.routes.quiz.generate_quiz_content",
        mock_generate_quiz_content,
    )

    db_generator = app.dependency_overrides[get_db]()
    db = next(db_generator)
    try:
        db.add(
            User(
                username="legacy_user",
                email="  MIXED@example.com ",
                score=5,
            )
        )
        db.add_all(
            [
                Quiz(
                    question=f"Existing eco question number {i}?",
                    options=["Option A", "Option B", "Option C", "Option D"],
                    correct_answer=0,
                    explanation="Test explanation",
                    category="Environment",
                )
                for i in range(10)
            ]
        )
        challenges = [
            Challenge(
                title=f"Legacy email challenge {i}",
                description=f"Complete challenge {i}.",
                points=10,
                is_active=True,
            )
            for i in range(4)
        ]
        db.add_all(challenges)
        db.commit()
        challenge_id = challenges[0].id
    finally:
        db.close()
        db_generator.close()

    start_response = client.post(
        "/api/v1/quiz/session/start",
        json={"email": " mixed@EXAMPLE.com "},
    )
    assert start_response.status_code == 200
    session = start_response.json()

    db_generator = app.dependency_overrides[get_db]()
    db = next(db_generator)
    try:
        quiz_session = (
            db.query(QuizSession)
            .filter_by(token=session["session_token"])
            .first()
        )
        quiz_session.email = " MIXED@Example.com "
        db.commit()
    finally:
        db.close()
        db_generator.close()

    submit_response = client.post(
        "/api/v1/quiz/session/submit",
        json={
            "session_token": session["session_token"],
            "username": "legacy_user",
            "email": "MIXED@example.com",
            "answers": [
                {"question_id": question["id"], "selected_option": 0}
                for question in session["questions"]
            ],
        },
    )
    assert submit_response.status_code == 200

    completion_response = client.get(
        "/api/v1/challenges/completions",
        params={"email": " mixed@EXAMPLE.com "},
    )
    assert completion_response.status_code == 200
    assert completion_response.json()["profile_exists"] is True
    assert completion_response.json()["completed_challenge_ids"] == []

    challenge_response = client.post(
        f"/api/v1/challenges/{challenge_id}/complete",
        json={"email": "MIXED@example.com"},
    )
    assert challenge_response.status_code == 200
    assert challenge_response.json()["total_score"] == 115

    duplicate_challenge_response = client.post(
        f"/api/v1/challenges/{challenge_id}/complete",
        json={"email": " mixed@example.com "},
    )
    assert duplicate_challenge_response.status_code == 409

    db_generator = app.dependency_overrides[get_db]()
    db = next(db_generator)
    try:
        matching_users = [
            user
            for user in db.query(User).all()
            if user.email.strip().lower() == "mixed@example.com"
        ]
        assert len(matching_users) == 1
        assert matching_users[0].score == 115
    finally:
        db.close()
        db_generator.close()


def test_submit_quiz_session_rejects_wrong_email(client, monkeypatch):
    async def mock_generate_quiz_content():
        return make_questions()

    monkeypatch.setattr(
        "app.routes.quiz.generate_quiz_content",
        mock_generate_quiz_content,
    )

    start_response = client.post(
        "/api/v1/quiz/session/start",
        json={"email": "owner@example.com"},
    )

    assert start_response.status_code == 200

    session_data = start_response.json()

    answers = [
        {
            "question_id": question["id"],
            "selected_option": 0,
        }
        for question in session_data["questions"]
    ]

    response = client.post(
        "/api/v1/quiz/session/submit",
        json={
            "session_token": session_data["session_token"],
            "username": "attacker",
            "email": "attacker@example.com",
            "answers": answers,
        },
    )

    assert response.status_code == 403
    assert "does not belong" in response.json()["detail"]

def test_submit_quiz_session_rejects_unknown_token(client):
    response = client.post(
        "/api/v1/quiz/session/submit",
        json={
            "session_token": "00000000-0000-0000-0000-000000000000",
            "username": "unknown_user",
            "email": "unknown@example.com",
            "answers": [
                {
                    "question_id": i,
                    "selected_option": 0,
                }
                for i in range(1, 11)
            ],
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Quiz session not found"


def test_submit_quiz_session_rejects_duplicate_submission(client, monkeypatch):
    from app.routes import quiz as quiz_routes

    async def fake_generate_quiz_content():
        return make_questions()

    monkeypatch.setattr(
        quiz_routes,
        "generate_quiz_content",
        fake_generate_quiz_content,
    )

    start_response = client.post(
        "/api/v1/quiz/session/start",
        json={"email": "duplicate@example.com"},
    )

    assert start_response.status_code == 200
    session_data = start_response.json()

    payload = {
        "session_token": session_data["session_token"],
        "username": "duplicate_user",
        "email": "duplicate@example.com",
        "answers": [
            {"question_id": question["id"], "selected_option": 0}
            for question in session_data["questions"]
        ],
    }

    first_response = client.post(
        "/api/v1/quiz/session/submit",
        json=payload,
    )

    assert first_response.status_code == 200

    second_response = client.post(
        "/api/v1/quiz/session/submit",
        json=payload,
    )

    assert second_response.status_code == 409
    assert second_response.json()["detail"] == (
        "This quiz session has already been submitted"
    )
def test_submit_quiz_session_rejects_unexpected_question_id(client, monkeypatch):
    from app.routes import quiz as quiz_routes

    async def fake_generate_quiz_content():
        return make_questions()

    monkeypatch.setattr(
        quiz_routes,
        "generate_quiz_content",
        fake_generate_quiz_content,
    )

    start_response = client.post(
        "/api/v1/quiz/session/start",
        json={"email": "unexpected@example.com"},
    )

    assert start_response.status_code == 200
    session_data = start_response.json()

    answers = [
        {"question_id": question["id"], "selected_option": 0}
        for question in session_data["questions"]
    ]

    # Replace one valid question ID with an unrelated ID.
    answers[0]["question_id"] = 999999

    response = client.post(
        "/api/v1/quiz/session/submit",
        json={
            "session_token": session_data["session_token"],
            "username": "unexpected_user",
            "email": "unexpected@example.com",
            "answers": answers,
        },
    )

    assert response.status_code == 422
    assert "do not match" in response.json()["detail"]
def test_submit_quiz_session_rejects_invalid_option_index(client, monkeypatch):
    from app.routes import quiz as quiz_routes

    async def fake_generate_quiz_content():
        return make_questions()

    monkeypatch.setattr(
        quiz_routes,
        "generate_quiz_content",
        fake_generate_quiz_content,
    )

    start_response = client.post(
        "/api/v1/quiz/session/start",
        json={"email": "invalid-option@example.com"},
    )

    assert start_response.status_code == 200
    session_data = start_response.json()

    answers = [
        {"question_id": question["id"], "selected_option": 0}
        for question in session_data["questions"]
    ]

    answers[0]["selected_option"] = 4

    response = client.post(
        "/api/v1/quiz/session/submit",
        json={
            "session_token": session_data["session_token"],
            "username": "invalid_option_user",
            "email": "invalid-option@example.com",
            "answers": answers,
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"].startswith("Invalid option for question")
def test_submit_quiz_session_rejects_incomplete_answers(client, monkeypatch):
    from app.routes import quiz as quiz_routes

    async def fake_generate_quiz_content():
        return make_questions()

    monkeypatch.setattr(
        quiz_routes,
        "generate_quiz_content",
        fake_generate_quiz_content,
    )

    start_response = client.post(
        "/api/v1/quiz/session/start",
        json={"email": "incomplete@example.com"},
    )

    assert start_response.status_code == 200
    session_data = start_response.json()

    answers = [
        {"question_id": question["id"], "selected_option": 0}
        for question in session_data["questions"][:9]
    ]

    response = client.post(
        "/api/v1/quiz/session/submit",
        json={
            "session_token": session_data["session_token"],
            "username": "incomplete_user",
            "email": "incomplete@example.com",
            "answers": answers,
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Exactly 10 answers are required"
def test_submit_quiz_session_rejects_session_without_email(client):
    from app.database import get_db
    from app.models import QuizSession

    db_generator = client.app.dependency_overrides[get_db]()
    db = next(db_generator)

    try:
        session = QuizSession(
            email=None,
            question_ids=list(range(1, 11)),
        )
        db.add(session)
        db.commit()
        session_token = session.token
    finally:
        db.close()
        db_generator.close()

    response = client.post(
        "/api/v1/quiz/session/submit",
        json={
            "session_token": session_token,
            "username": "legacy_user",
            "email": "legacy@example.com",
            "answers": [
                {"question_id": i, "selected_option": 0}
                for i in range(1, 11)
            ],
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
    "This quiz session does not belong to this email"
)

def test_same_user_can_submit_multiple_quiz_sessions(client, monkeypatch):
    from app.database import get_db
    from app.models import Quiz, User, QuizAttempt

    # Add 20 existing questions so both sessions can use
    # different sets of 10 without generating new questions.
    db_generator = client.app.dependency_overrides[get_db]()
    db = next(db_generator)

    try:
        for i in range(1, 21):
            db.add(
                Quiz(
                    question=f"Eco question number {i}?",
                    options=[
                        "Correct answer",
                        "Wrong answer 1",
                        "Wrong answer 2",
                        "Wrong answer 3",
                    ],
                    correct_answer=0,
                    explanation="This is the correct eco-friendly answer.",
                    category="Environment",
                )
            )

        db.commit()
    finally:
        db.close()
        db_generator.close()

    from app.routes import quiz as quiz_routes

    async def unexpected_generation():
        raise AssertionError("Groq should not be called")

    monkeypatch.setattr(
        quiz_routes,
        "generate_quiz_content",
        unexpected_generation,
    )

    email = "multiple@example.com"

    # First quiz session
    first_start = client.post(
        "/api/v1/quiz/session/start",
        json={"email": email},
    )

    assert first_start.status_code == 200
    first_data = first_start.json()

    first_ids = {
        question["id"] for question in first_data["questions"]
    }

    first_submit = client.post(
        "/api/v1/quiz/session/submit",
        json={
            "session_token": first_data["session_token"],
            "username": "multiple_user",
            "email": email,
            "answers": [
                {
                    "question_id": question["id"],
                    "selected_option": 0,
                }
                for question in first_data["questions"]
            ],
        },
    )

    assert first_submit.status_code == 200
    assert first_submit.json()["score"] == 100

    # Second quiz session for the same user
    second_start = client.post(
        "/api/v1/quiz/session/start",
        json={"email": email},
    )

    assert second_start.status_code == 200
    second_data = second_start.json()

    second_ids = {
        question["id"] for question in second_data["questions"]
    }

    assert len(second_ids) == 10
    assert first_ids.isdisjoint(second_ids)

    second_submit = client.post(
        "/api/v1/quiz/session/submit",
        json={
            "session_token": second_data["session_token"],
            "username": "multiple_user",
            "email": email,
            "answers": [
                {
                    "question_id": question["id"],
                    "selected_option": 0,
                }
                for question in second_data["questions"]
            ],
        },
    )

    assert second_submit.status_code == 200
    assert second_submit.json()["score"] == 100

    # Verify accumulated user score and attempt history.
    db_generator = client.app.dependency_overrides[get_db]()
    db = next(db_generator)

    try:
        user = db.query(User).filter(User.email == email).first()

        assert user is not None
        assert user.score == 200

        attempts = (
            db.query(QuizAttempt)
            .filter(QuizAttempt.user_id == user.id)
            .count()
        )

        assert attempts == 2
    finally:
        db.close()
        db_generator.close()