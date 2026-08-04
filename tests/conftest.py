import os
import sys

import pytest
from jinja2 import FileSystemLoader

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("GEMINI_API_KEY", "test-key")
os.environ.setdefault("SECRET_KEY", "test-secret")


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    """Point database.py at a throwaway SQLite file and initialize it."""
    import database

    db_path = str(tmp_path / "research.db")
    monkeypatch.setattr(database, "DB_PATH", db_path)
    database.init_db()
    return db_path


@pytest.fixture
def client(temp_db, monkeypatch):
    """Flask test client with templates resolved from the project root."""
    import app as app_module

    monkeypatch.setattr(
        app_module, "simplify_text", lambda text, audience: "simplified"
    )
    monkeypatch.setattr(
        app_module, "analyze_image", lambda image, audience: "image summary"
    )

    flask_app = app_module.app
    flask_app.config["TESTING"] = True
    flask_app.jinja_loader = FileSystemLoader(PROJECT_ROOT)

    with flask_app.test_client() as test_client:
        yield test_client
