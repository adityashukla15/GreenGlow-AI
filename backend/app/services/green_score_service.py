from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import (
    Challenge,
    ChallengeCompletion,
    EcoSortGameSession,
    QuizAttempt,
    User,
)
from app.schemas.green_score import (
    GreenScoreAchievement,
    GreenScoreActivitySummary,
    GreenScoreBreakdown,
    GreenScoreDashboard,
    GreenScoreRecentActivity,
)


RECENT_ACTIVITY_LIMIT = 10


@dataclass(frozen=True)
class AchievementDefinition:
    id: str
    name: str
    description: str
    target: int
    progress_key: str


ACHIEVEMENTS = (
    AchievementDefinition(
        id="eco-beginner",
        name="Eco Beginner",
        description="Earn 50 total points.",
        target=50,
        progress_key="total_points",
    ),
    AchievementDefinition(
        id="green-explorer",
        name="Green Explorer",
        description="Complete 3 quizzes.",
        target=3,
        progress_key="completed_quizzes",
    ),
    AchievementDefinition(
        id="challenge-starter",
        name="Challenge Starter",
        description="Complete 1 challenge.",
        target=1,
        progress_key="completed_challenges",
    ),
    AchievementDefinition(
        id="eco-sort-learner",
        name="Eco Sort Learner",
        description="Complete 1 Eco Sort game.",
        target=1,
        progress_key="completed_eco_sort_games",
    ),
    AchievementDefinition(
        id="green-champion",
        name="Green Champion",
        description="Earn 200 total points.",
        target=200,
        progress_key="total_points",
    ),
    AchievementDefinition(
        id="eco-champion",
        name="Eco Champion",
        description="Complete 10 activities.",
        target=10,
        progress_key="total_activities",
    ),
)


class GreenScoreUserNotFoundError(Exception):
    """Raised when a dashboard is requested for an unknown email."""


def _utc_sort_value(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def _build_achievements(
    total_points: int,
    summary: GreenScoreActivitySummary,
) -> list[GreenScoreAchievement]:
    progress_values = {
        "total_points": total_points,
        "completed_quizzes": summary.completed_quizzes,
        "completed_challenges": summary.completed_challenges,
        "completed_eco_sort_games": summary.completed_eco_sort_games,
        "total_activities": summary.total_activities,
    }

    return [
        GreenScoreAchievement(
            id=definition.id,
            name=definition.name,
            description=definition.description,
            earned=progress_values[definition.progress_key] >= definition.target,
            progress=min(
                progress_values[definition.progress_key],
                definition.target,
            ),
            target=definition.target,
        )
        for definition in ACHIEVEMENTS
    ]


def _get_recent_activity(
    db: Session,
    user_id: int,
) -> list[GreenScoreRecentActivity]:
    activities: list[tuple[datetime, int, int, GreenScoreRecentActivity]] = []

    quiz_attempts = (
        db.query(QuizAttempt)
        .filter(QuizAttempt.user_id == user_id)
        .order_by(QuizAttempt.created_at.desc(), QuizAttempt.id.desc())
        .limit(RECENT_ACTIVITY_LIMIT)
        .all()
    )
    for attempt in quiz_attempts:
        activities.append(
            (
                _utc_sort_value(attempt.created_at),
                0,
                attempt.id,
                GreenScoreRecentActivity(
                    activity_type="quiz",
                    points_earned=attempt.score,
                    completed_at=attempt.created_at,
                    description=(
                        f"Completed a quiz with {attempt.correct_answers} "
                        f"of {attempt.total_questions} correct."
                    ),
                ),
            )
        )

    challenge_completions = (
        db.query(ChallengeCompletion, Challenge.title)
        .join(Challenge, Challenge.id == ChallengeCompletion.challenge_id)
        .filter(ChallengeCompletion.user_id == user_id)
        .order_by(
            ChallengeCompletion.completed_at.desc(),
            ChallengeCompletion.id.desc(),
        )
        .limit(RECENT_ACTIVITY_LIMIT)
        .all()
    )
    for completion, title in challenge_completions:
        activities.append(
            (
                _utc_sort_value(completion.completed_at),
                1,
                completion.id,
                GreenScoreRecentActivity(
                    activity_type="challenge",
                    points_earned=completion.points_awarded,
                    completed_at=completion.completed_at,
                    description=f"Completed challenge: {title}.",
                ),
            )
        )

    eco_sort_sessions = (
        db.query(EcoSortGameSession)
        .filter(
            EcoSortGameSession.user_id == user_id,
            EcoSortGameSession.submitted_at.is_not(None),
        )
        .order_by(
            EcoSortGameSession.submitted_at.desc(),
            EcoSortGameSession.id.desc(),
        )
        .limit(RECENT_ACTIVITY_LIMIT)
        .all()
    )
    for game in eco_sort_sessions:
        activities.append(
            (
                _utc_sort_value(game.submitted_at),
                2,
                game.id,
                GreenScoreRecentActivity(
                    activity_type="eco_sort",
                    points_earned=game.awarded_score,
                    completed_at=game.submitted_at,
                    description="Completed an Eco Sort game.",
                ),
            )
        )

    activities.sort(key=lambda activity: activity[:3], reverse=True)
    return [activity[3] for activity in activities[:RECENT_ACTIVITY_LIMIT]]


def get_green_score_dashboard(db: Session, email: str) -> GreenScoreDashboard:
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise GreenScoreUserNotFoundError

    quiz_count, quiz_points = (
        db.query(
            func.count(QuizAttempt.id),
            func.coalesce(func.sum(QuizAttempt.score), 0),
        )
        .filter(QuizAttempt.user_id == user.id)
        .one()
    )

    challenge_count, challenge_points = (
        db.query(
            func.count(ChallengeCompletion.id),
            func.coalesce(func.sum(ChallengeCompletion.points_awarded), 0),
        )
        .filter(ChallengeCompletion.user_id == user.id)
        .one()
    )

    eco_sort_count, eco_sort_points = (
        db.query(
            func.count(EcoSortGameSession.id),
            func.coalesce(func.sum(EcoSortGameSession.awarded_score), 0),
        )
        .filter(
            EcoSortGameSession.user_id == user.id,
            EcoSortGameSession.submitted_at.is_not(None),
        )
        .one()
    )

    total_activities = quiz_count + challenge_count + eco_sort_count
    summary = GreenScoreActivitySummary(
        completed_quizzes=quiz_count,
        completed_challenges=challenge_count,
        completed_eco_sort_games=eco_sort_count,
        total_activities=total_activities,
    )
    total_points = user.score
    recorded_activity_points = quiz_points + challenge_points + eco_sort_points

    achievements = _build_achievements(total_points, summary)

    return GreenScoreDashboard(
        total_points=total_points,
        total_completed_activities=total_activities,
        achievement_count=sum(achievement.earned for achievement in achievements),
        score_breakdown=GreenScoreBreakdown(
            quiz_points=quiz_points,
            challenge_points=challenge_points,
            eco_sort_points=eco_sort_points,
            reconciliation_difference=total_points - recorded_activity_points,
        ),
        activity_summary=summary,
        achievements=achievements,
        recent_activity=_get_recent_activity(db, user.id),
    )
