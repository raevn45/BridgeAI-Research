import logging
import os
import sqlite3
from contextlib import contextmanager

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "research.db")


@contextmanager
def get_cursor():
    """Yield a cursor, committing on success and rolling back on failure."""
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn.cursor()
        conn.commit()
    except Exception:
        conn.rollback()
        logger.exception("Database operation on %s failed", DB_PATH)
        raise
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
    quiz1_score,
    confidence_before,
    quiz2_score,
    confidence_after,
    feedback,
    group_assignment=None,
):
    """Save a participant's research data to the database."""
    with get_cursor() as cursor:
        cursor.execute(
            """
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
        """,
            (
                first_name,
                age,
                passage_id,
                group_assignment,
                quiz1_score,
                confidence_before,
                quiz2_score,
                confidence_after,
                feedback,
            ),
        )


def get_all_participant_data():
    """Return all rows from the participants table as a list of dictionaries."""
    with get_cursor() as cursor:
        cursor.execute("SELECT * FROM participants")
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
