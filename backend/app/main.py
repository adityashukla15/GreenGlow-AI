
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize registered database tables
    Base.metadata.create_all(bind=engine)

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
