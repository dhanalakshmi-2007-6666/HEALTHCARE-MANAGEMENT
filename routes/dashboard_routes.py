from flask import Blueprint, render_template, session, jsonify, current_app, redirect, url_for
from auth_utils import role_required
from models.dashboard import get_stats, get_dashboard_tables

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/dashboard")
def root_dashboard():
    role = session.get("role", "Patient").lower()
    return redirect(url_for(f"dashboard.{role}_dashboard"))

@dashboard_bp.route("/api/dashboard/stats")
def dashboard_stats_api():
    if "username" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    role = session.get("role", "Patient")
    username = session.get("username", "")
    stats = get_stats(role, username, current_app.config["USERS_STORE"])
    
    return jsonify(stats)

@dashboard_bp.route("/dashboard/patient")
@role_required("Patient")
def patient_dashboard():
    return render_dashboard("Patient Dashboard", "View appointments, prescriptions, and health updates.")

@dashboard_bp.route("/dashboard/doctor")
@role_required("Doctor")
def doctor_dashboard():
    return render_dashboard("Doctor Dashboard", "Manage your schedule, review records, and track today's consultation list.")

@dashboard_bp.route("/dashboard/admin")
@role_required("Admin")
def admin_dashboard():
    return render_dashboard("Admin Dashboard", "Monitor hospital operations, metrics, and systems.")

@dashboard_bp.route("/dashboard/nurse")
@role_required("Nurse")
def nurse_dashboard():
    return render_dashboard("Nurse Dashboard", "Support care delivery with updated patient information.")

@dashboard_bp.route("/dashboard/pharmacist")
@role_required("Pharmacist")
def pharmacist_dashboard():
    return render_dashboard("Pharmacist Dashboard", "Manage medicine requests, dispensing status, and inventory level.")

@dashboard_bp.route("/dashboard/receptionist")
@role_required("Receptionist")
def receptionist_dashboard():
    return render_dashboard("Receptionist Dashboard", "Handle bookings, patient check-ins, and front-desk coordination.")

def render_dashboard(title, description):
    role = session.get("role")
    username = session.get("username")
    stats = get_stats(role, username, current_app.config["USERS_STORE"])
    tables = get_dashboard_tables(role, username)
    
    return render_template(
        "dashboard.html",
        dashboard_title=title,
        dashboard_description=description,
        stats=stats,
        tables=tables
    )
