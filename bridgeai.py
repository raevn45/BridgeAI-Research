import logging
import os

from google import genai
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

MODELS = [
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
]

_client = None


class AIServiceError(Exception):
    """Raised when the Gemini API cannot produce a usable response."""


class AIConfigurationError(AIServiceError):
    """Raised when the Gemini API is not configured correctly."""


def get_client():
    """Return a cached Gemini client, raising if it cannot be built."""
    global _client

    if _client is not None:
        return _client

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise AIConfigurationError(
            "GEMINI_API_KEY is not set; add it to your .env file."
        )

    try:
        _client = genai.Client(api_key=api_key)
    except Exception as exc:
        raise AIConfigurationError(
            f"Could not initialize the Gemini client: {exc}"
        ) from exc

    return _client


def build_prompt(audience, task, information=None):
    """Build the shared BridgeAI prompt for a task and target audience."""
    prompt = f"""
You are BridgeAI, an accessibility assistant.
{task}

Audience:
{audience}

Provide:

## Simple Explanation
Explain it clearly.

## Key Points
Important information in bullet points.

## Important Actions
What the user should do or remember.
"""

    if information is not None:
        prompt += f"\nInformation:\n{information}\n"

    return prompt


def generate_ai_response(contents):
    """Generate a response, falling back through the Gemini models."""
    client = get_client()

    last_error = None

    for model in MODELS:
        try:
            response = client.models.generate_content(model=model, contents=contents)
        except Exception as exc:
            last_error = exc
            logger.warning("Gemini model %s failed: %s", model, exc)
            continue

        if response.text:
            return response.text

        last_error = AIServiceError(f"Model {model} returned an empty response.")
        logger.warning("Gemini model %s returned an empty response.", model)

    raise AIServiceError(
        "All Gemini models failed to return a response."
    ) from last_error


def simplify_text(text, audience="General public"):
    """Simplifies passage or text input for a given target audience."""
    prompt = build_prompt(audience, "Simplify the information below.", information=text)
    return generate_ai_response(prompt)


def analyze_image(image, audience="General public"):
    """Analyzes and simplifies document image input."""
    prompt = build_prompt(audience, "Analyze this document image.")
    return generate_ai_response([prompt, image])
