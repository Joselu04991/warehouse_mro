# routes/admin_roles_routes.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models.user import User
from models import db

admin_roles_bp = Blueprint("admin_roles", __name__, url_prefix="/roles")


# ===========================
#  VALIDACIÓN: SOLO OWNER
# ===========================
def solo_owner():
    return current_user.is_authenticated and current_user.role == "owner"


# ===========================
#  LISTAR USUARIOS Y ROLES
# ===========================
@admin_roles_bp.route("/listar")
@login_required
def listar_roles():
    if not solo_owner():
        flash("No tienes permiso para gestionar roles.", "danger")
        return redirect(url_for("dashboard.dashboard"))

    usuarios = User.query.all()
    return render_template("roles/listar.html", usuarios=usuarios)


# ===========================
#  CAMBIAR ROL DE USUARIO
# ===========================
@admin_roles_bp.route("/cambiar/<int:user_id>", methods=["POST"])
@login_required
def cambiar_rol(user_id):
    if not solo_owner():
        flash("Acceso denegado.", "danger")
        return redirect(url_for("admin_roles.listar_roles"))

    nuevo_rol = request.form.get("rol")

    # Validar rol
    if nuevo_rol not in ["owner", "admin", "user"]:
        flash("Rol inválido.", "warning")
        return redirect(url_for("admin_roles.listar_roles"))

    usuario = User.query.get(user_id)

    if not usuario:
        flash("Usuario no encontrado.", "danger")
        return redirect(url_for("admin_roles.listar_roles"))

    # Evitar que el owner se quite su propio rol
    if usuario.id == current_user.id and nuevo_rol != "owner":
        flash("No puedes quitarte tu propio rol de OWNER.", "danger")
        return redirect(url_for("admin_roles.listar_roles"))

    # Guardar cambio
    usuario.role = nuevo_rol
    db.session.commit()

    flash(f"Rol actualizado a {nuevo_rol.upper()} correctamente.", "success")
    return redirect(url_for("admin_roles.listar_roles"))
