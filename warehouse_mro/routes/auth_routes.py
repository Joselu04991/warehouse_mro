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
from datetime import datetime
import os
from werkzeug.utils import secure_filename

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


# ============================================================
# 🔐 LOGIN SIMPLE (SIN BLOQUEO, SIN 2FA, SIN VERIFICACIÓN)
# ============================================================
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username").strip()
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()

        if not user or not user.check_password(password):
            flash("Usuario o contraseña incorrectos.", "danger")
            return redirect(url_for("auth.login"))

        # Login normal
        user.last_login = datetime.utcnow()
        db.session.commit()
        login_user(user)
        flash("Bienvenido.", "success")
        return redirect(url_for("dashboard.dashboard"))

    return render_template("auth/login.html")


# ============================================================
# 📝 REGISTRO SIMPLE (SIN CONFIRMAR CORREO)
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

        if User.query.filter_by(username=username).first():
            flash("Ese usuario ya existe.", "danger")
            return redirect(url_for("auth.register"))

        if User.query.filter_by(email=email).first():
            flash("Ese correo ya está registrado.", "danger")
            return redirect(url_for("auth.register"))

        nuevo = User(
            username=username,
            email=email,
            role="user",
            status="active"
        )
        nuevo.set_password(password)

        db.session.add(nuevo)
        db.session.commit()

        flash("Cuenta creada. Ahora inicia sesión.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


# ============================================================
# 🚪 LOGOUT
# ============================================================
@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Sesión cerrada.", "info")
    return redirect(url_for("auth.login"))


# ============================================================
# 👤 PERFIL
# ============================================================
@auth_bp.route("/perfil")
@login_required
def perfil_usuario():
    return render_template("perfil_usuario.html")


# ============================================================
# ✏ EDITAR PERFIL
# ============================================================
@auth_bp.route("/editar", methods=["GET", "POST"])
@login_required
def edit_user():
    if request.method == "POST":
        current_user.email = request.form.get("email")
        current_user.phone = request.form.get("phone")
        current_user.location = request.form.get("location")
        current_user.area = request.form.get("area")

        db.session.commit()

        flash("Cambios guardados.", "success")
        return redirect(url_for("auth.perfil_usuario"))

    return render_template("auth/edit_user.html")


# ============================================================
# 🔑 CAMBIAR CONTRASEÑA SIMPLE
# ============================================================
@auth_bp.route("/cambiar-password", methods=["GET", "POST"])
@login_required
def cambiar_password():
    if request.method == "POST":
        actual = request.form.get("current_password")
        nueva = request.form.get("new_password")
        confirmar = request.form.get("confirm_password")

        if not current_user.check_password(actual):
            flash("La contraseña actual es incorrecta.", "danger")
            return redirect(url_for("auth.cambiar_password"))

        if nueva != confirmar:
            flash("La confirmación no coincide.", "danger")
            return redirect(url_for("auth.cambiar_password"))

        current_user.set_password(nueva)
        db.session.commit()

        flash("Contraseña actualizada.", "success")
        return redirect(url_for("auth.perfil_usuario"))

    return render_template("auth/change_password.html")


# ============================================================
# 🖼 SUBIR FOTO
# ============================================================
@auth_bp.route("/subir-foto", methods=["GET", "POST"])
@login_required
def subir_foto():
    upload_folder = os.path.join(current_app.root_path, "static", "uploads", "users")
    os.makedirs(upload_folder, exist_ok=True)

    if request.method == "POST":
        file = request.files.get("photo")

        if not file:
            flash("No enviaste ninguna imagen.", "danger")
            return redirect(url_for("auth.subir_foto"))

        ext = file.filename.rsplit(".", 1)[-1].lower()
        if ext not in ["jpg", "jpeg", "png"]:
            flash("Formato no válido.", "danger")
            return redirect(url_for("auth.subir_foto"))

        filename = f"user_{current_user.id}.{ext}"
        path = os.path.join(upload_folder, filename)
        file.save(path)

        current_user.photo = f"uploads/users/{filename}"
        db.session.commit()

        flash("Foto actualizada.", "success")
        return redirect(url_for("auth.perfil_usuario"))

    return render_template("auth/upload_photo.html")


# ============================================================
# 📄 REPORTES PDF (MANTENIDOS TAL CUAL)
# ============================================================
@auth_bp.route("/reportes")
@login_required
def reportes_usuario():
    return render_template("auth/reportes_usuario.html")


# ============================================================
# 📄 PDF 1 - GERENCIA
# ============================================================
@auth_bp.route("/descargar-datos")
@login_required
def descargar_datos_gerencia():
    from datetime import datetime
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter

    reports_folder = os.path.join(current_app.root_path, "static", "reports")
    os.makedirs(reports_folder, exist_ok=True)

    pdf_path = os.path.join(reports_folder, f"perfil_usuario_{current_user.id}.pdf")

    c = canvas.Canvas(pdf_path, pagesize=letter)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(40, 750, "Reporte de Usuario – Nivel Gerencia")
    c.setFont("Helvetica", 12)
    c.drawString(40, 720, f"Usuario: {current_user.username}")
    c.drawString(40, 700, f"Correo: {current_user.email}")
    c.drawString(40, 680, f"Fecha: {datetime.utcnow()}")

    c.save()
    return send_file(pdf_path, as_attachment=True)
