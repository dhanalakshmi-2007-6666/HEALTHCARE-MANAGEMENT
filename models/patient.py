import sqlite3
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "hospital.db"


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_patient_table():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                gender TEXT NOT NULL,
                phone TEXT NOT NULL,
                address TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def generate_patient_id():
    year = datetime.now().year
    prefix = f"PAT{year}"
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT patient_id
            FROM patients
            WHERE patient_id LIKE ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (f"{prefix}%",),
        ).fetchone()

        if row is None:
            return f"{prefix}001"

        last_id = row["patient_id"]
        serial = int(last_id[-3:]) + 1
        return f"{prefix}{serial:03d}"


def create_patient(name, age, gender, phone, address):
    patient_id = generate_patient_id()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO patients (patient_id, name, age, gender, phone, address, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                patient_id,
                name.strip(),
                int(age),
                gender.strip(),
                phone.strip(),
                address.strip(),
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        conn.commit()
    return patient_id


def search_patients(search_term):
    with get_connection() as conn:
        if search_term:
            term = f"%{search_term.strip()}%"
            rows = conn.execute(
                """
                SELECT id, patient_id, name, age, gender, phone, address, created_at
                FROM patients
                WHERE patient_id LIKE ? OR name LIKE ?
                ORDER BY id DESC
                """,
                (term, term),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, patient_id, name, age, gender, phone, address, created_at
                FROM patients
                ORDER BY id DESC
                """
            ).fetchall()
    return rows


def get_total_patients():
    with get_connection() as conn:
        row = conn.execute("SELECT COUNT(*) AS total FROM patients").fetchone()
    return row["total"] if row else 0
