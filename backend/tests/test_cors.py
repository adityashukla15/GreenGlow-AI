from fastapi.testclient import TestClient

from app.main import app, get_cors_origins


client = TestClient(app)


def test_localhost_origin_is_allowed():
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == (
        "http://localhost:5173"
    )
    assert "access-control-allow-credentials" not in response.headers


def test_loopback_origin_is_allowed():
    response = client.options(
        "/health",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.headers["access-control-allow-origin"] == (
        "http://127.0.0.1:5173"
    )


def test_unapproved_origin_does_not_receive_allow_origin_header():
    response = client.get(
        "/",
        headers={"Origin": "https://unapproved.example"},
    )

    assert "access-control-allow-origin" not in response.headers


def test_root_and_health_endpoints_remain_functional():
    assert client.get("/").status_code == 200
    assert client.get("/health").status_code == 200


def test_production_origins_must_be_explicit(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv(
        "CORS_ORIGINS",
        "https://app.example.com, https://admin.example.com/",
    )

    assert get_cors_origins() == [
        "https://app.example.com",
        "https://admin.example.com",
    ]


def test_production_wildcard_origin_is_rejected(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("CORS_ORIGINS", "*")

    try:
        get_cors_origins()
    except ValueError as error:
        assert str(error) == "CORS_ORIGINS must contain valid explicit origins"
    else:
        raise AssertionError("Wildcard CORS origin must be rejected")


def test_production_wildcard_subdomain_is_rejected(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("CORS_ORIGINS", "https://*.example.com")

    try:
        get_cors_origins()
    except ValueError:
        pass
    else:
        raise AssertionError("Wildcard subdomain must be rejected")
