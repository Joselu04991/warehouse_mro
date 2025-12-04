from flask import Blueprint, render_template, request
from flask_login import login_required
from models import db
from models.equipos import Equipo   # Puedes luego cambiar si usas otros modelos

productividad_bp = Blueprint("productividad", __name__, url_prefix="/productividad")


@productividad_bp.route("/dashboard")
@login_required
def dashboard_productividad():

    # Datos falsos por ahora (para evitar errores)
    prod_labels = ["Excavadora", "Montacarga", "Camión", "Cinta 01"]
    prod_values = [85, 70, 60, 92]

    estado_labels = ["Operativo", "Stand By", "Avería"]
    estado_values = [14, 4, 2]

    detalle_equipos = [
        {
            "codigo": "EQ-001",
            "descripcion": "Excavadora principal",
            "area": "Chancado",
            "productividad": 85,
            "disponibilidad": 92,
            "mtbf": 120,
            "mttr": 2,
            "estado": "Operativo"
        },
        {
            "codigo": "EQ-002",
            "descripcion": "Montacarga",
            "area": "Almacén",
            "productividad": 70,
            "disponibilidad": 88,
            "mtbf": 95,
            "mttr": 3,
            "estado": "Operativo"
        }
    ]

    meses = [
        {"valor": 1, "nombre": "Enero"},
        {"valor": 2, "nombre": "Febrero"},
        {"valor": 3, "nombre": "Marzo"},
        {"valor": 4, "nombre": "Abril"},
        {"valor": 5, "nombre": "Mayo"},
        {"valor": 6, "nombre": "Junio"},
        {"valor": 7, "nombre": "Julio"},
        {"valor": 8, "nombre": "Agosto"},
        {"valor": 9, "nombre": "Setiembre"},
        {"valor": 10, "nombre": "Octubre"},
        {"valor": 11, "nombre": "Noviembre"},
        {"valor": 12, "nombre": "Diciembre"}
    ]

    areas = ["Chancado", "Almacén", "Fundición", "Acería"]

    return render_template(
        "productividad/dashboard.html",
        prod_labels=prod_labels,
        prod_values=prod_values,
        estado_labels=estado_labels,
        estado_values=estado_values,
        detalle_equipos=detalle_equipos,
        meses=meses,
        areas=areas
    )
