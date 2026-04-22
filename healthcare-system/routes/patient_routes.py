import os
import uuid
from datetime import datetime

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, session, url_for
from werkzeug.utils import secure_filename

from extensions import db
from models.patient import LabReport, MedicalRecord, Patient, VitalSign
from routes.auth_helpers import login_required, roles_required

patient_bp = Blueprint("patient", __name__, url_prefix="/patients")


def _generate_patient_code() -> str:
    latest = Patient.query.order_by(Patient.id.desc()).first()
    next_id = 1 if latest is None else latest.id + 1
    return f"PT-{next_id:05d}"


@patient_bp.route("/", methods=["GET"])
@login_required
@roles_required("Admin", "Doctor", "Nurse", "Receptionist")
def list_patients():
    term = request.args.get("q", "").strip()
    query = Patient.query
    if term:
        query = query.filter((Patient.patient_code.contains(term)) | (Patient.full_name.contains(term)))
    patients = query.order_by(Patient.created_at.desc()).all()
    return render_template("patient.html", patients=patients, q=term)


@patient_bp.route("/create", methods=["POST"])
@login_required
@roles_required("Admin", "Receptionist", "Nurse")
def create_patient():
    dob_raw = request.form.get("date_of_birth", "")
    patient = Patient(
        patient_code=_generate_patient_code(),
        full_name=request.form.get("full_name", "").strip(),
        gender=request.form.get("gender", "Other"),
        date_of_birth=datetime.strptime(dob_raw, "%Y-%m-%d").date(),
        phone=request.form.get("phone", "").strip(),
        address=request.form.get("address", "").strip(),
        emergency_contact=request.form.get("emergency_contact", "").strip(),
        created_by=session["user_id"],
    )
    db.session.add(patient)
    db.session.commit()
    flash("Patient registered successfully.", "success")
    return redirect(url_for("patient.list_patients"))


@patient_bp.route("/<int:patient_id>", methods=["GET"])
@login_required
def patient_history(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    return render_template("patient_history.html", patient=patient)


@patient_bp.route("/<int:patient_id>/record", methods=["POST"])
@login_required
@roles_required("Doctor")
def add_record(patient_id):
    record = MedicalRecord(
        patient_id=patient_id,
        doctor_id=session["user_id"],
        diagnosis=request.form.get("diagnosis", "").strip(),
        treatment_notes=request.form.get("treatment_notes", "").strip(),
    )
    db.session.add(record)
    db.session.commit()
    flash("Medical record added.", "success")
    return redirect(url_for("patient.patient_history", patient_id=patient_id))


@patient_bp.route("/<int:patient_id>/vitals", methods=["POST"])
@login_required
@roles_required("Nurse")
def add_vitals(patient_id):
    vitals = VitalSign(
        patient_id=patient_id,
        nurse_id=session["user_id"],
        blood_pressure=request.form.get("blood_pressure", "").strip(),
        pulse_rate=int(request.form.get("pulse_rate", "0") or 0),
        temperature=float(request.form.get("temperature", "0") or 0),
        spo2=int(request.form.get("spo2", "0") or 0),
        notes=request.form.get("notes", "").strip(),
    )
    db.session.add(vitals)
    db.session.commit()
    flash("Vitals updated.", "success")
    return redirect(url_for("patient.patient_history", patient_id=patient_id))


@patient_bp.route("/<int:patient_id>/lab-report", methods=["POST"])
@login_required
@roles_required("Doctor", "Nurse", "Admin")
def upload_report(patient_id):
    report = request.files.get("lab_report")
    if not report or report.filename == "":
        flash("Select a file before upload.", "danger")
        return redirect(url_for("patient.patient_history", patient_id=patient_id))

    clean_name = secure_filename(report.filename)
    unique_name = f"{uuid.uuid4().hex}_{clean_name}"
    relative_path = os.path.join(current_app.config["UPLOAD_FOLDER"], unique_name)
    absolute_path = os.path.join(current_app.root_path, relative_path)
    report.save(absolute_path)

    db.session.add(
        LabReport(
            patient_id=patient_id,
            uploaded_by=session["user_id"],
            file_name=clean_name,
            file_path=relative_path,
        )
    )
    db.session.commit()
    flash("Lab report uploaded.", "success")
    return redirect(url_for("patient.patient_history", patient_id=patient_id))


@patient_bp.route("/api/<int:patient_id>/history", methods=["GET"])
@login_required
def api_patient_history(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    return jsonify(
        {
            "patient_code": patient.patient_code,
            "full_name": patient.full_name,
            "records": [
                {"diagnosis": rec.diagnosis, "created_at": rec.created_at.isoformat()}
                for rec in patient.medical_records
            ],
            "vitals": [
                {
                    "blood_pressure": v.blood_pressure,
                    "temperature": v.temperature,
                    "recorded_at": v.recorded_at.isoformat(),
                }
                for v in patient.vital_signs
            ],
        }
    )
