from fastapi import APIRouter, HTTPException

from app.schemas.ai import AssistantRequest, AssistantResponse
from app.services.grok_service import (
    GroqServiceError,
    generate_eco_response,
)


router = APIRouter(
    prefix="/api/v1/ai",
    tags=["AI"],
)


def build_assistant_prompt(request: AssistantRequest) -> str:
    prompt_parts = [
        "You are GreenGlow AI, a helpful eco-friendly Diwali assistant.",
        "Answer the user's question with practical, actionable suggestions. "
        "Prefer affordable and reusable options where relevant. "
        "Keep recommendations focused on eco-friendly Diwali and do not "
        "invent environmental certifications, statistics, or claims. "
        "Prioritize fire safety: never place fabric, paper, dry leaves, or "
        "other flammable decorations near open flames; recommend LED lights "
        "when a decoration could be exposed to heat or flame. Do not advise "
        "mixing household chemicals, pouring chemicals into drains or the "
        "environment, burning waste, or releasing balloons.",
    ]

    if request.preferences is not None:
        preferences = request.preferences.model_dump(exclude_none=True)
        if preferences:
            prompt_parts.append(f"User preferences: {preferences}")

    prompt_parts.append(f"User question: {request.message}")
    return "\n\n".join(prompt_parts)


@router.post("/assistant", response_model=AssistantResponse)
async def ask_assistant(request: AssistantRequest) -> AssistantResponse:
    try:
        reply = await generate_eco_response(
            build_assistant_prompt(request)
        )
    except GroqServiceError as exc:
        raise HTTPException(
            status_code=503,
            detail="The AI assistant is temporarily unavailable. Please try again later.",
        ) from exc

    return AssistantResponse(reply=reply)