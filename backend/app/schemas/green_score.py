from datetime import datetime
from typing import Annotated, Literal

from fastapi import Query
from pydantic import BaseModel, ConfigDict, Field, field_validator


class GreenScoreQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=5, max_length=255)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        value = value.strip().lower()
        if "@" not in value or "." not in value.split("@")[-1]:
            raise ValueError("Invalid email address")

        return value


GreenScoreQueryParam = Annotated[GreenScoreQuery, Query()]


class GreenScoreBreakdown(BaseModel):
    quiz_points: int
    challenge_points: int
    eco_sort_points: int
    reconciliation_difference: int


class GreenScoreActivitySummary(BaseModel):
    completed_quizzes: int
    completed_challenges: int
    completed_eco_sort_games: int
    total_activities: int


class GreenScoreAchievement(BaseModel):
    id: str
    name: str
    description: str
    earned: bool
    progress: int
    target: int


class GreenScoreRecentActivity(BaseModel):
    activity_type: Literal["quiz", "challenge", "eco_sort"]
    points_earned: int
    completed_at: datetime
    description: str


class GreenScoreDashboard(BaseModel):
    total_points: int
    total_completed_activities: int
    achievement_count: int
    score_breakdown: GreenScoreBreakdown
    activity_summary: GreenScoreActivitySummary
    achievements: list[GreenScoreAchievement]
    recent_activity: list[GreenScoreRecentActivity]
