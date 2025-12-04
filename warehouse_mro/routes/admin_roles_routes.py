from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models.user import User
from models import db

roles_bp = Blueprint("roles", __name__, url_prefix="/roles")


@roles_bp.before_request
def validar_owner():
    if not current_user.is_authenticated or not current_user.is_owner():
        flash("No tienes permisos para administrar roles.", "danger")
        return redirect(url_for("dashboard.dashboard"))


@roles_bp.route("/")
@login_required
def listar():
    usuarios = User.query.all()
    return render_template("roles/listar.html", usuarios=usuarios)


@roles_bp.route("/cambiar/<int:user_id>", methods=["POST"])
@login_required
def cambiar_rol(user_id):

    user = User.query.get_or_404(user_id)
    nuevo_rol = request.form.get("role")

    # Owner NO puede ser degradado
    if user.is_owner() and user.username != current_user.username:
        flash("No puedes cambiar el rol del OWNER.", "danger")
        return redirect(url_for("roles.listar"))

    # Solo roles permitidos
    if nuevo_rol not in {"user", "admin", "owner"}:
        flash("Rol inválido.", "danger")
        return redirect(url_for("roles.listar"))

    # Evitar que haya 0 owners
    if nuevo_rol != "owner" and user.is_owner() and user.username == current_user.username:
        flash("Debe existir al menos un OWNER.", "danger")
        return redirect(url_for("roles.listar"))

    # Evitar asignar owner a cualquiera
    if nuevo_rol == "owner" and not current_user.is_owner():
        flash("Solo el OWNER puede asignar el rol OWNER.", "danger")
        return redirect(url_for("roles.listar"))

    user.role = nuevo_rol
    db.session.commit()

    flash("Rol actualizado correctamente.", "success")
    return redirect(url_for("roles.listar"))
