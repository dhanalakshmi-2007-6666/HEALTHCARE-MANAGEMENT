from datetime import datetime

from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for

from extensions import db
from models.pharmacy import Medicine, PharmacyBill, Prescription, PrescriptionItem
from routes.auth_helpers import login_required, roles_required

pharmacy_bp = Blueprint("pharmacy", __name__, url_prefix="/pharmacy")


@pharmacy_bp.route("/", methods=["GET"])
@login_required
@roles_required("Admin", "Doctor", "Pharmacist")
def pharmacy_dashboard():
    medicines = Medicine.query.order_by(Medicine.name.asc()).all()
    prescriptions = Prescription.query.order_by(Prescription.created_at.desc()).all()
    low_stock = [m for m in medicines if m.stock_qty <= m.low_stock_threshold]
    return render_template(
        "pharmacy.html",
        medicines=medicines,
        prescriptions=prescriptions,
        low_stock=low_stock,
    )


@pharmacy_bp.route("/medicine", methods=["POST"])
@login_required
@roles_required("Admin", "Pharmacist")
def upsert_medicine():
    name = request.form.get("name", "").strip()
    sku = request.form.get("sku", "").strip()
    medicine = Medicine.query.filter((Medicine.sku == sku) | (Medicine.name == name)).first()
    if medicine:
        medicine.stock_qty = int(request.form.get("stock_qty", medicine.stock_qty))
        medicine.unit_price = float(request.form.get("unit_price", medicine.unit_price))
        medicine.low_stock_threshold = int(request.form.get("low_stock_threshold", medicine.low_stock_threshold))
        flash("Medicine updated.", "info")
    else:
        db.session.add(
            Medicine(
                name=name,
                sku=sku,
                stock_qty=int(request.form.get("stock_qty", "0")),
                unit_price=float(request.form.get("unit_price", "0")),
                low_stock_threshold=int(request.form.get("low_stock_threshold", "10")),
            )
        )
        flash("Medicine added.", "success")
    db.session.commit()
    return redirect(url_for("pharmacy.pharmacy_dashboard"))


@pharmacy_bp.route("/prescription", methods=["POST"])
@login_required
@roles_required("Doctor")
def create_prescription():
    prescription = Prescription(
        patient_id=int(request.form.get("patient_id", "0")),
        doctor_id=session["user_id"],
        instructions=request.form.get("instructions", "").strip(),
    )
    db.session.add(prescription)
    db.session.flush()

    medicine_id = int(request.form.get("medicine_id", "0"))
    quantity = int(request.form.get("quantity", "1"))
    dosage = request.form.get("dosage", "1-0-1")
    db.session.add(
        PrescriptionItem(
            prescription_id=prescription.id,
            medicine_id=medicine_id,
            quantity=quantity,
            dosage=dosage,
        )
    )
    db.session.commit()
    flash("Digital prescription created.", "success")
    return redirect(url_for("pharmacy.pharmacy_dashboard"))


@pharmacy_bp.route("/prescription/<int:prescription_id>/complete", methods=["POST"])
@login_required
@roles_required("Pharmacist")
def complete_prescription(prescription_id):
    prescription = Prescription.query.get_or_404(prescription_id)
    if prescription.status == "COMPLETED":
        flash("Prescription already completed.", "info")
        return redirect(url_for("pharmacy.pharmacy_dashboard"))

    total = 0.0
    for item in prescription.items:
        medicine = Medicine.query.get(item.medicine_id)
        if medicine.stock_qty < item.quantity:
            flash(f"Insufficient stock for {medicine.name}.", "danger")
            return redirect(url_for("pharmacy.pharmacy_dashboard"))
        medicine.stock_qty -= item.quantity
        total += medicine.unit_price * item.quantity

    prescription.status = "COMPLETED"
    prescription.pharmacist_id = session["user_id"]
    prescription.completed_at = datetime.utcnow()
    db.session.add(PharmacyBill(prescription_id=prescription.id, total_amount=total))
    db.session.commit()
    flash("Prescription completed and bill generated.", "success")
    return redirect(url_for("pharmacy.pharmacy_dashboard"))


@pharmacy_bp.route("/api/sales-report", methods=["GET"])
@login_required
@roles_required("Admin")
def sales_report_api():
    bills = PharmacyBill.query.order_by(PharmacyBill.billed_at.desc()).all()
    total_sales = sum(b.total_amount for b in bills)
    return jsonify(
        {
            "total_sales": total_sales,
            "bill_count": len(bills),
            "bills": [{"id": b.id, "amount": b.total_amount, "billed_at": b.billed_at.isoformat()} for b in bills],
        }
    )
