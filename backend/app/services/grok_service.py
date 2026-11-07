
import os

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

        if not answer:
            raise GroqServiceError(
                "Groq returned an empty response."
            )

        return answer.strip()

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