import sqlite3
import json
import os
from datetime import datetime

# Path to the sqlite DB file (placed next to this module)
DB_PATH = os.path.join(os.path.dirname(__file__), "appointments.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS appointments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  appointment_id TEXT,
  patient_name TEXT,
  phone_number TEXT,
  preferred_date TEXT,
  preferred_time TEXT,
  reason TEXT,
  user_role TEXT,
  status TEXT DEFAULT 'pending',
  admin_notes TEXT,
  created_at TEXT,
  raw_payload TEXT
);
"""


def init_db():
    """Create DB file and schema if missing."""
    conn = sqlite3.connect(DB_PATH, timeout=30)
    try:
        cur = conn.cursor()
        cur.executescript(_SCHEMA)
        conn.commit()
    finally:
        conn.close()


def insert_appointment(payload: dict) -> int:
    """Insert an appointment payload into the local SQLite DB.

    Returns the rowid of the inserted row.
    Raises exception to caller if something goes wrong.
    """
    init_db()
    conn = sqlite3.connect(DB_PATH, timeout=30)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO appointments
            (appointment_id, patient_name, phone_number, preferred_date, preferred_time, reason, user_role, status, admin_notes, created_at, raw_payload)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.get('appointment_id'),
                payload.get('user_name'),
                payload.get('phone_number'),
                payload.get('preferred_date') or payload.get('date'),
                payload.get('preferred_time') or payload.get('time'),
                payload.get('reason'),
                payload.get('user_role'),
                payload.get('status', 'pending'),
                payload.get('admin_notes', ''),
                payload.get('created_at') or datetime.utcnow().isoformat(),
                json.dumps(payload, default=str)
            )
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()
