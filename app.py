from flask import Flask, redirect, render_template, request, session, url_for

from auth_utils import role_required
from models.appointment import get_todays_appointments_count, init_appointment_table
from models.medical_record import get_total_medical_records, init_medical_records_table
from models.patient import get_total_patients, init_patient_table
from models.pharmacy import get_low_stock_count, init_pharmacy_tables
from routes.appointment_routes import appointment_bp
from routes.medical_routes import medical_bp
from routes.pharmacy_routes import pharmacy_bp
from routes.patient_routes import patient_bp
from routes.dashboard_routes import dashboard_bp

app = Flask(__name__)
app.secret_key = "hms-demo-secret-key"
app.register_blueprint(patient_bp)
app.register_blueprint(appointment_bp)
app.register_blueprint(medical_bp)
app.register_blueprint(pharmacy_bp)
app.register_blueprint(dashboard_bp)
init_patient_table()
init_appointment_table()
init_medical_records_table()
init_pharmacy_tables()

users = {}
app.config["USERS_STORE"] = users

ROLE_DASHBOARD_ENDPOINTS = {
    "Admin": "dashboard.admin_dashboard",
    "Doctor": "dashboard.doctor_dashboard",
    "Nurse": "dashboard.nurse_dashboard",
    "Pharmacist": "dashboard.pharmacist_dashboard",
    "Patient": "dashboard.patient_dashboard",
    "Receptionist": "dashboard.receptionist_dashboard",
}


def get_dashboard_route(role):
    return ROLE_DASHBOARD_ENDPOINTS.get(role, "login")


@app.route("/", methods=["GET", "POST"])
def login():
    selected_role = "Patient"
    message = request.args.get("message")
    message_type = request.args.get("message_type", "info")

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        selected_role = request.form.get("role", "Patient")

        if not username or not password:
            message = "Please enter both username and password."
            message_type = "error"
        elif username not in users:
            message = "Account not found. Please create an account first."
            message_type = "error"
        elif users[username]["password"] != password:
            message = "Incorrect password. Please try again."
            message_type = "error"
        elif users[username]["role"] != selected_role:
            message = "Selected role does not match this account."
            message_type = "error"
        else:
            session["username"] = username
            session["full_name"] = users[username]["full_name"]
            session["role"] = users[username]["role"]
            return redirect(url_for(get_dashboard_route(selected_role)))

    return render_template(
        "login.html",
        selected_role=selected_role,
        message=message,
        message_type=message_type,
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    selected_role = "Patient"
    message = None
    message_type = "info"

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()
        selected_role = request.form.get("role", "Patient")

        if not full_name or not username or not password or not confirm_password:
            message = "Please complete all account details."
            message_type = "error"
        elif username in users:
            message = "This username already exists. Please choose another one."
            message_type = "error"
        elif password != confirm_password:
            message = "Passwords do not match."
            message_type = "error"
        else:
            users[username] = {
                "full_name": full_name,
                "password": password,
                "role": selected_role,
            }
            return redirect(
                url_for(
                    "login",
                    message="Account created successfully. Please log in.",
                    message_type="success",
                )
            )

    return render_template(
        "register.html",
        selected_role=selected_role,
        message=message,
        message_type=message_type,
    )


# Dashboard routes moved to dashboard_routes.py


@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        url_for(
            "login",
            message="You have been logged out successfully.",
            message_type="success",
        )
    )


if __name__ == "__main__":
    app.run(debug=True)
