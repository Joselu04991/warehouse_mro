from flask import Blueprint, render_template
from flask_login import login_required
from datetime import datetime
from models import db
from models.user import User

auditoria_bp = Blueprint("auditoria", __name__, url_prefix="/auditoria")


@auditoria_bp.route("/vista")
@login_required
def vista_auditoria():

    # Ejemplo: historial básico de auditoría
    logs = [
        {"usuario": "jcasti15", "accion": "Inicio de sesión", "fecha": "2025-12-01 10:31"},
        {"usuario": "admin", "accion": "Modificó inventario", "fecha": "2025-12-01 10:02"},
        {"usuario": "operario2", "accion": "Registró bulto", "fecha": "2025-11-30 17:22"},
    ]

    return render_template("auditoria/vista_auditoria.html", logs=logs)
