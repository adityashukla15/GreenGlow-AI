
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database import Base, engine
import app.models
from app.routes.quiz import router as quiz_router
from app.routes.leaderboard import router as leaderboard_router
from app.routes.challenges import router as challenges_router
from app.routes.ai import router as ai_router
from app.routes.eco_sort import router as eco_sort_router
from app.routes.green_score import router as green_score_router
from app.seed import seed_quiz_questions, seed_challenges
from app.database import SessionLocal

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
    lifespan=lifespan
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
        "status": "running"
    }


@app.get("/health", tags=["Health"])
def health_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "application": "GreenGlow AI",
            "database": "connected"
        }

    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "database": "disconnected"
            }
        )
