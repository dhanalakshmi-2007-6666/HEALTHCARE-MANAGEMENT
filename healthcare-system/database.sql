PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS role_permissions (
    role_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    PRIMARY KEY (role_id, permission_id),
    FOREIGN KEY (role_id) REFERENCES roles(id),
    FOREIGN KEY (permission_id) REFERENCES permissions(id)
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    role_id INTEGER NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    otp_code TEXT,
    otp_expiry DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(id)
);

CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_code TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    gender TEXT NOT NULL,
    date_of_birth DATE NOT NULL,
    phone TEXT NOT NULL,
    address TEXT NOT NULL,
    emergency_contact TEXT,
    created_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS medical_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    doctor_id INTEGER NOT NULL,
    diagnosis TEXT NOT NULL,
    treatment_notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (doctor_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS vital_signs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    nurse_id INTEGER NOT NULL,
    blood_pressure TEXT,
    pulse_rate INTEGER,
    temperature REAL,
    spo2 INTEGER,
    notes TEXT,
    recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (nurse_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS lab_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    uploaded_by INTEGER NOT NULL,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (uploaded_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS doctor_availability (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doctor_id INTEGER NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    is_booked INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (doctor_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    doctor_id INTEGER NOT NULL,
    receptionist_id INTEGER,
    availability_id INTEGER,
    status TEXT NOT NULL DEFAULT 'BOOKED',
    notes TEXT,
    confirmation_log TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (doctor_id) REFERENCES users(id),
    FOREIGN KEY (receptionist_id) REFERENCES users(id),
    FOREIGN KEY (availability_id) REFERENCES doctor_availability(id)
);

CREATE TABLE IF NOT EXISTS medicines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    sku TEXT UNIQUE NOT NULL,
    stock_qty INTEGER NOT NULL DEFAULT 0,
    low_stock_threshold INTEGER NOT NULL DEFAULT 10,
    unit_price REAL NOT NULL DEFAULT 0,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS prescriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    doctor_id INTEGER NOT NULL,
    pharmacist_id INTEGER,
    status TEXT NOT NULL DEFAULT 'PENDING',
    instructions TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (doctor_id) REFERENCES users(id),
    FOREIGN KEY (pharmacist_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS prescription_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prescription_id INTEGER NOT NULL,
    medicine_id INTEGER NOT NULL,
    dosage TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    FOREIGN KEY (prescription_id) REFERENCES prescriptions(id),
    FOREIGN KEY (medicine_id) REFERENCES medicines(id)
);

CREATE TABLE IF NOT EXISTS pharmacy_bills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prescription_id INTEGER NOT NULL,
    total_amount REAL NOT NULL,
    billed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (prescription_id) REFERENCES prescriptions(id)
);

CREATE TABLE IF NOT EXISTS beds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ward TEXT NOT NULL,
    bed_number TEXT UNIQUE NOT NULL,
    is_occupied INTEGER NOT NULL DEFAULT 0,
    daily_charge REAL NOT NULL DEFAULT 1200
);

CREATE TABLE IF NOT EXISTS admissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    admitted_by INTEGER NOT NULL,
    attending_doctor INTEGER,
    bed_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'ADMITTED',
    admission_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    discharge_date DATETIME,
    discharge_summary TEXT,
    room_charges REAL NOT NULL DEFAULT 0,
    total_billing REAL NOT NULL DEFAULT 0,
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (admitted_by) REFERENCES users(id),
    FOREIGN KEY (attending_doctor) REFERENCES users(id),
    FOREIGN KEY (bed_id) REFERENCES beds(id)
);

INSERT INTO permissions (name) VALUES
('manage_users'), ('manage_roles'), ('manage_patients'), ('book_appointments'), ('manage_inventory'), ('manage_admissions');

INSERT INTO roles (name, description) VALUES
('Admin', 'System administrator'),
('Doctor', 'Treats patients'),
('Nurse', 'Monitors vitals and nursing care'),
('Pharmacist', 'Manages medicine dispensing'),
('Receptionist', 'Handles front desk and booking'),
('Patient', 'Patient portal user');

INSERT INTO beds (ward, bed_number, is_occupied, daily_charge) VALUES
('A', 'A-01', 0, 1200), ('A', 'A-02', 0, 1200), ('B', 'B-01', 0, 1800), ('ICU', 'ICU-01', 0, 3500);
