from functools import wraps

from flask import abort, redirect, session, url_for


def login_required(view_fn):
    @wraps(view_fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return view_fn(*args, **kwargs)

    return wrapper


def roles_required(*allowed_roles):
    def decorator(view_fn):
        @wraps(view_fn)
        def wrapper(*args, **kwargs):
            current_role = session.get("role")
            if current_role not in allowed_roles:
                abort(403, description="Access denied for this role.")
            return view_fn(*args, **kwargs)

        return wrapper

    return decorator
