
import os
import re

import httpx
from dotenv import load_dotenv
import json

load_dotenv()

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "llama-3.3-70b-versatile"
)


class GroqServiceError(Exception):
    """Raised when the Groq API request fails."""


UNSAFE_ADVICE_PATTERNS = (
    re.compile(
        r"\b(?:fabric|cloth|paper|dry leaves|flammable decorations?)\b"
        r".{0,60}\b(?:near|next to|beside|around|over|on)\b.{0,40}"
        r"\b(?:open flames?|candles?|diyas?|lamps?|fire)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:wrap|cover|line|decorate)\b.{0,50}"
        r"\b(?:diyas?|candles?|lamps?|flames?)\b.{0,50}"
        r"\b(?:fabric|cloth|paper|dry leaves|flammable)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:pour|dump|flush|rinse|dispose of)\b.{0,70}"
        r"\b(?:chemicals?|paint|oil|solvents?|pesticides?|cleaners?|"
        r"batter(?:y|ies)|bleach|ammonia|e-waste)\b.{0,60}"
        r"\b(?:drain|sink|toilet|river|water|soil|garden|regular trash|"
        r"household waste)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:mix|combine)\b.{0,40}\b(?:bleach|ammonia)\b"
        r".{0,40}\b(?:bleach|ammonia)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:burn|incinerate)\b.{0,50}"
        r"\b(?:plastic|trash|waste|leaves|packaging|batter(?:y|ies))\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:release|let go of)\b.{0,30}\bballoons?\b"
        r"|\bcut down\b.{0,30}\btrees?\b"
        r"|\bdump\b.{0,40}\b(?:oil|chemicals?|waste)\b.{0,40}\b"
        r"(?:river|lake|ocean|waterway|soil)\b",
        re.IGNORECASE,
    ),
)


def validate_eco_response(answer: object) -> str:
    if not isinstance(answer, str) or not answer.strip():
        raise GroqServiceError("Groq returned an invalid response.")

    for sentence in re.split(r"(?<=[.!?])\s+", answer):
        for pattern in UNSAFE_ADVICE_PATTERNS:
            match = pattern.search(sentence)
            if match is None:
                continue

            preceding_text = sentence[max(0, match.start() - 48):match.start()]
            if re.search(
                r"\b(?:no|not|never|avoid|don't|do not)\b"
                r"(?:\s+\w+){0,5}\s*$",
                preceding_text,
                re.I,
            ):
                continue

            raise GroqServiceError(
                "Groq returned advice that did not pass safety checks."
            )

    return answer.strip()


async def generate_eco_response(message: str) -> str:
    """
    Generate an eco-friendly Diwali response using Groq.
    """

    if not GROQ_API_KEY:
        raise GroqServiceError(
            "Groq API key is not configured."
        )

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are GreenGlow AI, a friendly sustainability "
                    "assistant. Help users celebrate an eco-friendly "
                    "Diwali. Suggest practical ways to reduce pollution, "
                    "avoid plastic, manage waste, save electricity, "
                    "and choose sustainable decorations. "
                    "Keep answers clear, friendly, and practical. "
                    "Never invent environmental statistics."
                )
            },
            {
                "role": "user",
                "content": message
            }
        ],
        "temperature": 0.7,
        "max_completion_tokens": 500
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                GROQ_API_URL,
                headers=headers,
                json=payload
            )

            response.raise_for_status()

        result = response.json()

        answer = result["choices"][0]["message"]["content"]
        return validate_eco_response(answer)

    except httpx.TimeoutException as exc:
        raise GroqServiceError(
            "Groq API request timed out."
        ) from exc

    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 429:
            message = "Groq rate limit reached. Please try again later."
        else:
            message = (
                f"Groq API request failed with status "
                f"{exc.response.status_code}."
            )

        raise GroqServiceError(message) from exc

    except httpx.RequestError as exc:
        raise GroqServiceError(
            "Unable to connect to Groq API."
        ) from exc

    except (KeyError, IndexError, TypeError, ValueError, AttributeError) as exc:
        raise GroqServiceError(
            "Invalid response received from Groq."
        ) from exc
async def generate_structured_content(
    system_prompt: str,
    user_prompt: str
) -> dict:
    """
    Generate structured JSON content using Groq.
    """

    if not GROQ_API_KEY:
        raise GroqServiceError(
            "Groq API key is not configured."
        )

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        "temperature": 0.7,
        "max_completion_tokens": 4000,
        "response_format": {
            "type": "json_object"
        }
    }

    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.post(
                GROQ_API_URL,
                headers=headers,
                json=payload
            )

            response.raise_for_status()

        result = response.json()
        content = result["choices"][0]["message"]["content"]

        if not content:
            raise GroqServiceError(
                "Groq returned an empty response."
            )

        parsed_content = json.loads(content)

        if not isinstance(parsed_content, dict):
            raise GroqServiceError(
                "Groq returned an invalid JSON object."
            )

        return parsed_content

    except httpx.TimeoutException as exc:
        raise GroqServiceError(
            "Groq API request timed out."
        ) from exc

    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 429:
            message = "Groq rate limit reached. Please try again later."
        else:
            message = (
                f"Groq API request failed with status "
                f"{exc.response.status_code}."
            )

        raise GroqServiceError(message) from exc

    except httpx.RequestError as exc:
        raise GroqServiceError(
            "Unable to connect to Groq API."
        ) from exc

    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise GroqServiceError(
            "Invalid structured response received from Groq."
        ) from exc