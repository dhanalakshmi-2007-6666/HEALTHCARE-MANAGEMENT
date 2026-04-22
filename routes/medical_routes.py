import os
from pathlib import Path

from flask import Blueprint, current_app, redirect, render_template, request, session, url_for
from werkzeug.utils import secure_filename

from auth_utils import role_required
from models.medical_record import (
    add_medical_record,
    list_medical_records,
    patient_exists,
)

medical_bp = Blueprint("medical", __name__, url_prefix="/medical-records")


def _save_lab_report(file_obj):
    uploads_dir = Path(current_app.root_path) / "static" / "uploads" / "lab_reports"
    os.makedirs(uploads_dir, exist_ok=True)

    original_name = secure_filename(file_obj.filename)
    unique_name = f"{session.get('username', 'user')}_{original_name}"
    destination = uploads_dir / unique_name
    file_obj.save(destination)
    return f"uploads/lab_reports/{unique_name}"


@medical_bp.route("/", methods=["GET", "POST"])
@role_required(["Admin", "Doctor", "Nurse"])
def medical_records_page():
    message = request.args.get("message")
    message_type = request.args.get("message_type", "info")

    if request.method == "POST":
        if session.get("role") not in {"Doctor", "Admin"}:
            return redirect(
                url_for(
                    "medical.medical_records_page",
                    message="Only doctor/admin can add medical records.",
                    message_type="error",
                )
            )

        patient_id = request.form.get("patient_id", "").strip().upper()
        diagnosis = request.form.get("diagnosis", "").strip()
        prescription_notes = request.form.get("prescription_notes", "").strip()
        lab_report = request.files.get("lab_report")
        lab_report_path = ""

        if not all([patient_id, diagnosis, prescription_notes]):
            return redirect(
                url_for(
                    "medical.medical_records_page",
                    message="Patient ID, diagnosis, and prescription notes are required.",
                    message_type="error",
                )
            )

        if not patient_exists(patient_id):
            return redirect(
                url_for(
                    "medical.medical_records_page",
                    message=f"Patient ID {patient_id} not found.",
                    message_type="error",
                )
            )

        if lab_report and lab_report.filename:
            if not lab_report.filename.lower().endswith(".pdf"):
                return redirect(
                    url_for(
                        "medical.medical_records_page",
                        message="Only PDF files are allowed for lab reports.",
                        message_type="error",
                    )
                )
            lab_report_path = _save_lab_report(lab_report)

        add_medical_record(
            patient_id=patient_id,
            doctor_username=session.get("username", "doctor"),
            diagnosis=diagnosis,
            prescription_notes=prescription_notes,
            lab_report_path=lab_report_path,
        )
        return redirect(
            url_for(
                "medical.medical_records_page",
                message="Medical record added successfully.",
                message_type="success",
            )
        )

    query = request.args.get("q", "").strip()
    records = list_medical_records(session.get("role"), session.get("username"), query)
    return render_template(
        "medical_records.html",
        records=records,
        query=query,
        message=message,
        message_type=message_type,
    )
