import os

from flask import Flask, redirect, url_for
from werkzeug.security import generate_password_hash

from config import Config
from extensions import db
from models import Bed, Permission, Role, User
from routes import admin_bp, appointment_bp, auth_bp, patient_bp, pharmacy_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    os.makedirs(os.path.join(app.root_path, app.config["UPLOAD_FOLDER"]), exist_ok=True)

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(admin_bp)
    app.register_blueprint(patient_bp)
    app.register_blueprint(appointment_bp)
    app.register_blueprint(pharmacy_bp)

    @app.route("/")
    def home():
        return redirect(url_for("auth.login"))

    @app.cli.command("init-db")
    def init_db():
        db.drop_all()
        db.create_all()
        seed_data()
        print("Database initialized with seed data.")

    with app.app_context():
        db.create_all()
        if not Role.query.first():
            seed_data()

    return app


def seed_data():
    permissions = [
        "manage_users",
        "manage_roles",
        "manage_patients",
        "book_appointments",
        "manage_inventory",
        "manage_admissions",
    ]
    for permission_name in permissions:
        permission = Permission.query.filter_by(name=permission_name).first()
        if not permission:
            db.session.add(Permission(name=permission_name))
    db.session.flush()

    role_map = {
        "Admin": ["manage_users", "manage_roles", "manage_admissions"],
        "Doctor": ["manage_patients"],
        "Nurse": ["manage_patients"],
        "Pharmacist": ["manage_inventory"],
        "Receptionist": ["book_appointments", "manage_admissions"],
        "Patient": [],
    }
    for role_name, perms in role_map.items():
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            role = Role(name=role_name, description=f"{role_name} role")
            db.session.add(role)
            db.session.flush()
        for perm_name in perms:
            permission = Permission.query.filter_by(name=perm_name).first()
            if permission and permission not in role.permissions:
                role.permissions.append(permission)

    demo_users = [
        ("admin@hms.local", "System Admin", "Admin"),
        ("doctor@hms.local", "Dr. Priya Rao", "Doctor"),
        ("nurse@hms.local", "Nurse Anita", "Nurse"),
        ("pharmacist@hms.local", "Pharma Sai", "Pharmacist"),
        ("reception@hms.local", "Reception Joy", "Receptionist"),
        ("patient@hms.local", "Ravi Kumar", "Patient"),
    ]
    for email, full_name, role_name in demo_users:
        if not User.query.filter_by(email=email).first():
            role = Role.query.filter_by(name=role_name).first()
            db.session.add(
                User(
                    email=email,
                    full_name=full_name,
                    role_id=role.id,
                    password_hash=generate_password_hash("Pass@123"),
                    is_active=True,
                )
            )

    for ward, bed_number, charge in [("A", "A-01", 1200), ("A", "A-02", 1200), ("B", "B-01", 1800), ("ICU", "ICU-01", 3500)]:
        if not Bed.query.filter_by(bed_number=bed_number).first():
            db.session.add(Bed(ward=ward, bed_number=bed_number, daily_charge=charge, is_occupied=False))

    db.session.commit()


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
