"""Single-company local persistence. Back up the SQLite database with SQLite's backup API."""
import hashlib
import json
import os
import secrets
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path


def db_path():
    return Path(os.environ.get("WORKSPACE_DB", str(Path(__file__).resolve().parents[2] / "data" / "workspace.sqlite3")))


@contextmanager
def database():
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=20)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("PRAGMA journal_mode=WAL")
    connection.executescript('''
      CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY, email TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
        password TEXT NOT NULL, role TEXT NOT NULL, created REAL NOT NULL, active INTEGER NOT NULL DEFAULT 1);
      CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id), expires REAL NOT NULL);
      CREATE TABLE IF NOT EXISTS user_avatars(user_id TEXT PRIMARY KEY REFERENCES users(id), image BLOB NOT NULL, version TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS login_attempts(email TEXT PRIMARY KEY, count INTEGER NOT NULL, since REAL NOT NULL);
      CREATE TABLE IF NOT EXISTS documents(id TEXT PRIMARY KEY, name TEXT NOT NULL, insurer TEXT NOT NULL DEFAULT '',
        pdf BLOB NOT NULL, original TEXT NOT NULL DEFAULT '[]', working TEXT NOT NULL DEFAULT '[]',
        filename TEXT NOT NULL, revision INTEGER NOT NULL DEFAULT 0, state TEXT NOT NULL,
        error TEXT, owner TEXT NOT NULL REFERENCES users(id), created REAL NOT NULL, updated REAL NOT NULL);
      CREATE TABLE IF NOT EXISTS revisions(id TEXT PRIMARY KEY, document_id TEXT NOT NULL REFERENCES documents(id),
        revision INTEGER NOT NULL, data TEXT NOT NULL, filename TEXT NOT NULL, user_id TEXT NOT NULL REFERENCES users(id),
        created REAL NOT NULL, UNIQUE(document_id, revision));
      CREATE TABLE IF NOT EXISTS exports(id TEXT PRIMARY KEY, document_id TEXT NOT NULL REFERENCES documents(id),
        version INTEGER NOT NULL, revision INTEGER NOT NULL, filename TEXT NOT NULL, data BLOB NOT NULL,
        user_id TEXT NOT NULL REFERENCES users(id), created REAL NOT NULL, UNIQUE(document_id, version));
      CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY, document_id TEXT REFERENCES documents(id),
        user_id TEXT NOT NULL REFERENCES users(id), action TEXT NOT NULL, details TEXT NOT NULL, created REAL NOT NULL);
    ''')
    if "active" not in {row[1] for row in connection.execute("PRAGMA table_info(users)")}:
        connection.execute("ALTER TABLE users ADD COLUMN active INTEGER NOT NULL DEFAULT 1")
    try:
        yield connection
        connection.commit()
    except BaseException:
        connection.rollback()
        raise
    finally:
        connection.close()


def password_hash(password, salt=None):
    salt = salt or secrets.token_hex(16)
    derived = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1).hex()
    return f"{salt}:{derived}"


def password_valid(password, stored):
    return secrets.compare_digest(password_hash(password, stored.split(":")[0]), stored)


def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


def encode(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False)


def event(db, user, action, document=None, details=None):
    db.execute("INSERT INTO events(document_id,user_id,action,details,created) VALUES(?,?,?,?,?)",
               (document, user["id"], action, encode(details or {}), time.time()))
