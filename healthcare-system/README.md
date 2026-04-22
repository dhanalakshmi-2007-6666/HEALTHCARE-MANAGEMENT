# Hospital Management System (Flask + SQLite)

Production-style modular HMS with IAM, patient records, appointments, pharmacy, and admission/bed management.

## Features Included

- Session-based authentication with registration, login, logout, profile update
- OTP-simulated password reset
- RBAC decorators and role-based route protection
- Admin user management: role assignment and user deactivation
- Patient registration, search, diagnosis records, vitals updates, lab report uploads
- Appointment slot creation, booking, cancellation/rescheduling, doctor daily schedule
- Digital prescriptions, pharmacist completion flow, inventory + low-stock alerts, sales report API
- Patient admissions, bed transfer/discharge, room billing calculation

## Project Structure

```text
healthcare-system/
├── app.py
├── config.py
├── requirements.txt
├── database.sql
├── models/
├── routes/
├── templates/
└── static/
```

## Setup

1. Create and activate virtual environment:
   - Windows PowerShell:
     - `python -m venv .venv`
     - `.venv\Scripts\Activate.ps1`
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Initialize DB with seed data:
   - `flask --app app init-db`
4. Run:
   - `python app.py`
5. Open:
   - [http://127.0.0.1:5000](http://127.0.0.1:5000)

## Demo Login Accounts

All seeded users use password: `Pass@123`

- `admin@hms.local`
- `doctor@hms.local`
- `nurse@hms.local`
- `pharmacist@hms.local`
- `reception@hms.local`
- `patient@hms.local`

## API Endpoints (Sample)

- `GET /patients/api/<patient_id>/history`
- `GET /appointments/api/available-slots`
- `GET /pharmacy/api/sales-report`
