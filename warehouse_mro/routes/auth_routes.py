from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user
from models import db
from models.user import User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

# -----------------------------
# LOGIN
# -----------------------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("dashboard.dashboard"))
        else:
            flash("Usuario o contraseña incorrectos", "danger")

    return render_template("auth/login.html")


# -----------------------------
# LOGOUT (SIN login_required)
# -----------------------------
@auth_bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("auth.login"))


# -----------------------------
# REGISTRO (solo OWNER)
# -----------------------------
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if not current_user.is_authenticated or current_user.role != "owner":
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = request.form["role"]

        if User.query.filter_by(username=username).first():
            flash("El usuario ya existe.", "danger")
            return redirect(url_for("auth.register"))

        nuevo = User(username=username, role=role)
        nuevo.set_password(password)

        db.session.add(nuevo)
        db.session.commit()

        flash("Usuario registrado correctamente.", "success")
        return redirect(url_for("auth.register"))

    return render_template("auth/register.html")
