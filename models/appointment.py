import sqlite3
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "hospital.db"


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_appointment_table():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT NOT NULL,
                doctor_username TEXT NOT NULL,
                receptionist_username TEXT NOT NULL,
                appointment_date TEXT NOT NULL,
                appointment_time TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'BOOKED',
                notes TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
            )
            """
        )
        conn.commit()


def patient_exists(patient_id):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT patient_id FROM patients WHERE patient_id = ?",
            (patient_id,),
        ).fetchone()
    return row is not None


def book_appointment(patient_id, doctor_username, receptionist_username, appointment_date, appointment_time, notes):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO appointments (
                patient_id,
                doctor_username,
                receptionist_username,
                appointment_date,
                appointment_time,
                status,
                notes,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, 'BOOKED', ?, ?)
            """,
            (
                patient_id.strip(),
                doctor_username.strip(),
                receptionist_username.strip(),
                appointment_date.strip(),
                appointment_time.strip(),
                notes.strip(),
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        conn.commit()


def list_appointments(role, username, search_term=""):
    with get_connection() as conn:
        if role == "Doctor":
            base_query = """
                SELECT id, patient_id, doctor_username, receptionist_username, appointment_date, appointment_time, status, notes, created_at
                FROM appointments
                WHERE doctor_username = ?
            """
            params = [username]
        else:
            base_query = """
                SELECT id, patient_id, doctor_username, receptionist_username, appointment_date, appointment_time, status, notes, created_at
                FROM appointments
                WHERE 1 = 1
            """
            params = []

        if search_term:
            base_query += " AND (patient_id LIKE ? OR doctor_username LIKE ?)"
            term = f"%{search_term.strip()}%"
            params.extend([term, term])

        base_query += " ORDER BY appointment_date DESC, appointment_time DESC, id DESC"
        rows = conn.execute(base_query, params).fetchall()
    return rows


def update_appointment_status(appointment_id, status, new_date=None, new_time=None):
    status = status.upper().strip()
    if status == "RESCHEDULED" and new_date and new_time:
        with get_connection() as conn:
            conn.execute(
                """
                UPDATE appointments
                SET status = ?, appointment_date = ?, appointment_time = ?
                WHERE id = ?
                """,
                (status, new_date.strip(), new_time.strip(), int(appointment_id)),
            )
            conn.commit()
    else:
        with get_connection() as conn:
            conn.execute(
                "UPDATE appointments SET status = ? WHERE id = ?",
                (status, int(appointment_id)),
            )
            conn.commit()


def get_todays_appointments_count():
    today = datetime.now().strftime("%Y-%m-%d")
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS total FROM appointments WHERE appointment_date = ? AND status != 'CANCELLED'",
            (today,),
        ).fetchone()
    return row["total"] if row else 0
