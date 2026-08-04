import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def generate_ai_response(contents):
    """Fallback handler through Gemini models."""
    models = [
        "gemini-3.5-flash",
        "gemini-3.5-flash-lite",
        "gemini-2.5-flash"
    ]

    for model in models:
        try:
            response = client.models.generate_content(
                model=model,
                contents=contents
            )
            return response.text
        except Exception as e:
            print(f"{model} failed:", e)

    return """
## BridgeAI is temporarily unavailable

The AI service is currently experiencing high traffic. Please try again in a few moments.
"""


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