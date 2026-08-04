import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def generate_ai_response(contents):
    """Fallback handler through Gemini models."""
    import os
    from google import genai
    
    # Grab key explicitly from environment
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "## BridgeAI Error\n\n`GEMINI_API_KEY` is missing in your .env file."

    # Pass api_key directly to Client initialization
    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        print("Client init error:", e)
        return f"## BridgeAI Error\n\nCould not initialize API client: {e}"

    models = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"]

    for model in models:
        try:
            response = client.models.generate_content(
                model=model,
                contents=contents
            )
            if response.text:
                return response.text
        except Exception as e:
            print(f"[{model}] failed:", e)

    return "## BridgeAI Error\n\nAll AI models timed out or failed to respond. Please try again."
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
