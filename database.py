import logging
import os
import sqlite3
from contextlib import closing

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "research.db"
)


def init_db():
    """Initialize the SQLite database with the participants table."""
    try:
        with closing(sqlite3.connect(DB_PATH)) as conn:
            with conn:
                conn.execute("""
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
    except sqlite3.Error:
        logger.exception("Failed to initialize the research database at %s", DB_PATH)
        raise


def save_participant_data(
    first_name,
    age,
    passage_id,
    quiz1_score,
    confidence_before,
    quiz2_score,
    confidence_after,
    feedback
):
    """Save a participant's research data to the database."""
    try:
        with closing(sqlite3.connect(DB_PATH)) as conn:
            with conn:
                conn.execute("""
                    INSERT INTO participants (
                        first_name,
                        age,
                        passage_id,
                        quiz1_score,
                        confidence_before,
                        quiz2_score,
                        confidence_after,
                        feedback
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    first_name,
                    age,
                    passage_id,
                    quiz1_score,
                    confidence_before,
                    quiz2_score,
                    confidence_after,
                    feedback
                ))
    except sqlite3.Error:
        logger.exception("Failed to save participant data for passage %s", passage_id)
        raise
