import os
import sqlite3
from contextlib import contextmanager

DB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "research.db"
)


@contextmanager
def get_cursor():
    """Yield a cursor, committing and closing the connection afterwards."""
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn.cursor()
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Initialize the SQLite database with the participants table."""
    with get_cursor() as cursor:
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
    with get_cursor() as cursor:
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
