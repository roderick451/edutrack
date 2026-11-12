from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from app import db
from app.forms import LoginForm
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
            login_user(user, remember=True)
            flash("Welcome back!", "success")
            return redirect(url_for("dashboard.index"))
        flash("Invalid username or password.", "error")
    return render_template("login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))


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
