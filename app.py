import logging
import os
import random

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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

database.init_db()

AI_UNAVAILABLE_MESSAGE = (
    "<p>BridgeAI could not generate a simplification right now. "
    "Please try again in a few moments.</p>"
)


def parse_int(value, default):
    """Parse a form value as an int, falling back to a default."""
    try:
        return int(value)
    except (TypeError, ValueError):
        logger.info("Ignoring non-numeric form value %r", value)
        return default


def score_quiz(questions, form):
    """Count correct answers, ignoring missing or malformed submissions."""
    score = 0
    for index, question in enumerate(questions, start=1):
        answer = parse_int(form.get(f"q{index}"), None)
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
                from pypdf import PdfReader
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
                from PIL import Image
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

        return redirect(url_for("study_passage"))

    return render_template("participant.html")


@app.route("/study/passage", methods=["GET", "POST"])
def study_passage():

    if "passage_id" not in session:
        return redirect(url_for("study_consent"))

    passage_id = session["passage_id"]
    group = session.get("group", "control")
    passage = get_passage(passage_id)

    if request.method == "POST":
        return redirect(url_for("study_quiz1"))

    return render_template("passage.html", passage=passage, group=group)


@app.route("/study/quiz1", methods=["GET", "POST"])
def study_quiz1():

    if "passage_id" not in session:
        return redirect(url_for("study_consent"))

    passage = get_passage(session["passage_id"])
    questions = passage.get("quiz1_questions", [])

    if request.method == "POST":
        session["quiz1_score"] = score_quiz(questions, request.form)
        session["confidence_before"] = parse_int(
            request.form.get("confidence"), 3
        )

        return redirect(url_for("study_simplified"))

    return render_template("quiz1.html", passage=passage, questions=questions)


# ==========================================
# SIMPLIFIED VERSION
# ==========================================

@app.route("/study/simplified", methods=["GET", "POST"])
def study_simplified():

    if "passage_id" not in session:
        return redirect(url_for("study_consent"))

    if request.method == "POST":
        return redirect(url_for("study_quiz2"))

    passage = get_passage(session["passage_id"])

    try:
        raw_ai_response = simplify_text(
            passage["control_text"],
            "General public"
        )
    except AIServiceError:
        logger.exception("Study simplification failed for passage %s", session["passage_id"])
        return render_template(
            "simplified.html",
            simplified_text=AI_UNAVAILABLE_MESSAGE
        )

    simplified_html = markdown.markdown(raw_ai_response)

    return render_template("simplified.html", simplified_text=simplified_html)


# ==========================================
# SECOND QUIZ
# ==========================================

@app.route("/study/quiz2", methods=["GET", "POST"])
def study_quiz2():

    if "passage_id" not in session:
        return redirect(url_for("study_consent"))

    passage = get_passage(session["passage_id"])
    questions = passage.get("quiz2_questions", [])

    if request.method == "POST":
        session["quiz2_score"] = score_quiz(questions, request.form)
        session["confidence_after"] = parse_int(
            request.form.get("confidence"), 3
        )

        return redirect(url_for("study_feedback"))

    return render_template("quiz2.html", passage=passage, questions=questions)


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
                feedback=feedback
            )
        except Exception:
            logger.exception("Could not save participant feedback")
            return render_template(
                "feedback.html",
                error="We could not save your responses. Please try submitting again."
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
        debug=True
    )