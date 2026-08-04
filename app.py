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

database.init_db()


# ==========================================
# SHARED HELPERS
# ==========================================

def current_passage():
    """Return the passage assigned to the current session."""
    return get_passage(session.get("passage_id", "medical"))


def score_quiz(questions, form):
    """Count how many submitted answers match the correct option index."""
    score = 0

    for index, question in enumerate(questions, start=1):
        answer = form.get(f"q{index}")
        if answer is not None and int(answer) == question["answer"]:
            score += 1

    return score


def run_quiz_step(quiz_number, confidence_key, next_endpoint):
    """Handle one comprehension quiz: score it, store it, move on."""
    passage = current_passage()
    questions = passage.get(f"quiz{quiz_number}_questions", [])

    if request.method == "POST":
        session[f"quiz{quiz_number}_score"] = score_quiz(
            questions,
            request.form
        )
        session[confidence_key] = int(request.form.get("confidence", 3))

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
                reader = PdfReader(uploaded_file)
                pdf_text = ""
                for page in reader.pages:
                    pdf_text += page.extract_text() or ""
                content += "\n\n" + pdf_text

            # IMAGE PROCESSING
            elif filename.endswith((".png", ".jpg", ".jpeg")):
                image = Image.open(uploaded_file)
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
        age = request.form.get("age", 0)

        session["first_name"] = first_name
        session["age"] = age

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

    passage = current_passage()

    raw_ai_response = simplify_text(
        passage["control_text"],
        "General public"
    )

    simplified_html = markdown.markdown(raw_ai_response)

    if request.method == "POST":
        return redirect(url_for("study_quiz2"))

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
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=True
    )
