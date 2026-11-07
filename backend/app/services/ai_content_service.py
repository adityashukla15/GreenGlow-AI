from pydantic import ValidationError

from app.schemas.ai import (
    GeneratedChallengeContent,
    GeneratedQuizContent,
)
from app.services.grok_service import (
    GroqServiceError,
    generate_structured_content,
)


async def generate_quiz_content():
    system_prompt = """
    You are GreenGlow AI, an educational eco-friendly Diwali quiz generator.

    Generate exactly 10 unique multiple-choice questions about:
    - Sustainable Diwali celebrations
    - Air and noise pollution awareness
    - Waste management and recycling
    - Energy conservation
    - Sustainable decorations and gifting
    - Animal welfare

    Requirements:
    - Every question must have exactly 4 unique options.
    - correct_answer must be the zero-based index of the correct option.
    - Every question must have a clear, factually correct explanation.
    - Avoid misleading claims and invented environmental statistics.
    - Avoid duplicate or nearly identical questions.
    - Use simple, beginner-friendly English.
    - Return only a valid JSON object matching this structure:

    {
      "questions": [
        {
          "question": "Question text",
          "options": ["Option A", "Option B", "Option C", "Option D"],
          "correct_answer": 0,
          "explanation": "Explanation",
          "category": "Category"
        }
      ]
    }
    """

    try:
        content = await generate_structured_content(
            system_prompt=system_prompt,
            user_prompt="Generate a fresh set of 10 eco-friendly Diwali quiz questions."
        )

        validated = GeneratedQuizContent.model_validate(content)

        return validated.questions

    except ValidationError as exc:
        raise GroqServiceError(
            "Groq generated invalid quiz content."
        ) from exc


async def generate_challenge_content():
    system_prompt = """
    You are GreenGlow AI, an eco-friendly Diwali challenge generator.

    Generate between 3 and 5 unique, practical sustainability challenges.

    Requirements:
    - Challenges must be safe, realistic and actionable.
    - Focus on waste reduction, energy conservation, reusable items,
      sustainable gifting, composting and environmental awareness.
    - Each challenge must have a concise title and clear description.
    - Avoid duplicate or nearly identical challenges.
    - Do not generate points or scores. The backend assigns points.
    - Return only a valid JSON object matching this structure:

    {
      "challenges": [
        {
          "title": "Challenge title",
          "description": "Challenge description"
        }
      ]
    }
    """

    try:
        content = await generate_structured_content(
            system_prompt=system_prompt,
            user_prompt="Generate fresh and practical eco-friendly Diwali challenges."
        )

        validated = GeneratedChallengeContent.model_validate(content)

        return validated.challenges

    except ValidationError as exc:
        raise GroqServiceError(
            "Groq generated invalid challenge content."
        ) from exc