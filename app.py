import logging
import os
import random

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

app = Flask(__name__)
app.secret_key = os.getenv(
    "SECRET_KEY",
    "bridgeai-research-secret-key-2026"
)

# Cap upload size (default 10 MB) to avoid unbounded request bodies.
app.config["MAX_CONTENT_LENGTH"] = int(
    os.getenv("MAX_UPLOAD_BYTES", 10 * 1024 * 1024)
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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


def parse_int(value, default):
    """Parse a form value as an int, falling back to a default."""
    try:
        return int(value)
    except (TypeError, ValueError):
        logger.info("Ignoring non-numeric form value %r", value)
        return default


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
            request.form.get("confidence"), 3
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

        text = request.form.get("text", "")
        audience = request.form.get("audience", "General public")
        uploaded_file = request.files.get("file")

        content = ""

        # TEXT INPUT
        if text.strip():
            content += text

        # FILE INPUT
        if uploaded_file and uploaded_file.filename:

            filename = uploaded_file.filename.lower()

            # PDF PROCESSING
            if filename.endswith(".pdf"):
                try:
                    reader = PdfReader(uploaded_file)
                    pdf_text = ""
                    for page in reader.pages:
                        pdf_text += page.extract_text() or ""
                except Exception:
                    logger.exception("Failed to extract text from uploaded PDF")
                    return render_template(
                        "index.html",
                        result="<p>That PDF could not be read. "
                               "Please try a different file.</p>"
                    )
                content += "\n\n" + pdf_text

            # IMAGE PROCESSING
            elif filename.endswith((".png", ".jpg", ".jpeg")):
                try:
                    image = Image.open(uploaded_file)
                except Exception:
                    logger.exception("Failed to open uploaded image")
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

                result = markdown.markdown(ai_text)
                return render_template("index.html", result=result)

        if not content.strip():
            result = "<p>Please upload a PDF, image, or paste text first.</p>"
        else:
            try:
                ai_text = simplify_text(content, audience)
            except AIServiceError:
                logger.exception("Text simplification failed")
                return render_template(
                    "index.html",
                    result=AI_UNAVAILABLE_MESSAGE
                )
            result = markdown.markdown(ai_text)

    return render_template("index.html", result=result)


# ==========================================
# RESEARCH STUDY FLOW
# ==========================================

@app.route("/research", methods=["GET", "POST"])
@app.route("/study/consent", methods=["GET", "POST"])
def study_consent():

    if request.method == "POST":

        session["first_name"] = request.form.get("first_name", "Anonymous")
        session["age"] = parse_int(request.form.get("age"), 0)

        # Select random passage
        passage_keys = list(PASSAGES.keys())
        selected_passage = random.choice(passage_keys)
        session["passage_id"] = selected_passage

        # A/B testing group
        session["group"] = random.choice(["control", "treatment"])

        # Drop any cached simplification from a previous run.
        for key in [k for k in list(session.keys())
                    if k.startswith("simplified_html:")]:
            session.pop(key, None)

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

    # Generate the simplified passage once per participant/passage and cache it
    # in the session so page reloads don't trigger repeated (and differing)
    # Gemini calls during the study.
    cache_key = f"simplified_html:{session['passage_id']}"
    simplified_html = session.get(cache_key)

    if not simplified_html:
        passage = current_passage()
        try:
            raw_ai_response = simplify_text(
                passage["control_text"],
                "General public"
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

        simplified_html = markdown.markdown(raw_ai_response)
        session[cache_key] = simplified_html

    return render_template("simplified.html", simplified_text=simplified_html)


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

        helpful_rating = request.form.get("helpful_rating", "Neutral")
        impression = request.form.get("overall_impression", "")
        improvements = request.form.get("improvements", "")

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
                feedback=feedback,
                group_assignment=session.get("group")
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
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=os.getenv("FLASK_DEBUG") == "1"
    )
