from datetime import datetime

from flask import Blueprint, current_app, redirect, render_template, request, session, url_for

from auth_utils import role_required
from models.appointment import (
    book_appointment,
    list_appointments,
    patient_exists,
    update_appointment_status,
)

appointment_bp = Blueprint("appointment", __name__, url_prefix="/appointments")


@appointment_bp.route("/", methods=["GET", "POST"])
@role_required(["Admin", "Doctor", "Receptionist"])
def appointments_page():
    message = request.args.get("message")
    message_type = request.args.get("message_type", "info")

    if request.method == "POST":
        action = request.form.get("action", "").strip()
        if action == "book":
            if session.get("role") not in {"Receptionist", "Admin"}:
                return redirect(
                    url_for(
                        "appointment.appointments_page",
                        message="Only receptionist/admin can book appointments.",
                        message_type="error",
                    )
                )

            patient_id = request.form.get("patient_id", "").strip().upper()
            doctor_username = request.form.get("doctor_username", "").strip()
            appointment_date = request.form.get("appointment_date", "").strip()
            appointment_time = request.form.get("appointment_time", "").strip()
            notes = request.form.get("notes", "").strip()

            if not all([patient_id, doctor_username, appointment_date, appointment_time]):
                return redirect(
                    url_for(
                        "appointment.appointments_page",
                        message="Please fill all required appointment fields.",
                        message_type="error",
                    )
                )

            if not patient_exists(patient_id):
                return redirect(
                    url_for(
                        "appointment.appointments_page",
                        message=f"Patient ID {patient_id} not found.",
                        message_type="error",
                    )
                )

            try:
                datetime.strptime(appointment_date, "%Y-%m-%d")
                datetime.strptime(appointment_time, "%H:%M")
            except ValueError:
                return redirect(
                    url_for(
                        "appointment.appointments_page",
                        message="Invalid date or time format.",
                        message_type="error",
                    )
                )

            book_appointment(
                patient_id=patient_id,
                doctor_username=doctor_username,
                receptionist_username=session.get("username", "system"),
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                notes=notes,
            )
            return redirect(
                url_for(
                    "appointment.appointments_page",
                    message="Appointment booked successfully.",
                    message_type="success",
                )
            )

        if action in {"cancel", "reschedule"}:
            if session.get("role") not in {"Receptionist", "Admin"}:
                return redirect(
                    url_for(
                        "appointment.appointments_page",
                        message="Only receptionist/admin can modify appointments.",
                        message_type="error",
                    )
                )

            appointment_id = request.form.get("appointment_id", "").strip()
            if not appointment_id.isdigit():
                return redirect(
                    url_for(
                        "appointment.appointments_page",
                        message="Invalid appointment selected.",
                        message_type="error",
                    )
                )

            if action == "cancel":
                update_appointment_status(appointment_id, "CANCELLED")
                return redirect(
                    url_for(
                        "appointment.appointments_page",
                        message="Appointment cancelled.",
                        message_type="success",
                    )
                )

            new_date = request.form.get("new_date", "").strip()
            new_time = request.form.get("new_time", "").strip()
            if not new_date or not new_time:
                return redirect(
                    url_for(
                        "appointment.appointments_page",
                        message="Provide new date and time for reschedule.",
                        message_type="error",
                    )
                )
            update_appointment_status(appointment_id, "RESCHEDULED", new_date, new_time)
            return redirect(
                url_for(
                    "appointment.appointments_page",
                    message="Appointment rescheduled.",
                    message_type="success",
                )
            )

    users_store = current_app.config.get("USERS_STORE", {})
    doctors = [username for username, data in users_store.items() if data.get("role") == "Doctor"]
    query = request.args.get("q", "").strip()
    appointments = list_appointments(session.get("role"), session.get("username"), query)

    return render_template(
        "appointments.html",
        appointments=appointments,
        doctors=doctors,
        query=query,
        message=message,
        message_type=message_type,
    )
