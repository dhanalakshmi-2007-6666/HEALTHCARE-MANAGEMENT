import random
from datetime import datetime, timedelta

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db
from models.user import Role, User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        full_name = request.form.get("full_name", "").strip()
        password = request.form.get("password", "")
        role_name = request.form.get("role", "Patient")

        role = Role.query.filter_by(name=role_name).first()
        if not role:
            flash("Selected role does not exist.", "danger")
            return redirect(url_for("auth.register"))

        if User.query.filter_by(email=email).first():
            flash("Email already in use.", "danger")
            return redirect(url_for("auth.register"))

        user = User(
            email=email,
            full_name=full_name,
            password_hash=generate_password_hash(password),
            role_id=role.id,
        )
        db.session.add(user)
        db.session.commit()
        flash("Registration successful. Please login.", "success")
        return redirect(url_for("auth.login"))

    roles = Role.query.order_by(Role.name.asc()).all()
    return render_template("register.html", roles=roles)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password_hash, password):
            flash("Invalid credentials.", "danger")
            return redirect(url_for("auth.login"))
        if not user.is_active:
            flash("Account is deactivated. Contact admin.", "danger")
            return redirect(url_for("auth.login"))

        session["user_id"] = user.id
        session["email"] = user.email
        session["name"] = user.full_name
        session["role"] = user.role.name

        flash("Logged in successfully.", "success")
        return redirect(url_for("admin.dashboard"))
    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You are now logged out.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/profile", methods=["GET", "POST"])
def profile():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user = User.query.get_or_404(session["user_id"])
    if request.method == "POST":
        user.full_name = request.form.get("full_name", user.full_name).strip()
        db.session.commit()
        session["name"] = user.full_name
        flash("Profile updated.", "success")
        return redirect(url_for("auth.profile"))

    return render_template("profile.html", user=user)


@auth_bp.route("/password-reset", methods=["GET", "POST"])
def password_reset():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()
        if not user:
            flash("No account found for this email.", "danger")
            return redirect(url_for("auth.password_reset"))

        otp = str(random.randint(100000, 999999))
        user.otp_code = otp
        user.otp_expiry = datetime.utcnow() + timedelta(minutes=10)
        db.session.commit()
        flash(f"OTP simulated: {otp} (valid 10 minutes).", "warning")
        return redirect(url_for("auth.verify_otp", email=email))

    return render_template("password_reset.html")


@auth_bp.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():
    email = request.args.get("email", "").strip().lower()
    user = User.query.filter_by(email=email).first()
    if not user:
        flash("Invalid reset request.", "danger")
        return redirect(url_for("auth.password_reset"))

    if request.method == "POST":
        otp = request.form.get("otp", "").strip()
        new_password = request.form.get("new_password", "")
        if user.otp_code != otp or not user.otp_expiry or datetime.utcnow() > user.otp_expiry:
            flash("Invalid or expired OTP.", "danger")
            return redirect(url_for("auth.verify_otp", email=email))

        user.password_hash = generate_password_hash(new_password)
        user.otp_code = None
        user.otp_expiry = None
        db.session.commit()
        flash("Password changed successfully.", "success")
        return redirect(url_for("auth.login"))

    return render_template("verify_otp.html", email=email)
