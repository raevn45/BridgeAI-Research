import html
import logging
import os
import random
import secrets

import markdown

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session
)

from dotenv import load_dotenv

from PIL import Image, UnidentifiedImageError

from pypdf import PdfReader

from bridgeai import (
    simplify_text,
    analyze_image
)

from passages import (
    PASSAGES,
    get_passage
)

import database

load_dotenv()

logger = logging.getLogger(__name__)

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_TEXT_LENGTH = 20000
MAX_NAME_LENGTH = 100
MAX_FEEDBACK_LENGTH = 2000
MAX_PDF_PAGES = 50
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
    logger.warning(
        "SECRET_KEY is not set; generating an ephemeral key. "
        "Sessions will be invalidated on restart."
    )
    secret_key = secrets.token_hex(32)
app.secret_key = secret_key

app.config.update(
    MAX_CONTENT_LENGTH=MAX_UPLOAD_BYTES,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.getenv("SESSION_COOKIE_SECURE", "1") == "1",
)

database.init_db()


def render_markdown(text):
    """Render untrusted markdown without letting raw HTML through."""
    return markdown.markdown(html.escape(text))


def extract_pdf_text(uploaded_file):
    """Extract text from an uploaded PDF, or None when it cannot be read."""
    try:
        reader = PdfReader(uploaded_file)
        pages = reader.pages[:MAX_PDF_PAGES]
        return "".join(page.extract_text() or "" for page in pages)
    except Exception:
        logger.exception("Failed to read uploaded PDF")
        return None


def load_image(uploaded_file):
    """Open an uploaded image, or None when it is not a valid image."""
    try:
        image = Image.open(uploaded_file)
        image.verify()
        uploaded_file.seek(0)
        return Image.open(uploaded_file)
    except (UnidentifiedImageError, OSError, ValueError):
        logger.exception("Failed to read uploaded image")
        return None


def clean_audience(value):
    """Restrict the audience to the values offered by the form."""
    return value if value in ALLOWED_AUDIENCES else DEFAULT_AUDIENCE


def parse_int(value, default, minimum, maximum):
    """Parse an integer form field, falling back to a clamped default."""
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, parsed))


def score_quiz(questions):
    """Score submitted answers against the expected question answers."""
    score = 0
    for index, question in enumerate(questions, start=1):
        answer = parse_int(request.form.get(f"q{index}"), None, 0, 10)
        if answer is not None and answer == question["answer"]:
            score += 1
    return score


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
        audience = clean_audience(request.form.get("audience", DEFAULT_AUDIENCE))
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
                        result=render_markdown(
                            "That PDF could not be read. "
                            "Please try a different file."
                        )
                    )
                content += "\n\n" + pdf_text

            # IMAGE PROCESSING
            elif filename.endswith(IMAGE_EXTENSIONS):
                image = load_image(uploaded_file)
                if image is None:
                    return render_template(
                        "index.html",
                        result=render_markdown(
                            "That image could not be read. "
                            "Please upload a PNG or JPG file."
                        )
                    )
                ai_text = analyze_image(image, audience)
                return render_template(
                    "index.html",
                    result=render_markdown(ai_text)
                )

            else:
                return render_template(
                    "index.html",
                    result=render_markdown(
                        "Unsupported file type. "
                        "Please upload a PDF, PNG, or JPG file."
                    )
                )

        if not content.strip():
            result = render_markdown(
                "Please upload a PDF, image, or paste text first."
            )
        else:
            ai_text = simplify_text(content[:MAX_TEXT_LENGTH], audience)
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
        session["age"] = parse_int(request.form.get("age"), 0, 0, 120)

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

    passage_id = session.get("passage_id", "medical")
    group = session.get("group", "control")
    passage = get_passage(passage_id)

    if request.method == "POST":
        return redirect(url_for("study_quiz1"))

    return render_template("passage.html", passage=passage, group=group)


@app.route("/study/quiz1", methods=["GET", "POST"])
def study_quiz1():

    passage_id = session.get("passage_id", "medical")
    passage = get_passage(passage_id)
    questions = passage.get("quiz1_questions", [])

    if request.method == "POST":
        session["quiz1_score"] = score_quiz(questions)
        session["confidence_before"] = parse_int(
            request.form.get("confidence"), 3, 1, 5
        )

        return redirect(url_for("study_simplified"))

    return render_template("quiz1.html", passage=passage, questions=questions)


# ==========================================
# SIMPLIFIED VERSION
# ==========================================

@app.route("/study/simplified", methods=["GET", "POST"])
def study_simplified():

    passage_id = session.get("passage_id", "medical")
    passage = get_passage(passage_id)

    raw_ai_response = simplify_text(
        passage["control_text"],
        "General public"
    )

    simplified_html = render_markdown(raw_ai_response)

    if request.method == "POST":
        return redirect(url_for("study_quiz2"))

    return render_template("simplified.html", simplified_text=simplified_html)


# ==========================================
# SECOND QUIZ
# ==========================================

@app.route("/study/quiz2", methods=["GET", "POST"])
def study_quiz2():

    passage_id = session.get("passage_id", "medical")
    passage = get_passage(passage_id)
    questions = passage.get("quiz2_questions", [])

    if request.method == "POST":
        session["quiz2_score"] = score_quiz(questions)
        session["confidence_after"] = parse_int(
            request.form.get("confidence"), 3, 1, 5
        )

        return redirect(url_for("study_feedback"))

    return render_template("quiz2.html", passage=passage, questions=questions)


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
