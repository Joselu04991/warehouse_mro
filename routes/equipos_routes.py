from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from models import db
from models.equipos import Equipo

equipos_bp = Blueprint("equipos", __name__, url_prefix="/equipos")

# ===========================
# LISTA DE EQUIPOS
# ===========================
@equipos_bp.route("/lista")
@login_required
def lista():
    equipos = Equipo.query.all()
    return render_template("equipos/lista_equipos.html", equipos=equipos)

# ===========================
# NUEVO EQUIPO
# ===========================
@equipos_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo():
    if request.method == "POST":
        codigo = request.form.get("codigo")
        descripcion = request.form.get("descripcion")
        area = request.form.get("area")

        nuevo = Equipo(codigo=codigo, descripcion=descripcion, area=area)
        db.session.add(nuevo)
        db.session.commit()

        flash("Equipo registrado correctamente.", "success")
        return redirect(url_for("equipos.lista"))

    return render_template("equipos/nuevo_equipo.html")

