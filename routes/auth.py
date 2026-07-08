import random
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from extensions import db
from models import User

bp = Blueprint("auth", __name__)


def send_reset_code(user):
    code = f"{random.randint(0, 999999):06d}"
    user.reset_code = code
    user.reset_code_expires_at = datetime.utcnow() + timedelta(minutes=15)
    db.session.commit()

    message = f"Your Mining Study Hub password reset code is: {code}"
    flash(f"A password reset code has been sent to {user.email}.", "success")
    return message


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")

        if not username or not email or not password:
            flash("All fields are required.", "error")
        elif password != confirm:
            flash("Passwords do not match.", "error")
        elif len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
        elif User.query.filter_by(username=username).first():
            flash("That username is already taken.", "error")
        elif User.query.filter_by(email=email).first():
            flash("An account with that email already exists.", "error")
        else:
            user = User(username=username, email=email)
            user.set_password(password)
            # first ever user becomes admin automatically
            if User.query.count() == 0:
                user.is_admin = True
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Welcome to Mining Study Hub!", "success")
            return redirect(url_for("main.dashboard"))

    return render_template("register.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter(
            (User.username == identifier) | (User.email == identifier.lower())
        ).first()

        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get("next")
            flash(f"Welcome back, {user.username}!", "success")
            return redirect(next_page or url_for("main.dashboard"))

        flash("Invalid username/email or password.", "error")

    return render_template("login.html")


@bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()

        if user:
            send_reset_code(user)
            return redirect(url_for("auth.reset_password", email=user.email))

        flash("No account was found with that email address.", "error")

    return render_template("forgot_password.html")


@bp.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    email = request.args.get("email", "").strip().lower()
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        code = request.form.get("code", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")

        user = User.query.filter_by(email=email).first()
        if not user:
            flash("No account was found with that email address.", "error")
        elif not user.reset_code or not user.reset_code_expires_at or datetime.utcnow() > user.reset_code_expires_at:
            flash("The reset code is invalid or has expired.", "error")
        elif user.reset_code != code:
            flash("The reset code is incorrect.", "error")
        elif len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
        elif password != confirm:
            flash("Passwords do not match.", "error")
        else:
            user.set_password(password)
            user.reset_code = None
            user.reset_code_expires_at = None
            db.session.commit()
            flash("Your password has been reset successfully.", "success")
            return redirect(url_for("auth.login"))

    return render_template("reset_password.html", email=email)


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.home"))
