import os
import sqlite3

DB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "research.db"
)


def init_db():
    """Initialize the SQLite database with the participants table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT,
            age INTEGER,
            passage_id TEXT,
            group_assignment TEXT,
            quiz1_score INTEGER,
            confidence_before INTEGER,
            quiz2_score INTEGER,
            confidence_after INTEGER,
            feedback TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def save_participant_data(
    first_name,
    age,
    passage_id,
    group_assignment,
    quiz1_score,
    confidence_before,
    quiz2_score,
    confidence_after,
    feedback
):
    """Save a participant's research data to the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO participants (
            first_name,
            age,
            passage_id,
            group_assignment,
            quiz1_score,
            confidence_before,
            quiz2_score,
            confidence_after,
            feedback
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        first_name,
        age,
        passage_id,
        group_assignment,
        quiz1_score,
        confidence_before,
        quiz2_score,
        confidence_after,
        feedback
    ))

    conn.commit()
    conn.close()