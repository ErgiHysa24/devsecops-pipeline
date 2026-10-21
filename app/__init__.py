"""Notes API: a small Flask service used to demonstrate a DevSecOps pipeline."""

import ipaddress
import os
import sqlite3
# Used only with a fixed argument list, see /ping
import subprocess  # nosec B404

from flask import Flask, g, jsonify, request

MAX_TITLE = 200
MAX_BODY = 10_000


def create_app(db_path=None):
    app = Flask(__name__)
    app.config["DATABASE"] = db_path or os.environ.get("NOTES_DB", "notes.db")

    def get_db():
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DATABASE"])
            g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def close_db(_exc):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    with app.app_context():
        get_db().execute(
            "CREATE TABLE IF NOT EXISTS notes ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "title TEXT NOT NULL, body TEXT NOT NULL)"
        )
        get_db().commit()

    @app.get("/health")
    def health():
        return jsonify(status="ok")

    @app.get("/ping")
    def ping():
        host = request.args.get("host", "127.0.0.1")
        try:
            ipaddress.ip_address(host)
        except ValueError:
            return jsonify(error="invalid host"), 400
        # host is validated as an IP address and no shell is used
        result = subprocess.run(  # nosec B603 B607
            ["ping", "-c", "1", host],
            capture_output=True, text=True, timeout=5, check=False,
        )
        return result.stdout

    @app.get("/notes")
    def list_notes():
        query = request.args.get("q", "")
        rows = get_db().execute(
            "SELECT id, title, body FROM notes WHERE title LIKE ? ORDER BY id",
            (f"%{query}%",),
        ).fetchall()
        return jsonify([dict(r) for r in rows])

    @app.get("/notes/<int:note_id>")
    def get_note(note_id):
        row = get_db().execute(
            "SELECT id, title, body FROM notes WHERE id = ?", (note_id,)
        ).fetchone()
        if row is None:
            return jsonify(error="not found"), 404
        return jsonify(dict(row))

    @app.post("/notes")
    def create_note():
        data = request.get_json(silent=True) or {}
        title = data.get("title")
        body = data.get("body", "")
        if not isinstance(title, str) or not title.strip():
            return jsonify(error="title is required"), 400
        if not isinstance(body, str):
            return jsonify(error="body must be a string"), 400
        if len(title) > MAX_TITLE or len(body) > MAX_BODY:
            return jsonify(error="too long"), 400
        db = get_db()
        cur = db.execute(
            "INSERT INTO notes (title, body) VALUES (?, ?)", (title.strip(), body)
        )
        db.commit()
        return jsonify(id=cur.lastrowid, title=title.strip(), body=body), 201

    @app.delete("/notes/<int:note_id>")
    def delete_note(note_id):
        db = get_db()
        cur = db.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        db.commit()
        if cur.rowcount == 0:
            return jsonify(error="not found"), 404
        return "", 204

    return app
