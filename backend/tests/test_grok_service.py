import asyncio

import httpx
import pytest

from app.services import grok_service
from app.services.grok_service import GroqServiceError


class MockGroqResponse:
    def __init__(self, content=None, status_code=200, payload=None):
        self.content = content
        self.status_code = status_code
        self.payload = payload

    def raise_for_status(self):
        if self.status_code >= 400:
            request = httpx.Request("POST", grok_service.GROQ_API_URL)
            response = httpx.Response(self.status_code, request=request)
            raise httpx.HTTPStatusError(
                "Provider details must not escape.",
                request=request,
                response=response,
            )

    def json(self):
        if self.payload is not None:
            return self.payload
        return {
            "choices": [
                {"message": {"content": self.content}}
            ]
        }


class MockGroqClient:
    response = None
    error = None

    def __init__(self, timeout):
        self.timeout = timeout

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        return None

    async def post(self, *_args, **_kwargs):
        if self.error is not None:
            raise self.error
        return self.response


def patch_groq_client(
    monkeypatch,
    *,
    content=None,
    status_code=200,
    error=None,
    payload=None,
):
    MockGroqClient.response = MockGroqResponse(
        content,
        status_code,
        payload,
    )
    MockGroqClient.error = error
    monkeypatch.setattr(grok_service, "GROQ_API_KEY", "test-key-not-real")
    monkeypatch.setattr(grok_service.httpx, "AsyncClient", MockGroqClient)


@pytest.mark.parametrize(
    "content",
    [
        "Put a strip of cloth next to the diya flame.",
        "Pour leftover paint down the kitchen drain.",
        "Burn plastic packaging to get rid of it.",
        "Release balloons outdoors after the celebration.",
    ],
)
def test_rejects_unsafe_environmental_advice(monkeypatch, content):
    patch_groq_client(monkeypatch, content=content)

    with pytest.raises(GroqServiceError, match="safety checks"):
        asyncio.run(
            grok_service.generate_eco_response("Give me an eco-friendly tip.")
        )


@pytest.mark.parametrize(
    "content",
    [
        "Never place fabric near an open flame. Use LED lights instead.",
        "Do not pour paint down the drain; take it to a local collection site.",
        "Avoid burning plastic packaging.",
    ],
)
def test_allows_clear_safety_warnings(monkeypatch, content):
    patch_groq_client(monkeypatch, content=content)

    assert asyncio.run(
        grok_service.generate_eco_response("How should I stay safe?")
    ) == content


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"choices": []},
        {"choices": [{"message": {"content": None}}]},
        {"choices": [{"message": {"content": 42}}]},
        {"choices": [{"message": {"content": "   "}}]},
    ],
)
def test_rejects_malformed_or_empty_provider_responses(monkeypatch, payload):
    patch_groq_client(monkeypatch, payload=payload)

    with pytest.raises(GroqServiceError):
        asyncio.run(
            grok_service.generate_eco_response("Give me one practical tip.")
        )


def test_provider_timeout_is_handled(monkeypatch):
    patch_groq_client(monkeypatch, error=httpx.TimeoutException("provider timeout"))

    with pytest.raises(GroqServiceError, match="timed out"):
        asyncio.run(
            grok_service.generate_eco_response("Give me one practical tip.")
        )


def test_provider_error_does_not_expose_provider_details(monkeypatch):
    patch_groq_client(monkeypatch, status_code=500)

    with pytest.raises(GroqServiceError) as error:
        asyncio.run(
            grok_service.generate_eco_response("Give me one practical tip.")
        )

    assert "Provider details must not escape" not in str(error.value)
