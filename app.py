import os
import sqlite3
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path

from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
DATABASE = Path(os.environ.get("DATABASE_PATH", BASE_DIR / "database.db"))

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-this-secret-key")


def get_db():
    """Open a SQLite connection and return rows by column name."""
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db():
    """Create tables and seed demo data/admin account if they don't exist."""
    DATABASE.parent.mkdir(parents=True, exist_ok=True)
    with get_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            event_date TEXT NOT NULL,
            venue TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT NOT NULL,
            event_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(phone, event_id),
            FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE
        );
        """)

        admin_username = os.environ.get("ADMIN_USERNAME", "admin")
        admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
        existing_admin = db.execute(
            "SELECT id FROM admins WHERE username = ?", (admin_username,)
        ).fetchone()
        if not existing_admin:
            db.execute(
                "INSERT INTO admins (username, password_hash) VALUES (?, ?)",
                (admin_username, generate_password_hash(admin_password)),
            )

        event_count = db.execute("SELECT COUNT(*) AS count FROM events").fetchone()["count"]
        if event_count == 0:
            db.executemany(
                "INSERT INTO events (title, description, event_date, venue) VALUES (?, ?, ?, ?)",
                [
                    ("CodeOMania", "A day of coding, innovation, and technical competitions.", "2026-11-23", "Seminar Hall"),
                    ("Cultural Night", "Music, dance, performances, and student showcases.", "2026-11-22", "Auditorium"),
                    ("Hackathon Sprint", "Build a prototype with a team and present your solution.", "2026-11-25", "Innovation Lab"),
                ],
            )


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_id"):
            if request.path.startswith("/api/"):
                return jsonify({"error": "Please log in as an admin."}), 401
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


@app.get("/")
def index():
    with get_db() as db:
        events = db.execute(
            """SELECT e.*,
                      (SELECT COUNT(*) FROM registrations r WHERE r.event_id = e.id) AS registration_count
               FROM events e ORDER BY e.event_date"""
        ).fetchall()
    return render_template("index.html", events=events)


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("admin_id"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        with get_db() as db:
            admin = db.execute(
                "SELECT * FROM admins WHERE username = ?", (username,)
            ).fetchone()

        if admin and check_password_hash(admin["password_hash"], password):
            session.clear()
            session["admin_id"] = admin["id"]
            session["admin_username"] = admin["username"]
            return redirect(url_for("dashboard"))

        flash("Incorrect username or password.", "error")

    return render_template("login.html")


@app.post("/logout")
@admin_required
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.get("/admin")
@admin_required
def dashboard():
    return render_template("admin.html", username=session.get("admin_username", "Admin"))


@app.get("/api/events")
def api_events():
    with get_db() as db:
        events = db.execute(
            """SELECT e.*,
                      (SELECT COUNT(*) FROM registrations r WHERE r.event_id = e.id) AS registration_count
               FROM events e ORDER BY e.event_date"""
        ).fetchall()
    return jsonify([dict(row) for row in events])


@app.post("/api/register")
def api_register():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    phone = "".join(ch for ch in str(data.get("phone", "")) if ch.isdigit())
    event_id = data.get("event_id")

    if not name or len(name) > 100:
        return jsonify({"error": "Please enter your name (up to 100 characters)."}), 400
    if not email or "@" not in email or len(email) > 254:
        return jsonify({"error": "Please enter a valid email address."}), 400
    if len(phone) < 10 or len(phone) > 15:
        return jsonify({"error": "Please enter a valid phone number (10–15 digits)."}), 400

    try:
        event_id = int(event_id)
    except (TypeError, ValueError):
        return jsonify({"error": "Please select an event before registering."}), 400

    with get_db() as db:
        event = db.execute("SELECT id FROM events WHERE id = ?", (event_id,)).fetchone()
        if not event:
            return jsonify({"error": "That event could not be found. Refresh the page and try again."}), 404
        try:
            db.execute(
                "INSERT INTO registrations (name, phone, email, event_id, created_at) VALUES (?, ?, ?, ?, ?)",
                (name, phone, email, event_id, datetime.now(timezone.utc).isoformat(timespec="seconds")),
            )
        except sqlite3.IntegrityError:
            return jsonify({"error": "This phone number is already registered for this event."}), 409

    return jsonify({"message": "Registration successful! See you at the event.", "type": "registration"}), 201


@app.get("/api/admin/registrations")
@admin_required
def api_admin_registrations():
    with get_db() as db:
        rows = db.execute(
            """SELECT r.id, r.name, r.phone, r.email, r.created_at,
                      e.title AS event_title, e.event_date
               FROM registrations r
               JOIN events e ON e.id = r.event_id
               ORDER BY r.created_at DESC"""
        ).fetchall()
    return jsonify([dict(row) for row in rows])


@app.post("/api/admin/events")
@admin_required
def api_create_event():
    data = request.get_json(silent=True) or {}
    title = str(data.get("title", "")).strip()
    description = str(data.get("description", "")).strip()
    event_date = str(data.get("event_date", "")).strip()
    venue = str(data.get("venue", "")).strip()

    if not all([title, description, event_date, venue]):
        return jsonify({"error": "Please fill in every event field."}), 400
    try:
        datetime.strptime(event_date, "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "Please choose a valid event date."}), 400

    with get_db() as db:
        cursor = db.execute(
            "INSERT INTO events (title, description, event_date, venue) VALUES (?, ?, ?, ?)",
            (title, description, event_date, venue),
        )
        event_id = cursor.lastrowid
    return jsonify({"message": "Event created successfully.", "id": event_id}), 201


@app.delete("/api/admin/events/<int:event_id>")
@admin_required
def api_delete_event(event_id):
    with get_db() as db:
        event = db.execute("SELECT id FROM events WHERE id = ?", (event_id,)).fetchone()
        if not event:
            return jsonify({"error": "Event not found."}), 404
        db.execute("DELETE FROM events WHERE id = ?", (event_id,))
    return jsonify({"message": "Event deleted."})


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


# Initialise at import time so this also works when served by Gunicorn.
init_db()

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1", host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
