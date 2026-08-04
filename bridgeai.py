import logging
import os

from google import genai
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

MODELS = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"]


class AIServiceError(Exception):
    """Raised when the Gemini API cannot produce a usable response."""


class AIConfigurationError(AIServiceError):
    """Raised when the Gemini API is not configured correctly."""


def get_client():
    """Build a Gemini client, raising AIConfigurationError if unusable."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise AIConfigurationError(
            "GEMINI_API_KEY is not set; add it to your .env file."
        )

    try:
        return genai.Client(api_key=api_key)
    except Exception as exc:
        raise AIConfigurationError(
            f"Could not initialize the Gemini client: {exc}"
        ) from exc


def generate_ai_response(contents):
    """Call Gemini, falling back through models, raising on total failure."""
    client = get_client()

    last_error = None

    for model in MODELS:
        try:
            response = client.models.generate_content(
                model=model,
                contents=contents
            )
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
    prompt = f"""
You are BridgeAI, an accessibility assistant.
Simplify the information below.

Audience:
{audience}

Provide:

## Simple Explanation
Explain it clearly.

## Key Points
Important information in bullet points.

## Important Actions
What the user should do or remember.

Information:
{text}
"""
    return generate_ai_response(prompt)


def analyze_image(image, audience="General public"):
    """Analyzes and simplifies document image input."""
    prompt = f"""
You are BridgeAI, an accessibility assistant.
Analyze this document image.

Audience:
{audience}

Provide:

## Simple Explanation
## Key Points
## Important Actions
"""
    return generate_ai_response([prompt, image])
