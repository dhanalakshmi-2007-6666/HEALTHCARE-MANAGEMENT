import sqlite3
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "hospital.db"


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_medical_records_table():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS medical_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT NOT NULL,
                doctor_username TEXT NOT NULL,
                diagnosis TEXT NOT NULL,
                prescription_notes TEXT NOT NULL,
                lab_report_path TEXT,
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


def add_medical_record(patient_id, doctor_username, diagnosis, prescription_notes, lab_report_path=""):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO medical_records (
                patient_id,
                doctor_username,
                diagnosis,
                prescription_notes,
                lab_report_path,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                patient_id.strip().upper(),
                doctor_username.strip(),
                diagnosis.strip(),
                prescription_notes.strip(),
                lab_report_path.strip(),
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        conn.commit()


def list_medical_records(role, username, search_term=""):
    with get_connection() as conn:
        base_query = """
            SELECT id, patient_id, doctor_username, diagnosis, prescription_notes, lab_report_path, created_at
            FROM medical_records
            WHERE 1 = 1
        """
        params = []

        if role == "Doctor":
            base_query += " AND doctor_username = ?"
            params.append(username)

        if search_term:
            term = f"%{search_term.strip()}%"
            base_query += " AND (patient_id LIKE ? OR diagnosis LIKE ?)"
            params.extend([term, term])

        base_query += " ORDER BY id DESC"
        rows = conn.execute(base_query, params).fetchall()
    return rows


def get_total_medical_records():
    with get_connection() as conn:
        row = conn.execute("SELECT COUNT(*) AS total FROM medical_records").fetchone()
    return row["total"] if row else 0
