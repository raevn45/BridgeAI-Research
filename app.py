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

database.init_db()


def _safe_int(value, default=0):
    """Parse an int from untrusted form input, falling back to a default."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


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
                    content += "\n\n" + pdf_text
                except Exception as e:
                    print("PDF parse error:", e)
                    result = (
                        "<p>Could not read that PDF. "
                        "Please try a different file or paste the text.</p>"
                    )
                    return render_template("index.html", result=result)

            # IMAGE PROCESSING
            elif filename.endswith((".png", ".jpg", ".jpeg")):
                from PIL import Image
                try:
                    image = Image.open(uploaded_file)
                except Exception as e:
                    print("Image open error:", e)
                    result = "<p>Could not read that image. Please try another file.</p>"
                    return render_template("index.html", result=result)
                ai_text = analyze_image(image, audience)
                result = markdown.markdown(ai_text)
                return render_template("index.html", result=result)

        if not content.strip():
            result = "<p>Please upload a PDF, image, or paste text first.</p>"
        else:
            ai_text = simplify_text(content, audience)
            result = markdown.markdown(ai_text)

    return render_template("index.html", result=result)


# ==========================================
# RESEARCH STUDY FLOW
# ==========================================

@app.route("/research", methods=["GET", "POST"])
@app.route("/study/consent", methods=["GET", "POST"])
def study_consent():

    if request.method == "POST":

        first_name = request.form.get("first_name", "Anonymous")
        age = _safe_int(request.form.get("age"), 0)

        session["first_name"] = first_name
        session["age"] = age

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
        score = 0
        for index, question in enumerate(questions, start=1):
            answer = request.form.get(f"q{index}")
            if answer is not None and _safe_int(answer, -1) == question["answer"]:
                score += 1

        session["quiz1_score"] = score
        session["confidence_before"] = _safe_int(
            request.form.get("confidence"), 3
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

    # Generate the simplified passage once per participant/passage and cache it
    # in the session so page reloads don't trigger repeated (and differing)
    # Gemini calls during the study.
    cache_key = f"simplified_html:{passage_id}"
    simplified_html = session.get(cache_key)
    if not simplified_html:
        raw_ai_response = simplify_text(
            passage["control_text"],
            "General public"
        )
        simplified_html = markdown.markdown(raw_ai_response)
        session[cache_key] = simplified_html

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
        score = 0
        for index, question in enumerate(questions, start=1):
            answer = request.form.get(f"q{index}")
            if answer is not None and _safe_int(answer, -1) == question["answer"]:
                score += 1

        session["quiz2_score"] = score
        session["confidence_after"] = _safe_int(
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

        database.save_participant_data(
            first_name=session.get("first_name", "Anonymous"),
            age=session.get("age", 0),
            passage_id=session.get("passage_id", "unknown"),
            group_assignment=session.get("group", "unknown"),
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
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=os.getenv("FLASK_DEBUG") == "1"
    )