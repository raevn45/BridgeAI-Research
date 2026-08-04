import logging
import os

from google import genai
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-2.0-flash"
]

UNAVAILABLE_MESSAGE = (
    "## BridgeAI is temporarily unavailable\n\n"
    "The AI service could not be reached right now. "
    "Please try again in a few moments."
)

_client = None


def get_client():
    """Return a cached Gemini client, or None if the API key is missing."""
    global _client

    if _client is not None:
        return _client

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY is not configured")
        return None

    try:
        _client = genai.Client(api_key=api_key)
    except Exception:
        logger.exception("Failed to initialize the Gemini client")
        return None

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
    if client is None:
        return UNAVAILABLE_MESSAGE

    for model in MODELS:
        try:
            response = client.models.generate_content(
                model=model,
                contents=contents
            )
            if response.text:
                return response.text
        except Exception:
            logger.exception("Model %s failed", model)

    return UNAVAILABLE_MESSAGE


def simplify_text(text, audience="General public"):
    """Simplifies passage or text input for a given target audience."""
    prompt = build_prompt(
        audience,
        "Simplify the information below.",
        information=text
    )
    return generate_ai_response(prompt)


def analyze_image(image, audience="General public"):
    """Analyzes and simplifies document image input."""
    prompt = build_prompt(
        audience,
        "Analyze this document image."
    )
    return generate_ai_response([prompt, image])
