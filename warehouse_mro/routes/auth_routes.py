from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, current_app, send_file, session
)
from flask_login import (
    login_user, logout_user, login_required,
    current_user
)
from models import db
from models.user import User
from datetime import datetime, timedelta
import os
import re
import secrets
import pyotp
from werkzeug.utils import secure_filename
from utils.pdf_report import create_pdf_reporte  


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

# ============================================================
# EXPIRACIÓN DE SESIÓN
# ============================================================
@auth_bp.before_app_request
def verificar_expiracion_sesion():
    if "last_activity" not in session:
        session["last_activity"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        return

    raw_value = session["last_activity"]
    try:
        if "+" in raw_value:
            raw_value = raw_value.split("+")[0]
        last_activity = datetime.strptime(raw_value, "%Y-%m-%d %H:%M:%S")
    except Exception:
        session["last_activity"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        return

    limite = last_activity + timedelta(minutes=30)
    if datetime.utcnow() > limite:
        logout_user()
        session.clear()
        flash("Tu sesión expiró por inactividad.", "warning")
        return redirect(url_for("auth.login"))

    session["last_activity"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


# ============================================================
# VALIDAR CONTRASEÑA
# ============================================================
def validar_password(password):
    reglas = [
        (r".{8,}", "Debe tener al menos 8 caracteres."),
        (r"[A-Z]", "Debe contener mayúsculas."),
        (r"[a-z]", "Debe contener minúsculas."),
        (r"[0-9]", "Debe contener números."),
        (r"[^A-Za-z0-9]", "Debe tener un símbolo.")
    ]
    errores = []
    for reg, msg in reglas:
        if not re.search(reg, password):
            errores.append(msg)
    return errores


# ============================================================
# LOGIN SIN ACTIVACIÓN POR CORREO
# ============================================================
@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        username = request.form.get("username").strip()
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()

        if not user:
            flash("Usuario o contraseña incorrectos.", "danger")
            return redirect(url_for("auth.login"))

        if not user.check_password(password):
            flash("Contraseña incorrecta.", "danger")
            return redirect(url_for("auth.login"))

        # 2FA opcional
        if getattr(user, "twofa_enabled", False):
            session["2fa_user_id"] = user.id
            return redirect(url_for("auth.twofa_verify"))

        # Login normal
        user.last_login = datetime.utcnow()
        db.session.commit()
        login_user(user)

        return redirect(url_for("dashboard.dashboard"))

    return render_template("auth/login.html")


# ============================================================
# 2FA LOGIN
# ============================================================
@auth_bp.route("/2fa-verificar", methods=["GET", "POST"])
def twofa_verify():

    user_id = session.get("2fa_user_id")
    if not user_id:
        flash("No hay sesión pendiente de 2FA.", "warning")
        return redirect(url_for("auth.login"))

    user = User.query.get(user_id)

    if request.method == "POST":
        code = request.form.get("code")
        totp = pyotp.TOTP(user.twofa_secret)
        if totp.verify(code):
            session.pop("2fa_user_id", None)
            login_user(user)
            return redirect(url_for("dashboard.dashboard"))
        else:
            flash("Código incorrecto.", "danger")

    return render_template("auth/2fa_verify.html", user=user)


# ============================================================
# REGISTRO (SIN ACTIVACIÓN POR EMAIL)
# ============================================================
@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        username = request.form.get("username").strip()
        email = request.form.get("email").strip()
        password = request.form.get("password")
        password2 = request.form.get("password2")

        if password != password2:
            flash("Las contraseñas no coinciden.", "danger")
            return redirect(url_for("auth.register"))

        errores = validar_password(password)
        if errores:
            for e in errores:
                flash(e, "danger")
            return redirect(url_for("auth.register"))

        nuevo = User(
            username=username,
            email=email,
            role="user",
            email_confirmed=True  # ACTIVADO DIRECTO
        )
        nuevo.set_password(password)
        db.session.add(nuevo)
        db.session.commit()

        flash("Cuenta creada. Ahora puedes iniciar sesión.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


# ============================================================
# LOGOUT
# ============================================================
@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    flash("Sesión cerrada.", "info")
    return redirect(url_for("auth.login"))


# ============================================================
# PERFIL
# ============================================================
@auth_bp.route("/perfil")
@login_required
def perfil_usuario():
    return render_template("perfil_usuario.html")


# ============================================================
# SUBIR FOTO
# ============================================================
@auth_bp.route("/subir-foto", methods=["GET", "POST"])
@login_required
def subir_foto():

    upload_folder = os.path.join(current_app.root_path, "static", "uploads", "users")
    os.makedirs(upload_folder, exist_ok=True)

    if request.method == "POST":
        file = request.files["photo"]
        ext = file.filename.split(".")[-1].lower()
        filename = f"user_{current_user.id}.{ext}"
        path = os.path.join(upload_folder, filename)
        file.save(path)

        current_user.photo = f"uploads/users/{filename}"
        db.session.commit()

        flash("Foto actualizada.", "success")
        return redirect(url_for("auth.perfil_usuario"))

    return render_template("auth/upload_photo.html")
