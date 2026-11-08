
from contextlib import asynccontextmanager
import os
from urllib.parse import urlsplit

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database import Base, engine, SessionLocal
import app.models

from app.routes.quiz import router as quiz_router
from app.routes.leaderboard import router as leaderboard_router
from app.routes.challenges import router as challenges_router
from app.routes.ai import router as ai_router
from app.routes.eco_sort import router as eco_sort_router
from app.routes.green_score import router as green_score_router

from app.seed import seed_quiz_questions, seed_challenges


DEVELOPMENT_CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


def get_cors_origins() -> list[str]:
    environment = os.getenv(
        "APP_ENV", "development"
    ).strip().lower()

    if environment in {"development", "dev", "local"}:
        return DEVELOPMENT_CORS_ORIGINS.copy()

    configured_origins = os.getenv("CORS_ORIGINS", "")
    origins = []

    for configured_origin in configured_origins.split(","):
        origin = configured_origin.strip().rstrip("/")

        if not origin:
            continue

        parsed_origin = urlsplit(origin)

        try:
            parsed_origin.port

            invalid_origin = (
                origin == "*"
                or parsed_origin.scheme not in {"http", "https"}
                or not parsed_origin.hostname
                or "*" in parsed_origin.hostname
                or parsed_origin.username is not None
                or parsed_origin.password is not None
                or bool(parsed_origin.path)
                or bool(parsed_origin.query)
                or bool(parsed_origin.fragment)
            )

        except ValueError:
            invalid_origin = True

        if invalid_origin:
            raise ValueError(
                "CORS_ORIGINS must contain valid explicit origins"
            )

        origins.append(origin)

    origins = list(dict.fromkeys(origins))

    if not origins:
        raise RuntimeError(
            "CORS_ORIGINS is empty. Configure allowed frontend origins."
        )

    return origins


CORS_ORIGINS = get_cors_origins()

print(f"APP_ENV: {os.getenv('APP_ENV', 'development')}")
print(f"Resolved CORS origins: {CORS_ORIGINS}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        seed_quiz_questions(db)
        seed_challenges(db)
    finally:
        db.close()

    yield


app = FastAPI(
    title="GreenGlow AI API",
    description=(
        "AI-powered eco-friendly Diwali platform "
        "with sustainability challenges and interactive quizzes."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


app.include_router(quiz_router)
app.include_router(leaderboard_router)
app.include_router(challenges_router)
app.include_router(ai_router)
app.include_router(eco_sort_router)
app.include_router(green_score_router)


@app.get("/", tags=["Root"])
def root():
    return {
        "message": "Welcome to GreenGlow AI API",
        "status": "running",
    }


@app.get("/health", tags=["Health"])
def health_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "application": "GreenGlow AI",
            "database": "connected",
        }

    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "database": "disconnected",
            },
        )


# Wrap the complete application so CORS headers
# are also applied to error responses.
app = CORSMiddleware(
    app=app,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
