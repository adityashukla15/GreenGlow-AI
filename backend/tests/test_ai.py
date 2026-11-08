from app.services.grok_service import GroqServiceError


def test_assistant_returns_groq_response(client, monkeypatch):
    async def mock_generate_eco_response(message):
        assert "User question: Suggest eco-friendly Diwali decorations" in message
        assert "affordable" in message
        assert "near open flames" in message
        assert "pouring chemicals into drains" in message
        return "Try reusable fabric buntings and diya arrangements."

    monkeypatch.setattr(
        "app.routes.ai.generate_eco_response",
        mock_generate_eco_response,
    )

    response = client.post(
        "/api/v1/ai/assistant",
        json={"message": "Suggest eco-friendly Diwali decorations"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "reply": "Try reusable fabric buntings and diya arrangements.",
        "provider": "groq",
    }


def test_assistant_rejects_empty_message(client):
    response = client.post(
        "/api/v1/ai/assistant",
        json={"message": "   "},
    )

    assert response.status_code == 422


def test_assistant_rejects_invalid_payload(client):
    response = client.post(
        "/api/v1/ai/assistant",
        json={
            "message": "How can I celebrate sustainably?",
            "preferences": {"budget": 100},
        },
    )

    assert response.status_code == 422


def test_assistant_maps_groq_failure_to_safe_error(client, monkeypatch):
    async def fail_generate_eco_response(message):
        raise GroqServiceError("Internal details and secret")

    monkeypatch.setattr(
        "app.routes.ai.generate_eco_response",
        fail_generate_eco_response,
    )

    response = client.post(
        "/api/v1/ai/assistant",
        json={"message": "Suggest eco-friendly gifts"},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "The AI assistant is temporarily unavailable. Please try again later."
    )
    assert "secret" not in response.text


def test_assistant_handles_missing_groq_configuration(client, monkeypatch):
    monkeypatch.setattr("app.services.grok_service.GROQ_API_KEY", None)

    response = client.post(
        "/api/v1/ai/assistant",
        json={"message": "How can I reduce waste?"},
    )

    assert response.status_code == 503
    assert "API key" not in response.text


def test_assistant_includes_provided_personalization(client, monkeypatch):
    captured_prompts = []

    async def mock_generate_eco_response(message):
        captured_prompts.append(message)
        return "Make decorations from materials you already have."

    monkeypatch.setattr(
        "app.routes.ai.generate_eco_response",
        mock_generate_eco_response,
    )

    response = client.post(
        "/api/v1/ai/assistant",
        json={
            "message": "Suggest decorations",
            "preferences": {
                "budget": " low ",
                "interests": ["DIY decorations", " reusable items "],
                "decoration_interests": ["paper lanterns"],
                "celebration_style": "small family gathering",
            },
        },
    )

    assert response.status_code == 200
    assert len(captured_prompts) == 1
    assert "low" in captured_prompts[0]
    assert "DIY decorations" in captured_prompts[0]
    assert "reusable items" in captured_prompts[0]
    assert "paper lanterns" in captured_prompts[0]
    assert "small family gathering" in captured_prompts[0]


def test_existing_quiz_and_challenge_routes_remain_available(client):
    quiz_response = client.get("/api/v1/quiz/questions")
    challenge_response = client.get("/api/v1/challenges/")

    assert quiz_response.status_code == 200
    assert challenge_response.status_code == 200
