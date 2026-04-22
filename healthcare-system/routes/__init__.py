from routes.admin_routes import admin_bp
from routes.appointment_routes import appointment_bp
from routes.auth_routes import auth_bp
from routes.patient_routes import patient_bp
from routes.pharmacy_routes import pharmacy_bp

__all__ = ["admin_bp", "appointment_bp", "auth_bp", "patient_bp", "pharmacy_bp"]
