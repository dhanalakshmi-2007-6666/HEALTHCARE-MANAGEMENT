PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    age INTEGER NOT NULL CHECK (age > 0 AND age <= 120),
    gender TEXT NOT NULL,
    phone TEXT NOT NULL,
    address TEXT NOT NULL,
    created_at TEXT NOT NULL
);

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
);

CREATE TABLE IF NOT EXISTS medical_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id TEXT NOT NULL,
    doctor_username TEXT NOT NULL,
    diagnosis TEXT NOT NULL,
    prescription_notes TEXT NOT NULL,
    lab_report_path TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
);

CREATE TABLE IF NOT EXISTS medicines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    medicine_name TEXT UNIQUE NOT NULL,
    stock_qty INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    low_stock_threshold INTEGER NOT NULL DEFAULT 10,
    created_at TEXT NOT NULL
);

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
);

CREATE TABLE IF NOT EXISTS beds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ward_name TEXT NOT NULL,
    bed_number TEXT UNIQUE NOT NULL,
    is_occupied BOOLEAN NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS admissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id TEXT NOT NULL,
    bed_id INTEGER NOT NULL,
    admission_date TEXT NOT NULL,
    discharge_date TEXT,
    status TEXT NOT NULL DEFAULT 'ADMITTED',
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY (bed_id) REFERENCES beds(id)
);
