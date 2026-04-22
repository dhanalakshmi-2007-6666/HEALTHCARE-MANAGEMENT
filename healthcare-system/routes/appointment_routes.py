from datetime import datetime

from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for

from extensions import db
from models.appointment import Appointment, DoctorAvailability
from models.patient import Patient
from models.user import Role, User
from routes.auth_helpers import login_required, roles_required

appointment_bp = Blueprint("appointment", __name__, url_prefix="/appointments")


@appointment_bp.route("/", methods=["GET"])
@login_required
def appointment_page():
    doctors = User.query.join(Role, User.role_id == Role.id).filter(Role.name == "Doctor").all()
    availabilities = DoctorAvailability.query.filter_by(is_booked=False).order_by(DoctorAvailability.start_time.asc()).all()
    appointments = Appointment.query.order_by(Appointment.created_at.desc()).limit(20).all()
    return render_template(
        "appointment.html",
        doctors=doctors,
        availabilities=availabilities,
        appointments=appointments,
    )


@appointment_bp.route("/availability", methods=["POST"])
@login_required
@roles_required("Admin", "Doctor")
def create_availability():
    doctor_id = int(request.form.get("doctor_id", session["user_id"]))
    start_time = datetime.strptime(request.form.get("start_time", ""), "%Y-%m-%dT%H:%M")
    end_time = datetime.strptime(request.form.get("end_time", ""), "%Y-%m-%dT%H:%M")
    db.session.add(DoctorAvailability(doctor_id=doctor_id, start_time=start_time, end_time=end_time))
    db.session.commit()
    flash("Availability slot created.", "success")
    return redirect(url_for("appointment.appointment_page"))


@appointment_bp.route("/book", methods=["POST"])
@login_required
@roles_required("Receptionist", "Patient")
def book_appointment():
    availability = DoctorAvailability.query.get_or_404(int(request.form.get("availability_id", "0")))
    patient_id = int(request.form.get("patient_id", "0"))
    Patient.query.get_or_404(patient_id)
    if availability.is_booked:
        flash("Slot already booked.", "danger")
        return redirect(url_for("appointment.appointment_page"))

    appointment = Appointment(
        patient_id=patient_id,
        doctor_id=availability.doctor_id,
        availability_id=availability.id,
        receptionist_id=session["user_id"] if session.get("role") == "Receptionist" else None,
        confirmation_log="SMS/Email simulated: appointment confirmation sent.",
    )
    availability.is_booked = True
    db.session.add(appointment)
    db.session.commit()
    flash("Appointment booked and confirmation simulated.", "success")
    return redirect(url_for("appointment.appointment_page"))


@appointment_bp.route("/<int:appointment_id>/status", methods=["POST"])
@login_required
@roles_required("Receptionist", "Admin")
def update_status(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    action = request.form.get("action", "").upper()
    if action not in {"RESCHEDULED", "CANCELLED"}:
        flash("Invalid action.", "danger")
        return redirect(url_for("appointment.appointment_page"))
    appointment.status = action
    db.session.commit()
    flash(f"Appointment {action.lower()}.", "info")
    return redirect(url_for("appointment.appointment_page"))


@appointment_bp.route("/doctor/daily", methods=["GET"])
@login_required
@roles_required("Doctor")
def doctor_daily_dashboard():
    today = datetime.utcnow().date()
    starts = datetime.combine(today, datetime.min.time())
    ends = datetime.combine(today, datetime.max.time())
    appointments = Appointment.query.filter(
        Appointment.doctor_id == session["user_id"],
        Appointment.created_at >= starts,
        Appointment.created_at <= ends,
    ).all()
    return render_template("doctor_schedule.html", appointments=appointments)


@appointment_bp.route("/api/available-slots", methods=["GET"])
@login_required
def available_slots_api():
    slots = DoctorAvailability.query.filter_by(is_booked=False).all()
    return jsonify(
        [
            {
                "id": slot.id,
                "doctor_id": slot.doctor_id,
                "start_time": slot.start_time.isoformat(),
                "end_time": slot.end_time.isoformat(),
            }
            for slot in slots
        ]
    )
