from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from app.activity import record_activity
from app import db
from app.forms import AdminSettingsForm, LoginForm
from app.models import User


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember_me.data)
            record_activity("Signed in", "Account", user.username)
            db.session.commit()
            flash("Welcome back!", "success")
            return redirect(url_for("dashboard.index"))
        flash("Invalid username or password.", "error")
    return render_template("login.html", form=form)


@auth_bp.route("/forgot-password")
def forgot_password():
    return render_template("forgot_password.html")


@auth_bp.route("/logout")
@login_required
def logout():
    record_activity("Signed out", "Account", current_user.username)
    db.session.commit()
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    form = AdminSettingsForm(obj=current_user)
    if form.validate_on_submit():
        if not current_user.verify_password(form.current_password.data):
            form.current_password.errors.append("Current password is incorrect.")
            return render_template("settings.html", form=form)

        username = form.username.data.strip()
        email = form.email.data.strip().lower()
        if User.query.filter(User.username == username, User.id != current_user.id).first():
            form.username.errors.append("That username is already in use.")
        if User.query.filter(User.email == email, User.id != current_user.id).first():
            form.email.errors.append("That email address is already in use.")
        if form.username.errors or form.email.errors:
            return render_template("settings.html", form=form)

        password_changed = bool(form.new_password.data)
        current_user.username = username
        current_user.email = email
        if form.new_password.data:
            current_user.password_hash = generate_password_hash(form.new_password.data)
        record_activity(
            "Updated",
            "Account",
            current_user.username,
            "Updated account profile and password." if password_changed else "Updated account profile.",
        )
        db.session.commit()
        flash("Account settings updated successfully.", "success")
        return redirect(url_for("auth.settings"))

    return render_template("settings.html", form=form)


@auth_bp.route("/setup-admin", methods=["GET", "POST"])
def setup_admin():
    if User.query.first() is not None:
        return redirect(url_for("auth.login"))

    form = LoginForm()
    if form.validate_on_submit():
        new_user = User(
            username=form.username.data.strip(),
            email=f"{form.username.data.strip()}@admin.local",
            password_hash=generate_password_hash(form.password.data),
        )
        db.session.add(new_user)
        db.session.commit()
        flash("Admin account created. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("login.html", form=form, setup_mode=True)
