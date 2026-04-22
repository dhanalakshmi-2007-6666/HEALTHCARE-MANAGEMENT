import sqlite3
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "hospital.db"


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_pharmacy_tables():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS medicines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                medicine_name TEXT UNIQUE NOT NULL,
                stock_qty INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                low_stock_threshold INTEGER NOT NULL DEFAULT 10,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS prescriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT NOT NULL,
                doctor_username TEXT NOT NULL,
                medicine_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                notes TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'PENDING',
                completed_by TEXT,
                created_at TEXT NOT NULL,
                completed_at TEXT,
                FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
            )
            """
        )
        conn.commit()


def add_or_update_medicine(medicine_name, stock_qty, unit_price, low_stock_threshold):
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT id FROM medicines WHERE medicine_name = ?",
            (medicine_name.strip(),),
        ).fetchone()
        if existing:
            conn.execute(
                """
                UPDATE medicines
                SET stock_qty = ?, unit_price = ?, low_stock_threshold = ?
                WHERE medicine_name = ?
                """,
                (
                    int(stock_qty),
                    float(unit_price),
                    int(low_stock_threshold),
                    medicine_name.strip(),
                ),
            )
        else:
            conn.execute(
                """
                INSERT INTO medicines (medicine_name, stock_qty, unit_price, low_stock_threshold, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    medicine_name.strip(),
                    int(stock_qty),
                    float(unit_price),
                    int(low_stock_threshold),
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )
        conn.commit()


def list_medicines(search_term=""):
    with get_connection() as conn:
        if search_term:
            term = f"%{search_term.strip()}%"
            rows = conn.execute(
                """
                SELECT id, medicine_name, stock_qty, unit_price, low_stock_threshold, created_at
                FROM medicines
                WHERE medicine_name LIKE ?
                ORDER BY medicine_name ASC
                """,
                (term,),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, medicine_name, stock_qty, unit_price, low_stock_threshold, created_at
                FROM medicines
                ORDER BY medicine_name ASC
                """
            ).fetchall()
    return rows


def get_low_stock_medicines():
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, medicine_name, stock_qty, low_stock_threshold
            FROM medicines
            WHERE stock_qty <= low_stock_threshold
            ORDER BY stock_qty ASC
            """
        ).fetchall()
    return rows


def patient_exists(patient_id):
    with get_connection() as conn:
        row = conn.execute("SELECT patient_id FROM patients WHERE patient_id = ?", (patient_id,)).fetchone()
    return row is not None


def medicine_exists(medicine_name):
    with get_connection() as conn:
        row = conn.execute("SELECT medicine_name FROM medicines WHERE medicine_name = ?", (medicine_name,)).fetchone()
    return row is not None


def add_prescription(patient_id, doctor_username, medicine_name, quantity, notes):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO prescriptions (
                patient_id, doctor_username, medicine_name, quantity, notes, status, created_at
            )
            VALUES (?, ?, ?, ?, ?, 'PENDING', ?)
            """,
            (
                patient_id.strip().upper(),
                doctor_username.strip(),
                medicine_name.strip(),
                int(quantity),
                notes.strip(),
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        conn.commit()


def list_prescriptions(role, username, search_term=""):
    with get_connection() as conn:
        base_query = """
            SELECT id, patient_id, doctor_username, medicine_name, quantity, notes, status, completed_by, created_at, completed_at
            FROM prescriptions
            WHERE 1 = 1
        """
        params = []

        if role == "Doctor":
            base_query += " AND doctor_username = ?"
            params.append(username)

        if search_term:
            term = f"%{search_term.strip()}%"
            base_query += " AND (patient_id LIKE ? OR medicine_name LIKE ?)"
            params.extend([term, term])

        base_query += " ORDER BY id DESC"
        rows = conn.execute(base_query, params).fetchall()
    return rows


def complete_prescription(prescription_id, pharmacist_username):
    with get_connection() as conn:
        prescription = conn.execute(
            """
            SELECT id, medicine_name, quantity, status
            FROM prescriptions
            WHERE id = ?
            """,
            (int(prescription_id),),
        ).fetchone()
        if not prescription:
            return False, "Prescription not found."
        if prescription["status"] == "COMPLETED":
            return False, "Prescription already completed."

        medicine = conn.execute(
            "SELECT stock_qty FROM medicines WHERE medicine_name = ?",
            (prescription["medicine_name"],),
        ).fetchone()
        if not medicine:
            return False, "Medicine not found in inventory."
        if medicine["stock_qty"] < prescription["quantity"]:
            return False, "Insufficient stock to complete this prescription."

        new_stock = medicine["stock_qty"] - prescription["quantity"]
        conn.execute(
            "UPDATE medicines SET stock_qty = ? WHERE medicine_name = ?",
            (new_stock, prescription["medicine_name"]),
        )
        conn.execute(
            """
            UPDATE prescriptions
            SET status = 'COMPLETED', completed_by = ?, completed_at = ?
            WHERE id = ?
            """,
            (
                pharmacist_username.strip(),
                datetime.now().isoformat(timespec="seconds"),
                int(prescription_id),
            ),
        )
        conn.commit()
    return True, "Prescription marked as completed."


def get_low_stock_count():
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS total FROM medicines WHERE stock_qty <= low_stock_threshold"
        ).fetchone()
    return row["total"] if row else 0
