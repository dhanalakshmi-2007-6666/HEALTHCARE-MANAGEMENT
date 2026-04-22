from flask import Blueprint, redirect, render_template, request, session, url_for

from auth_utils import role_required
from models.pharmacy import (
    add_or_update_medicine,
    add_prescription,
    complete_prescription,
    get_low_stock_medicines,
    list_medicines,
    list_prescriptions,
    medicine_exists,
    patient_exists,
)

pharmacy_bp = Blueprint("pharmacy", __name__, url_prefix="/pharmacy")


@pharmacy_bp.route("/", methods=["GET", "POST"])
@role_required(["Admin", "Doctor", "Pharmacist"])
def pharmacy_page():
    message = request.args.get("message")
    message_type = request.args.get("message_type", "info")

    if request.method == "POST":
        action = request.form.get("action", "").strip()

        if action == "save_medicine":
            if session.get("role") not in {"Admin", "Pharmacist"}:
                return redirect(
                    url_for(
                        "pharmacy.pharmacy_page",
                        message="Only admin/pharmacist can manage inventory.",
                        message_type="error",
                    )
                )
            medicine_name = request.form.get("medicine_name", "").strip()
            stock_qty = request.form.get("stock_qty", "").strip()
            unit_price = request.form.get("unit_price", "").strip()
            low_stock_threshold = request.form.get("low_stock_threshold", "").strip()

            if not all([medicine_name, stock_qty, unit_price, low_stock_threshold]):
                return redirect(
                    url_for(
                        "pharmacy.pharmacy_page",
                        message="Please fill all medicine fields.",
                        message_type="error",
                    )
                )
            if not stock_qty.isdigit() or int(stock_qty) < 0:
                return redirect(url_for("pharmacy.pharmacy_page", message="Stock must be a non-negative number.", message_type="error"))
            try:
                float(unit_price)
            except ValueError:
                return redirect(url_for("pharmacy.pharmacy_page", message="Unit price must be numeric.", message_type="error"))
            if not low_stock_threshold.isdigit() or int(low_stock_threshold) < 0:
                return redirect(url_for("pharmacy.pharmacy_page", message="Low stock threshold must be non-negative.", message_type="error"))

            add_or_update_medicine(medicine_name, int(stock_qty), float(unit_price), int(low_stock_threshold))
            return redirect(url_for("pharmacy.pharmacy_page", message="Medicine saved successfully.", message_type="success"))

        if action == "add_prescription":
            if session.get("role") not in {"Doctor", "Admin"}:
                return redirect(url_for("pharmacy.pharmacy_page", message="Only doctor/admin can create prescriptions.", message_type="error"))

            patient_id = request.form.get("patient_id", "").strip().upper()
            medicine_name = request.form.get("medicine_name", "").strip()
            quantity = request.form.get("quantity", "").strip()
            notes = request.form.get("notes", "").strip()

            if not all([patient_id, medicine_name, quantity, notes]):
                return redirect(url_for("pharmacy.pharmacy_page", message="Please fill all prescription fields.", message_type="error"))
            if not patient_exists(patient_id):
                return redirect(url_for("pharmacy.pharmacy_page", message=f"Patient ID {patient_id} not found.", message_type="error"))
            if not medicine_exists(medicine_name):
                return redirect(url_for("pharmacy.pharmacy_page", message=f"Medicine {medicine_name} not found.", message_type="error"))
            if not quantity.isdigit() or int(quantity) <= 0:
                return redirect(url_for("pharmacy.pharmacy_page", message="Quantity must be a positive number.", message_type="error"))

            add_prescription(
                patient_id=patient_id,
                doctor_username=session.get("username", "doctor"),
                medicine_name=medicine_name,
                quantity=int(quantity),
                notes=notes,
            )
            return redirect(url_for("pharmacy.pharmacy_page", message="Prescription created successfully.", message_type="success"))

        if action == "complete_prescription":
            if session.get("role") not in {"Pharmacist", "Admin"}:
                return redirect(url_for("pharmacy.pharmacy_page", message="Only pharmacist/admin can complete prescriptions.", message_type="error"))
            prescription_id = request.form.get("prescription_id", "").strip()
            if not prescription_id.isdigit():
                return redirect(url_for("pharmacy.pharmacy_page", message="Invalid prescription selected.", message_type="error"))
            ok, response_message = complete_prescription(int(prescription_id), session.get("username", "pharmacist"))
            return redirect(
                url_for(
                    "pharmacy.pharmacy_page",
                    message=response_message,
                    message_type="success" if ok else "error",
                )
            )

    query = request.args.get("q", "").strip()
    medicines = list_medicines(query)
    prescriptions = list_prescriptions(session.get("role"), session.get("username"), query)
    low_stock_medicines = get_low_stock_medicines()

    return render_template(
        "pharmacy.html",
        medicines=medicines,
        prescriptions=prescriptions,
        low_stock_medicines=low_stock_medicines,
        query=query,
        message=message,
        message_type=message_type,
    )
