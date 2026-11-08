
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Quiz, User, QuizAttempt, QuizSession
from app.schemas.quiz import (
    AnswerResult,
    QuizQuestionResponse,
    QuizSubmitRequest,
    QuizSubmitResponse,
    QuizSessionStartRequest,
    QuizSessionStartResponse,
    QuizSessionSubmitRequest,
)
from app.services.ai_content_service import generate_quiz_content
from app.services.grok_service import GroqServiceError
from app.services.user_service import find_user_by_email, normalize_email

import random

router = APIRouter(
    prefix="/api/v1/quiz",
    tags=["Quiz"]
)


@router.get(
    "/questions",
    response_model=list[QuizQuestionResponse]
)
def get_quiz_questions(db: Session = Depends(get_db)):
    return (
        db.query(Quiz)
        .order_by(Quiz.id)
        .all()
    )


@router.post(
    "/session/start",
    response_model=QuizSessionStartResponse
)
async def start_quiz_session(
    request: QuizSessionStartRequest,
    db: Session = Depends(get_db)
):
    email = normalize_email(request.email)
    user = find_user_by_email(db, email)

    # Retrieve question IDs from previously completed sessions
    attempted_question_ids = set()

    if user:
        previous_sessions = (
            db.query(QuizSession.question_ids)
            .join(
                QuizAttempt,
                QuizAttempt.quiz_session_id == QuizSession.id
            )
            .filter(QuizAttempt.user_id == user.id)
            .all()
        )

        for session in previous_sessions:
            attempted_question_ids.update(session.question_ids)

    # Get questions that the user has not attempted
    all_questions = (
        db.query(Quiz)
        .order_by(Quiz.id)
        .all()
    )

    available_questions = [
        question
        for question in all_questions
        if question.id not in attempted_question_ids
    ]

    # Generate fresh questions if fewer than 10 are available
    if len(available_questions) < 10:
        try:
            generated_questions = await generate_quiz_content()

            existing_texts = {
                " ".join(question.question.casefold().split())
                for question in all_questions
            }

            for generated in generated_questions:
                normalized_text = " ".join(
                    generated.question.casefold().split()
                )

                if normalized_text in existing_texts:
                    continue

                new_question = Quiz(**generated.model_dump())

                db.add(new_question)
                existing_texts.add(normalized_text)

            db.flush()

            # Refresh available questions after generation
            all_questions = (
                db.query(Quiz)
                .order_by(Quiz.id)
                .all()
            )

            available_questions = [
                question
                for question in all_questions
                if question.id not in attempted_question_ids
            ]

        except GroqServiceError:
            # Continue with existing database questions as fallback
            pass

    # Never create an incomplete quiz session
    if len(available_questions) < 10:
        db.rollback()

        raise HTTPException(
            status_code=503,
            detail="Unable to prepare 10 fresh quiz questions right now. Please try again later."
        )

    # Select exactly 10 questions
    selected_questions = random.sample(
        available_questions,
        10
    )

    # Create a new quiz session with email binding
    session = QuizSession(
        email=email,
        question_ids=[
            question.id
            for question in selected_questions
        ]
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    return QuizSessionStartResponse(
        session_token=session.token,
        questions=[
            QuizQuestionResponse(
                id=question.id,
                question=question.question,
                options=question.options,
                category=question.category
            )
            for question in selected_questions
        ]
    )


@router.post(
    "/submit",
    response_model=QuizSubmitResponse
)

@router.post(
    "/session/submit",
    response_model=QuizSubmitResponse
)
def submit_quiz_session(
    request: QuizSessionSubmitRequest,
    db: Session = Depends(get_db)
):
    # Find the quiz session
    session = (
        db.query(QuizSession)
        .filter(QuizSession.token == request.session_token)
        .with_for_update()
        .first()
    )

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Quiz session not found"
        )

    # Verify session ownership
    email = normalize_email(request.email)
    if session.email is None or normalize_email(session.email) != email:
        raise HTTPException(
            status_code=403,
            detail="This quiz session does not belong to this email"
        )

    # Prevent duplicate submissions
    if session.submitted_at is not None:
        raise HTTPException(
            status_code=409,
            detail="This quiz session has already been submitted"
        )

    # Require exactly 10 answers
    if len(request.answers) != 10:
        raise HTTPException(
            status_code=422,
            detail="Exactly 10 answers are required"
        )

    submitted_question_ids = {
        answer.question_id for answer in request.answers
    }

    expected_question_ids = set(session.question_ids)

    # Verify exact question membership
    if submitted_question_ids != expected_question_ids:
        raise HTTPException(
            status_code=422,
            detail="Submitted questions do not match this quiz session"
        )

    questions = (
        db.query(Quiz)
        .filter(Quiz.id.in_(session.question_ids))
        .all()
    )

    question_map = {
        question.id: question for question in questions
    }

    if len(question_map) != 10:
        raise HTTPException(
            status_code=500,
            detail="Quiz session questions are unavailable"
        )

    results = []
    correct_count = 0

    for answer in request.answers:
        question = question_map[answer.question_id]

        if answer.selected_option >= len(question.options):
            raise HTTPException(
                status_code=422,
                detail=f"Invalid option for question {question.id}"
            )

        is_correct = (
            answer.selected_option == question.correct_answer
        )

        if is_correct:
            correct_count += 1

        results.append(
            AnswerResult(
                question_id=question.id,
                selected_option=answer.selected_option,
                correct_option=question.correct_answer,
                is_correct=is_correct,
                explanation=question.explanation
            )
        )

    total_questions = 10
    incorrect_count = total_questions - correct_count
    score = correct_count * 10

    # Find or create user
    user = find_user_by_email(db, email)

    if user:
        existing_username = (
            db.query(User)
            .filter(
                User.username == request.username,
                User.id != user.id
            )
            .first()
        )

        if existing_username:
            raise HTTPException(
                status_code=409,
                detail="Username is already taken"
            )

        user.username = request.username
        user.score += score

    else:
        existing_username = (
            db.query(User)
            .filter(User.username == request.username)
            .first()
        )

        if existing_username:
            raise HTTPException(
                status_code=409,
                detail="Username is already taken"
            )

        user = User(
            username=request.username,
            email=email,
            score=score
        )

        db.add(user)
        db.flush()

    # Save attempt and mark session submitted atomically
    attempt = QuizAttempt(
        user_id=user.id,
        quiz_session_id=session.id,
        total_questions=total_questions,
        correct_answers=correct_count,
        score=score
    )

    db.add(attempt)

    from datetime import datetime, timezone
    session.submitted_at = datetime.now(timezone.utc)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="This quiz session has already been submitted"
        )

    return QuizSubmitResponse(
        username=user.username,
        total_questions=total_questions,
        correct_answers=correct_count,
        incorrect_answers=incorrect_count,
        score=score,
        results=results
    )

