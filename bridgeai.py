import logging
import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

logger = logging.getLogger(__name__)

UNAVAILABLE_MESSAGE = (
    "## BridgeAI is temporarily unavailable\n\n"
    "The AI service could not be reached right now. "
    "Please try again in a few moments."
)

MODELS = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"]


def get_client():
    """Create a Gemini client, or None when no API key is configured."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY is not configured")
        return None

    try:
        return genai.Client(api_key=api_key)
    except Exception:
        logger.exception("Failed to initialize the Gemini client")
        return None


def generate_ai_response(contents):
    """Fallback handler through Gemini models."""
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
