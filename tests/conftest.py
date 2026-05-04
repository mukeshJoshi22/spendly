"""
conftest.py — shared fixtures for Spendly pytest suite.

All tests run against a fresh in-memory SQLite database that is created per
test function so there is never shared mutable state between tests.

The fixture monkey-patches database.db.DB_PATH to ':memory:' before each test
and restores the original value afterwards.  Because sqlite3 closes the
connection after every helper call we cannot simply hold a single in-memory
connection open; instead we redirect every get_db() call to a named shared
in-memory database (URI mode) so all calls within one test share the same
in-memory store.
"""

import sqlite3
import pytest
from werkzeug.security import generate_password_hash

import database.db as db_module


# ------------------------------------------------------------------ #
# Helpers used by multiple test files                                 #
# ------------------------------------------------------------------ #

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT    NOT NULL,
    email         TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    created_at    TEXT    DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS expenses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id),
    amount      REAL    NOT NULL,
    category    TEXT    NOT NULL,
    date        TEXT    NOT NULL,
    description TEXT,
    created_at  TEXT    DEFAULT (datetime('now'))
);
"""


def _make_shared_uri(test_name: str) -> str:
    """Return a URI for a named shared in-memory SQLite database."""
    safe = test_name.replace("[", "_").replace("]", "_").replace(" ", "_")
    return f"file:{safe}?mode=memory&cache=shared"


@pytest.fixture()
def app(monkeypatch, request):
    """
    Yield a configured Flask test application backed by a fresh in-memory DB.

    Steps:
    1. Build a named shared in-memory SQLite URI unique to this test.
    2. Patch database.db.get_db() to return connections to that URI.
    3. Bootstrap the schema into that in-memory store.
    4. Yield the Flask app with TESTING=True.
    5. Teardown is automatic — in-memory DB is discarded when all connections close.
    """
    import app as app_module

    db_uri = _make_shared_uri(request.node.nodeid)

    def patched_get_db():
        conn = sqlite3.connect(db_uri, uri=True)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    monkeypatch.setattr(db_module, "get_db", patched_get_db)

    # Bootstrap schema into the fresh in-memory DB.
    conn = patched_get_db()
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    conn.close()

    flask_app = app_module.app
    flask_app.config["TESTING"] = True
    flask_app.config["WTF_CSRF_ENABLED"] = False

    yield flask_app


@pytest.fixture()
def client(app):
    """Return a Flask test client for the app fixture."""
    return app.test_client()


# ------------------------------------------------------------------ #
# DB seed helpers (used in multiple test files)                       #
# ------------------------------------------------------------------ #

def seed_user(monkeypatch, request, name="Test User", email="test@example.com",
              password="password123"):
    """
    Insert a test user into the in-memory DB and return their id.

    This is a plain function (not a fixture) so callers can customise
    name/email/password and call it multiple times within one test.
    """
    import database.db as db_mod
    pw_hash = generate_password_hash(password, method="pbkdf2:sha256")
    conn = db_mod.get_db()
    cursor = conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        (name, email, pw_hash),
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id


def seed_expense(user_id, amount, category, date, description=""):
    """Insert a single expense row and return its id."""
    import database.db as db_mod
    conn = db_mod.get_db()
    cursor = conn.execute(
        "INSERT INTO expenses (user_id, amount, category, date, description) "
        "VALUES (?, ?, ?, ?, ?)",
        (user_id, amount, category, date, description),
    )
    conn.commit()
    expense_id = cursor.lastrowid
    conn.close()
    return expense_id