def submit_quiz(
    request: QuizSubmitRequest,
    db: Session = Depends(get_db)
):
    email = normalize_email(request.email)
    question_ids = [
        answer.question_id for answer in request.answers
    ]

    questions = (
        db.query(Quiz)
        .filter(Quiz.id.in_(question_ids))
        .all()
    )

    question_map = {
        question.id: question for question in questions
    }

    if len(question_map) != len(question_ids):
        raise HTTPException(
            status_code=404,
            detail="One or more quiz questions were not found"
        )

    results = []
    correct_count = 0

    for answer in request.answers:
        question = question_map[answer.question_id]

        if answer.selected_option >= len(question.options):
            raise HTTPException(
                status_code=422,
                detail=f"Invalid option for question {question.id}"
            )

        is_correct = (
            answer.selected_option == question.correct_answer
        )

        if is_correct:
            correct_count += 1

        results.append(
            AnswerResult(
                question_id=question.id,
                selected_option=answer.selected_option,
                correct_option=question.correct_answer,
                is_correct=is_correct,
                explanation=question.explanation
            )
        )

    total_questions = len(request.answers)
    incorrect_count = total_questions - correct_count
    score = correct_count * 10

    user = find_user_by_email(db, email)

    if user:
        existing_attempt = (
            db.query(QuizAttempt)
            .filter(QuizAttempt.user_id == user.id)
            .first()
        )

        if existing_attempt:
            raise HTTPException(
                status_code=409,
                detail="You have already completed the quiz"
            )

        existing_username = (
            db.query(User)
            .filter(
                User.username == request.username,
                User.id != user.id
            )
            .first()
        )

        if existing_username:
            raise HTTPException(
                status_code=409,
                detail="Username is already taken"
            )

        user.username = request.username
        user.score += score

    else:
        existing_username = (
            db.query(User)
            .filter(User.username == request.username)
            .first()
        )

        if existing_username:
            raise HTTPException(
                status_code=409,
                detail="Username is already taken"
            )

        user = User(
            username=request.username,
            email=email,
            score=score
        )

        db.add(user)
        db.flush()

    attempt = QuizAttempt(
        user_id=user.id,
        total_questions=total_questions,
        correct_answers=correct_count,
        score=score
    )

    db.add(attempt)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="You have already completed the quiz"
        )

    return QuizSubmitResponse(
        username=user.username,
        total_questions=total_questions,
        correct_answers=correct_count,
        incorrect_answers=incorrect_count,
        score=score,
        results=results
    )
