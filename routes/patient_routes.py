from flask import Blueprint, redirect, render_template, request, url_for

from auth_utils import role_required
from models.patient import create_patient, search_patients

patient_bp = Blueprint("patient", __name__, url_prefix="/patients")


@patient_bp.route("/add", methods=["GET", "POST"])
@role_required(["Admin", "Receptionist", "Nurse"])
def add_patient():
    message = request.args.get("message")
    message_type = request.args.get("message_type", "info")

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        age_raw = request.form.get("age", "").strip()
        gender = request.form.get("gender", "").strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()

        if not all([name, age_raw, gender, phone, address]):
            return render_template(
                "add_patient.html",
                message="Please fill all fields.",
                message_type="error",
            )

        if not age_raw.isdigit() or int(age_raw) <= 0 or int(age_raw) > 120:
            return render_template(
                "add_patient.html",
                message="Age must be a valid number between 1 and 120.",
                message_type="error",
            )

        patient_id = create_patient(name=name, age=int(age_raw), gender=gender, phone=phone, address=address)
        return redirect(
            url_for(
                "patient.add_patient",
                message=f"Patient created successfully with ID: {patient_id}",
                message_type="success",
            )
        )

    return render_template("add_patient.html", message=message, message_type=message_type)


@patient_bp.route("/list", methods=["GET"])
@role_required(["Admin", "Doctor", "Nurse", "Receptionist"])
def patient_list():
    query = request.args.get("q", "").strip()
    patients = search_patients(query)
    return render_template("patient_list.html", patients=patients, query=query)
