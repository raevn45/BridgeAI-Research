import sqlite3

import database


def fetch_all(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM participants").fetchall()
    conn.close()
    return rows


def test_init_db_creates_participants_table(temp_db):
    conn = sqlite3.connect(temp_db)
    columns = {row[1] for row in conn.execute("PRAGMA table_info(participants)")}
    conn.close()

    assert columns == {
        "id",
        "first_name",
        "age",
        "passage_id",
        "group_assignment",
        "quiz1_score",
        "confidence_before",
        "quiz2_score",
        "confidence_after",
        "feedback",
        "timestamp",
    }


def test_init_db_is_idempotent(temp_db):
    database.save_participant_data(
        "Ada", 30, "medical", 2, 3, 4, 5, "feedback"
    )
    database.init_db()

    assert len(fetch_all(temp_db)) == 1


def test_save_participant_data_persists_all_fields(temp_db):
    database.save_participant_data(
        first_name="Ada",
        age=36,
        passage_id="legal",
        quiz1_score=1,
        confidence_before=2,
        quiz2_score=4,
        confidence_after=5,
        feedback="Rating: Helpful",
    )

    row = fetch_all(temp_db)[0]
    assert row["first_name"] == "Ada"
    assert row["age"] == 36
    assert row["passage_id"] == "legal"
    assert row["quiz1_score"] == 1
    assert row["confidence_before"] == 2
    assert row["quiz2_score"] == 4
    assert row["confidence_after"] == 5
    assert row["feedback"] == "Rating: Helpful"
    assert row["group_assignment"] is None
    assert row["timestamp"] is not None


def test_save_participant_data_appends_rows(temp_db):
    for name in ("Ada", "Grace", "Alan"):
        database.save_participant_data(name, 20, "medical", 0, 3, 0, 3, "")

    rows = fetch_all(temp_db)
    assert [row["first_name"] for row in rows] == ["Ada", "Grace", "Alan"]
    assert [row["id"] for row in rows] == [1, 2, 3]
