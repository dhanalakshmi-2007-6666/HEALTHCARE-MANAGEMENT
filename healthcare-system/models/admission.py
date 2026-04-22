from datetime import datetime

from extensions import db


class Bed(db.Model):
    __tablename__ = "beds"

    id = db.Column(db.Integer, primary_key=True)
    ward = db.Column(db.String(50), nullable=False)
    bed_number = db.Column(db.String(20), unique=True, nullable=False)
    is_occupied = db.Column(db.Boolean, default=False, nullable=False)
    daily_charge = db.Column(db.Float, default=1200.0, nullable=False)


class Admission(db.Model):
    __tablename__ = "admissions"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    admitted_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    attending_doctor = db.Column(db.Integer, db.ForeignKey("users.id"))
    bed_id = db.Column(db.Integer, db.ForeignKey("beds.id"), nullable=False)
    status = db.Column(db.String(30), default="ADMITTED", nullable=False)
    admission_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    discharge_date = db.Column(db.DateTime)
    discharge_summary = db.Column(db.Text)
    room_charges = db.Column(db.Float, default=0, nullable=False)
    total_billing = db.Column(db.Float, default=0, nullable=False)
