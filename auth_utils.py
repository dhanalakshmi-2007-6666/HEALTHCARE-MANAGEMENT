from functools import wraps

from flask import redirect, session, url_for


def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if "username" not in session or "role" not in session:
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    return wrapped_view


def role_required(roles):
    if isinstance(roles, str):
        allowed_roles = {roles}
    else:
        allowed_roles = set(roles)

    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped_view(*args, **kwargs):
            if session.get("role") not in allowed_roles:
                endpoint = {
                    "Admin": "dashboard.admin_dashboard",
                    "Doctor": "dashboard.doctor_dashboard",
                    "Nurse": "dashboard.nurse_dashboard",
                    "Pharmacist": "dashboard.pharmacist_dashboard",
                    "Patient": "dashboard.patient_dashboard",
                    "Receptionist": "dashboard.receptionist_dashboard",
                }.get(session.get("role"), "login")
                return redirect(url_for(endpoint))
            return view_func(*args, **kwargs)

        return wrapped_view

    return decorator
