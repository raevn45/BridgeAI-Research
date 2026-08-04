import html
import logging
import os
import random
import secrets

import markdown

from PIL import Image
from pypdf import PdfReader

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session
)

from dotenv import load_dotenv

from bridgeai import (
    AIServiceError,
    simplify_text,
    analyze_image
)

from passages import (
    PASSAGES,
    get_passage
)

import database

load_dotenv()

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_TEXT_LENGTH = 20000
MAX_NAME_LENGTH = 100
MAX_FEEDBACK_LENGTH = 2000
MAX_PDF_PAGES = 50
MAX_AGE = 120
ALLOWED_AUDIENCES = {
    "General public",
    "Student",
    "Patient",
    "Elderly person",
}
DEFAULT_AUDIENCE = "General public"
PDF_EXTENSIONS = (".pdf",)
IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg")

app = Flask(__name__)

secret_key = os.getenv("SECRET_KEY")
if not secret_key:
    secret_key = secrets.token_hex(32)
app.secret_key = secret_key

app.config.update(
    MAX_CONTENT_LENGTH=MAX_UPLOAD_BYTES,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.getenv("SESSION_COOKIE_SECURE", "1") == "1",
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if not os.getenv("SECRET_KEY"):
    logger.warning(
        "SECRET_KEY is not set; using an ephemeral key. "
        "Sessions will be invalidated on restart."
    )

database.init_db()

AI_UNAVAILABLE_MESSAGE = (
    "<p>BridgeAI could not generate a simplification right now. "
    "Please try again in a few moments.</p>"
)


# ==========================================
# SHARED HELPERS
# ==========================================

def current_passage():
    """Return the passage assigned to the current session."""
    return get_passage(session["passage_id"])


def render_markdown(text):
    """Render untrusted markdown without letting raw HTML through."""
    return markdown.markdown(html.escape(text))


def parse_int(value, default, minimum=None, maximum=None):
    """Parse a form value as an int, falling back to a clamped default."""
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        logger.info("Ignoring non-numeric form value %r", value)
        return default

    if minimum is not None:
        parsed = max(minimum, parsed)
    if maximum is not None:
        parsed = min(maximum, parsed)

    return parsed


def clean_audience(value):
    """Restrict the audience to the values offered by the form."""
    return value if value in ALLOWED_AUDIENCES else DEFAULT_AUDIENCE


def extract_pdf_text(uploaded_file):
    """Extract text from an uploaded PDF, or None when it cannot be read."""
    try:
        reader = PdfReader(uploaded_file)
        pdf_text = ""
        for page in reader.pages[:MAX_PDF_PAGES]:
            pdf_text += page.extract_text() or ""
    except Exception:
        logger.exception("Failed to extract text from uploaded PDF")
        return None

    return pdf_text


def load_image(uploaded_file):
    """Open an uploaded image, or None when it is not a valid image."""
    try:
        return Image.open(uploaded_file)
    except Exception:
        logger.exception("Failed to open uploaded image")
        return None


def score_quiz(questions, form):
    """Count how many submitted answers match the correct option index."""
    score = 0

    for index, question in enumerate(questions, start=1):
        answer = parse_int(form.get(f"q{index}"), None)
        if answer is not None and answer == question["answer"]:
            score += 1

    return score


def run_quiz_step(quiz_number, confidence_key, next_endpoint):
    """Handle one comprehension quiz: score it, store it, move on."""
    if "passage_id" not in session:
        return redirect(url_for("study_consent"))

    passage = current_passage()
    questions = passage.get(f"quiz{quiz_number}_questions", [])

    if request.method == "POST":
        session[f"quiz{quiz_number}_score"] = score_quiz(
            questions,
            request.form
        )
        session[confidence_key] = parse_int(
            request.form.get("confidence"), 3, minimum=1, maximum=5
        )

        return redirect(url_for(next_endpoint))

    return render_template(
        f"quiz{quiz_number}.html",
        passage=passage,
        questions=questions
    )


# ==========================================
# BRIDGEAI PUBLIC TOOL
# ==========================================

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/app", methods=["GET", "POST"])
def bridge_app():

    result = ""

    if request.method == "POST":

        text = request.form.get("text", "")[:MAX_TEXT_LENGTH]
        audience = clean_audience(
            request.form.get("audience", DEFAULT_AUDIENCE)
        )
        uploaded_file = request.files.get("file")

        content = ""

        # TEXT INPUT
        if text.strip():
            content += text

        # FILE INPUT
        if uploaded_file and uploaded_file.filename:

            filename = uploaded_file.filename.lower()

            # PDF PROCESSING
            if filename.endswith(PDF_EXTENSIONS):
                pdf_text = extract_pdf_text(uploaded_file)
                if pdf_text is None:
                    return render_template(
                        "index.html",
                        result="<p>That PDF could not be read. "
                               "Please try a different file.</p>"
                    )
                content += "\n\n" + pdf_text

            # IMAGE PROCESSING
            elif filename.endswith(IMAGE_EXTENSIONS):
                image = load_image(uploaded_file)
                if image is None:
                    return render_template(
                        "index.html",
                        result="<p>That image could not be read. "
                               "Please try a different file.</p>"
                    )

                try:
                    ai_text = analyze_image(image, audience)
                except AIServiceError:
                    logger.exception("Image analysis failed")
                    return render_template(
                        "index.html",
                        result=AI_UNAVAILABLE_MESSAGE
                    )

                return render_template(
                    "index.html",
                    result=render_markdown(ai_text)
                )

            # UNSUPPORTED FILE TYPE
            else:
                return render_template(
                    "index.html",
                    result="<p>Unsupported file type. "
                           "Please upload a PDF, PNG, or JPG file.</p>"
                )

        if not content.strip():
            result = "<p>Please upload a PDF, image, or paste text first.</p>"
        else:
            try:
                ai_text = simplify_text(content[:MAX_TEXT_LENGTH], audience)
            except AIServiceError:
                logger.exception("Text simplification failed")
                return render_template(
                    "index.html",
                    result=AI_UNAVAILABLE_MESSAGE
                )
            result = render_markdown(ai_text)

    return render_template("index.html", result=result)


# ==========================================
# RESEARCH STUDY FLOW
# ==========================================

@app.route("/research", methods=["GET", "POST"])
@app.route("/study/consent", methods=["GET", "POST"])
def study_consent():

    if request.method == "POST":

        first_name = request.form.get("first_name", "").strip()
        session["first_name"] = first_name[:MAX_NAME_LENGTH] or "Anonymous"
        session["age"] = parse_int(
            request.form.get("age"), 0, minimum=0, maximum=MAX_AGE
        )

        # Select random passage
        passage_keys = list(PASSAGES.keys())
        selected_passage = random.choice(passage_keys)
        session["passage_id"] = selected_passage

        # A/B testing group
        session["group"] = random.choice(["control", "treatment"])

        return redirect(url_for("study_passage"))

    return render_template("participant.html")


@app.route("/study/passage", methods=["GET", "POST"])
def study_passage():

    if "passage_id" not in session:
        return redirect(url_for("study_consent"))

    group = session.get("group", "control")
    passage = current_passage()

    if request.method == "POST":
        return redirect(url_for("study_quiz1"))

    return render_template("passage.html", passage=passage, group=group)


@app.route("/study/quiz1", methods=["GET", "POST"])
def study_quiz1():

    return run_quiz_step(
        quiz_number=1,
        confidence_key="confidence_before",
        next_endpoint="study_simplified"
    )


# ==========================================
# SIMPLIFIED VERSION
# ==========================================

@app.route("/study/simplified", methods=["GET", "POST"])
def study_simplified():

    if "passage_id" not in session:
        return redirect(url_for("study_consent"))

    if request.method == "POST":
        return redirect(url_for("study_quiz2"))

    passage = current_passage()

    try:
        raw_ai_response = simplify_text(
            passage["control_text"],
            DEFAULT_AUDIENCE
        )
    except AIServiceError:
        logger.exception(
            "Study simplification failed for passage %s",
            session["passage_id"]
        )
        return render_template(
            "simplified.html",
            simplified_text=AI_UNAVAILABLE_MESSAGE
        )

    return render_template(
        "simplified.html",
        simplified_text=render_markdown(raw_ai_response)
    )


# ==========================================
# SECOND QUIZ
# ==========================================

@app.route("/study/quiz2", methods=["GET", "POST"])
def study_quiz2():

    return run_quiz_step(
        quiz_number=2,
        confidence_key="confidence_after",
        next_endpoint="study_feedback"
    )


# ==========================================
# FEEDBACK PAGE
# ==========================================

@app.route("/study/feedback", methods=["GET", "POST"])
def study_feedback():

    if request.method == "POST":

        helpful_rating = request.form.get(
            "helpful_rating", "Neutral"
        )[:MAX_NAME_LENGTH]
        impression = request.form.get(
            "overall_impression", ""
        )[:MAX_FEEDBACK_LENGTH]
        improvements = request.form.get(
            "improvements", ""
        )[:MAX_FEEDBACK_LENGTH]

        feedback = (
            f"Rating: {helpful_rating} | "
            f"Experience: {impression} | "
            f"Improvements: {improvements}"
        )

        try:
            database.save_participant_data(
                first_name=session.get("first_name", "Anonymous"),
                age=session.get("age", 0),
                passage_id=session.get("passage_id", "unknown"),
                quiz1_score=session.get("quiz1_score", 0),
                confidence_before=session.get("confidence_before", 3),
                quiz2_score=session.get("quiz2_score", 0),
                confidence_after=session.get("confidence_after", 3),
                feedback=feedback
            )
        except Exception:
            logger.exception("Could not save participant feedback")
            return render_template(
                "feedback.html",
                error="We could not save your responses. "
                      "Please try submitting again."
            ), 500

        return redirect(url_for("study_thankyou"))

    return render_template("feedback.html")


# ==========================================
# THANK YOU PAGE
# ==========================================

@app.route("/study/thankyou")
def study_thankyou():
    return render_template("thankyou.html")


# ==========================================
# RUN SERVER
# ==========================================

if __name__ == "__main__":
    app.run(
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", 5000)),
        debug=os.environ.get("FLASK_DEBUG", "0") == "1"
    )
