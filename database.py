import logging
import os
import sqlite3
from contextlib import contextmanager
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Local development uses SQLite. Production should set DATABASE_URL to a
# managed PostgreSQL database; Vercel's function filesystem is not persistent.
DB_PATH = os.getenv(
    "SQLITE_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "research.db"),
)


class CursorAdapter:
    """Keep the existing qmark SQL compatible with SQLite and PostgreSQL."""

    def __init__(self, cursor, postgres=False):
        self._cursor = cursor
        self._postgres = postgres

    def execute(self, query, params=()):
        if self._postgres:
            query = query.replace("?", "%s")
        return self._cursor.execute(query, params)

    @property
    def description(self):
        return self._cursor.description

    def fetchall(self):
        return self._cursor.fetchall()

    def fetchone(self):
        return self._cursor.fetchone()


@contextmanager
def get_cursor():
    database_url = os.getenv("DATABASE_URL")
    if not database_url and os.getenv("VERCEL") == "1":
        raise RuntimeError("Set DATABASE_URL to a managed PostgreSQL database before using the research app on Vercel.")
    if database_url:
        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError as exc:
            raise RuntimeError(
                "DATABASE_URL is set but psycopg is not installed. "
                "Install the project's requirements."
            ) from exc

        conn = psycopg.connect(database_url, row_factory=dict_row)
        try:
            yield CursorAdapter(conn.cursor(), postgres=True)
            conn.commit()
        except Exception:
            conn.rollback()
            logger.exception("PostgreSQL database operation failed")
            raise
        finally:
            conn.close()
        return

    conn = sqlite3.connect(DB_PATH)
    try:
        yield CursorAdapter(conn.cursor())
        conn.commit()
    except Exception:
        conn.rollback()
        logger.exception("SQLite database operation on %s failed", DB_PATH)
        raise
    finally:
        conn.close()


def init_db():
    """Initialize the participant table in SQLite or managed PostgreSQL."""
    with get_cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS participants (
                id SERIAL PRIMARY KEY,
                first_name TEXT,
                age INTEGER,
                passage_id TEXT,
                group_assignment TEXT,
                quiz1_score INTEGER,
                confidence_before INTEGER,
                quiz2_score INTEGER,
                confidence_after INTEGER,
                feedback TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """ if os.getenv("DATABASE_URL") else """
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
    """Save a participant's research data."""
    with get_cursor() as cursor:
        cursor.execute("""
            INSERT INTO participants (
                first_name, age, passage_id, group_assignment, quiz1_score,
                confidence_before, quiz2_score, confidence_after, feedback
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            first_name, age, passage_id, group_assignment, quiz1_score,
            confidence_before, quiz2_score, confidence_after, feedback,
        ))


def get_all_participant_data():
    """Return all participant rows as dictionaries."""
    with get_cursor() as cursor:
        cursor.execute("SELECT * FROM participants ORDER BY id")
        rows = cursor.fetchall()
        if rows and isinstance(rows[0], dict):
            return rows
        columns = [
            column.name if hasattr(column, "name") else column[0]
            for column in cursor.description
        ]
        return [dict(zip(columns, row)) for row in rows]
