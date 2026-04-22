import sqlite3
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "hospital.db"

def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection

def get_stats(role, username, users_store):
    stats = {}
    today = datetime.now().strftime("%Y-%m-%d")
    
    with get_connection() as conn:
        # Common Queries
        patients_row = conn.execute("SELECT COUNT(*) AS total FROM patients").fetchone()
        stats["total_patients"] = patients_row["total"] if patients_row else 0
        
        # Total Doctors
        stats["total_doctors"] = sum(1 for u in users_store.values() if u["role"] == "Doctor")
        
        # Today's appointments (All)
        appointments_row = conn.execute("SELECT COUNT(*) AS total FROM appointments WHERE appointment_date = ? AND status != 'CANCELLED'", (today,)).fetchone()
        stats["today_appointments_all"] = appointments_row["total"] if appointments_row else 0
        
        # Today's appointments (Doctor specific)
        if role == 'Doctor':
            doc_app_row = conn.execute("SELECT COUNT(*) AS total FROM appointments WHERE appointment_date = ? AND doctor_username = ? AND status != 'CANCELLED'", (today, username)).fetchone()
            stats["today_appointments_doctor"] = doc_app_row["total"] if doc_app_row else 0
        else:
            stats["today_appointments_doctor"] = 0
            
        # Total Medical Records
        med_row = conn.execute("SELECT COUNT(*) AS total FROM medical_records").fetchone()
        stats["total_medical_records"] = med_row["total"] if med_row else 0
        
        # Low Stock Medicines
        low_stock_row = conn.execute("SELECT COUNT(*) AS total FROM medicines WHERE stock_qty <= low_stock_threshold").fetchone()
        stats["low_stock_medicines"] = low_stock_row["total"] if low_stock_row else 0
        
        # Available Beds (Total beds - Occupied)
        try:
            beds_row = conn.execute("SELECT COUNT(*) AS total FROM beds WHERE is_occupied = 0").fetchone()
            stats["available_beds"] = beds_row["total"] if beds_row else 0
        except sqlite3.OperationalError:
            stats["available_beds"] = 0

        # Pending Prescriptions
        try:
            pres_row = conn.execute("SELECT COUNT(*) AS total FROM prescriptions WHERE status = 'PENDING'").fetchone()
            stats["pending_prescriptions"] = pres_row["total"] if pres_row else 0
        except sqlite3.OperationalError:
            stats["pending_prescriptions"] = 0

    return stats

def get_dashboard_tables(role, username):
    tables = {}
    today = datetime.now().strftime("%Y-%m-%d")
    
    with get_connection() as conn:
        if role == 'Doctor':
            tables['recent_appointments'] = [dict(row) for row in conn.execute("SELECT id, patient_id, appointment_time, status FROM appointments WHERE appointment_date = ? AND doctor_username = ? ORDER BY appointment_time ASC LIMIT 5", (today, username)).fetchall()]
        elif role == 'Admin' or role == 'Receptionist':
            tables['recent_appointments'] = [dict(row) for row in conn.execute("SELECT id, patient_id, doctor_username, appointment_time, status FROM appointments WHERE appointment_date = ? ORDER BY appointment_time ASC LIMIT 5", (today,)).fetchall()]
            tables['recent_patients'] = [dict(row) for row in conn.execute("SELECT patient_id, name, created_at FROM patients ORDER BY id DESC LIMIT 5").fetchall()]
        elif role == 'Pharmacist':
            tables['pending_prescriptions'] = [dict(row) for row in conn.execute("SELECT id, patient_id, medicine_name, quantity FROM prescriptions WHERE status = 'PENDING' ORDER BY id ASC LIMIT 5").fetchall()]
            tables['low_stock_items'] = [dict(row) for row in conn.execute("SELECT medicine_name, stock_qty, low_stock_threshold FROM medicines WHERE stock_qty <= low_stock_threshold LIMIT 5").fetchall()]
            
    return tables
