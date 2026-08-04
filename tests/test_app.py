import io
import sqlite3

import pytest
from flask import session

from passages import PASSAGES


def get_participants(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM participants").fetchall()
    conn.close()
    return rows


@pytest.mark.parametrize(
    "path",
    [
        "/",
        "/app",
        "/research",
        "/study/consent",
        "/study/passage",
        "/study/quiz1",
        "/study/quiz2",
        "/study/feedback",
        "/study/thankyou",
    ],
)
def test_pages_render(client, path):
    assert client.get(path).status_code == 200


def test_bridge_app_simplifies_pasted_text(client):
    response = client.post(
        "/app", data={"text": "dense legalese", "audience": "Children"}
    )

    assert response.status_code == 200
    assert b"simplified" in response.data


def test_bridge_app_prompts_when_no_input_given(client):
    response = client.post("/app", data={"text": "   "})

    assert b"Please upload a PDF, image, or paste text first." in response.data


def test_bridge_app_analyzes_uploaded_image(client, monkeypatch):
    monkeypatch.setattr("app.Image.open", lambda stream: "fake-image")

    response = client.post(
        "/app",
        data={"file": (io.BytesIO(b"not-really-a-png"), "scan.png")},
        content_type="multipart/form-data",
    )

    assert b"image summary" in response.data


def test_bridge_app_extracts_text_from_pdf(client, monkeypatch):
    class FakePage:
        def extract_text(self):
            return "pdf words"

    class FakeReader:
        def __init__(self, stream):
            self.pages = [FakePage(), FakePage()]

    monkeypatch.setattr("app.PdfReader", FakeReader)
    captured = {}

    def fake_simplify(text, audience):
        captured["text"] = text
        return "pdf simplified"

    monkeypatch.setattr("app.simplify_text", fake_simplify)

    response = client.post(
        "/app",
        data={"file": (io.BytesIO(b"%PDF-1.4"), "notice.pdf")},
        content_type="multipart/form-data",
    )

    assert b"pdf simplified" in response.data
    assert captured["text"].count("pdf words") == 2


def test_consent_post_assigns_session_state(client):
    response = client.post(
        "/study/consent", data={"first_name": "Ada", "age": "36"}
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/study/passage")
    assert session["first_name"] == "Ada"
    assert session["age"] == "36"
    assert session["passage_id"] in PASSAGES
    assert session["group"] in ("control", "treatment")


def test_consent_post_uses_defaults_when_fields_missing(client):
    client.post("/study/consent", data={})
    assert session["first_name"] == "Anonymous"
    assert session["age"] == 0


def test_passage_post_redirects_to_quiz1(client):
    response = client.post("/study/passage")

    assert response.headers["Location"].endswith("/study/quiz1")


def test_simplified_page_shows_rendered_markdown(client, monkeypatch):
    monkeypatch.setattr(
        "app.simplify_text", lambda text, audience: "## Heading\n\nbody"
    )

    response = client.get("/study/simplified")

    assert b"<h2>Heading</h2>" in response.data


def test_simplified_post_redirects_to_quiz2(client):
    response = client.post("/study/simplified")

    assert response.headers["Location"].endswith("/study/quiz2")


@pytest.mark.parametrize(
    "quiz_path, quiz_key, score_key, confidence_key, next_path",
    [
        (
            "/study/quiz1",
            "quiz1_questions",
            "quiz1_score",
            "confidence_before",
            "/study/simplified",
        ),
        (
            "/study/quiz2",
            "quiz2_questions",
            "quiz2_score",
            "confidence_after",
            "/study/feedback",
        ),
    ],
)
def test_quiz_scores_correct_answers(
    client, quiz_path, quiz_key, score_key, confidence_key, next_path
):
    questions = PASSAGES["medical"][quiz_key]
    data = {
        f"q{index}": str(question["answer"])
        for index, question in enumerate(questions, start=1)
    }
    data["confidence"] = "5"

    client.post("/study/consent", data={"first_name": "Ada", "age": "36"})
    with client.session_transaction() as sess:
        sess["passage_id"] = "medical"

    response = client.post(quiz_path, data=data)
    assert response.headers["Location"].endswith(next_path)
    assert session[score_key] == len(questions)
    assert session[confidence_key] == 5


def test_quiz1_ignores_wrong_and_unanswered_questions(client):
    questions = PASSAGES["medical"]["quiz1_questions"]
    correct = questions[0]["answer"]
    wrong = (correct + 1) % len(questions[0]["options"])

    with client.session_transaction() as sess:
        sess["passage_id"] = "medical"

    client.post("/study/quiz1", data={"q1": str(wrong)})
    assert session["quiz1_score"] == 0
    assert session["confidence_before"] == 3


def test_feedback_post_saves_participant_and_redirects(client, temp_db):
    with client.session_transaction() as sess:
        sess.update(
            first_name="Ada",
            age="36",
            passage_id="legal",
            quiz1_score=1,
            confidence_before=2,
            quiz2_score=3,
            confidence_after=4,
        )

    response = client.post(
        "/study/feedback",
        data={
            "helpful_rating": "Very helpful",
            "overall_impression": "Clear",
            "improvements": "More examples",
        },
    )

    assert response.headers["Location"].endswith("/study/thankyou")

    row = get_participants(temp_db)[0]
    assert row["first_name"] == "Ada"
    assert row["passage_id"] == "legal"
    assert row["quiz1_score"] == 1
    assert row["confidence_after"] == 4
    assert row["feedback"] == (
        "Rating: Very helpful | Experience: Clear | Improvements: More examples"
    )


def test_feedback_post_falls_back_to_session_defaults(client, temp_db):
    client.post("/study/feedback", data={})

    row = get_participants(temp_db)[0]
    assert row["first_name"] == "Anonymous"
    assert row["age"] == 0
    assert row["passage_id"] == "unknown"
    assert row["quiz1_score"] == 0
    assert row["confidence_before"] == 3
    assert row["feedback"] == "Rating: Neutral | Experience:  | Improvements: "
