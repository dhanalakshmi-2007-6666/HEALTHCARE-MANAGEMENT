from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from extensions import db
from models.admission import Admission, Bed
from models.patient import Patient
from models.user import Permission, Role, User
from routes.auth_helpers import login_required, roles_required

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/")
@login_required
def dashboard():
    role = session.get("role")
    cards = {
        "Admin": ["Users", "Beds", "Pharmacy Sales", "Doctor Slots"],
        "Doctor": ["Appointments", "Medical Records", "Prescriptions"],
        "Nurse": ["Vitals", "Ward Monitoring", "Patient History"],
        "Pharmacist": ["Prescriptions Queue", "Inventory", "Billing"],
        "Receptionist": ["Patient Registration", "Appointments", "Admissions"],
        "Patient": ["My Appointments", "My Reports", "Profile"],
    }
    return render_template("dashboard.html", cards=cards.get(role, []), role=role)


@admin_bp.route("/admin/users", methods=["GET", "POST"])
@login_required
@roles_required("Admin")
def manage_users():
    if request.method == "POST":
        user = User.query.get_or_404(int(request.form.get("user_id", "0")))
        role = Role.query.get_or_404(int(request.form.get("role_id", "0")))
        user.role_id = role.id
        user.is_active = request.form.get("is_active", "true") == "true"
        db.session.commit()
        flash("User updated successfully.", "success")
        return redirect(url_for("admin.manage_users"))

    users = User.query.order_by(User.created_at.desc()).all()
    roles = Role.query.order_by(Role.name.asc()).all()
    return render_template("admin_users.html", users=users, roles=roles)


@admin_bp.route("/admin/roles", methods=["POST"])
@login_required
@roles_required("Admin")
def create_role():
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    permission_names = [p.strip() for p in request.form.get("permissions", "").split(",") if p.strip()]

    role = Role(name=name, description=description)
    for permission_name in permission_names:
        permission = Permission.query.filter_by(name=permission_name).first()
        if not permission:
            permission = Permission(name=permission_name)
        role.permissions.append(permission)

    db.session.add(role)
    db.session.commit()
    flash("Role created with permissions.", "success")
    return redirect(url_for("admin.manage_users"))


@admin_bp.route("/admissions", methods=["GET", "POST"])
@login_required
@roles_required("Admin", "Doctor", "Receptionist")
def admissions():
    if request.method == "POST":
        admission = Admission(
            patient_id=int(request.form.get("patient_id", "0")),
            admitted_by=session["user_id"],
            attending_doctor=int(request.form.get("doctor_id", "0") or 0) or None,
            bed_id=int(request.form.get("bed_id", "0")),
        )
        bed = Bed.query.get_or_404(admission.bed_id)
        if bed.is_occupied:
            flash("Selected bed is occupied.", "danger")
            return redirect(url_for("admin.admissions"))
        bed.is_occupied = True
        db.session.add(admission)
        db.session.commit()
        flash("Patient admitted successfully.", "success")
        return redirect(url_for("admin.admissions"))

    admissions_data = Admission.query.order_by(Admission.admission_date.desc()).all()
    beds = Bed.query.order_by(Bed.ward.asc()).all()
    patients = Patient.query.order_by(Patient.full_name.asc()).all()
    doctors = User.query.join(Role, User.role_id == Role.id).filter(Role.name == "Doctor").all()
    return render_template("admission.html", admissions=admissions_data, beds=beds, patients=patients, doctors=doctors)


@admin_bp.route("/admissions/<int:admission_id>/transfer", methods=["POST"])
@login_required
@roles_required("Admin")
def transfer_bed(admission_id):
    admission = Admission.query.get_or_404(admission_id)
    new_bed = Bed.query.get_or_404(int(request.form.get("new_bed_id", "0")))
    old_bed = Bed.query.get(admission.bed_id)
    if new_bed.is_occupied:
        flash("New bed is already occupied.", "danger")
        return redirect(url_for("admin.admissions"))

    if old_bed:
        old_bed.is_occupied = False
    new_bed.is_occupied = True
    admission.bed_id = new_bed.id
    db.session.commit()
    flash("Patient transferred successfully.", "success")
    return redirect(url_for("admin.admissions"))


@admin_bp.route("/admissions/<int:admission_id>/discharge", methods=["POST"])
@login_required
@roles_required("Admin", "Doctor")
def discharge(admission_id):
    admission = Admission.query.get_or_404(admission_id)
    if admission.status == "DISCHARGED":
        flash("Patient already discharged.", "info")
        return redirect(url_for("admin.admissions"))

    admission.discharge_date = datetime.utcnow()
    stay_days = max(1, (admission.discharge_date.date() - admission.admission_date.date()).days)
    bed = Bed.query.get(admission.bed_id)
    room_charges = stay_days * (bed.daily_charge if bed else 0)
    admission.room_charges = room_charges
    admission.total_billing = room_charges
    admission.status = "DISCHARGED"
    admission.discharge_summary = request.form.get("discharge_summary", "").strip()
    if bed:
        bed.is_occupied = False

    db.session.commit()
    flash("Discharge completed and billing calculated.", "success")
    return redirect(url_for("admin.admissions"))
