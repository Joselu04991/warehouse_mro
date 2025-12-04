from flask import Blueprint, render_template
from flask_login import login_required
from sqlalchemy import func
from datetime import date

from models.inventory import InventoryItem
from models.bultos import Bulto
from models.alerts import Alert        # ← CORREGIDO
from models.warehouse2d import WarehouseLocation
from models.technician_error import TechnicianError
from models.equipos import Equipo

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@dashboard_bp.route("/", endpoint="dashboard")
@login_required
def dashboard():

    # KPI PRINCIPALES
    total_stock = InventoryItem.query.count()

    bultos_hoy = Bulto.query.filter(
        func.date(Bulto.fecha_hora) == date.today()
    ).count()

    alertas_activas = Alert.query.filter(
        Alert.estado == "activo"
    ).count()

    errores_hoy = TechnicianError.query.filter(
        func.date(TechnicianError.creado_en) == date.today()
    ).count()

    # ESTADOS DEL INVENTARIO
    ubicaciones = WarehouseLocation.query.all()

    criticos = sum(1 for i in ubicaciones if i.status == "crítico")
    bajos = sum(1 for i in ubicaciones if i.status == "bajo")
    normales = sum(1 for i in ubicaciones if i.status == "normal")
    vacios = sum(1 for i in ubicaciones if i.status == "vacío")

    # ALERTAS POR DÍA
    alertas_por_dia = (
        Alert.query.with_entities(
            func.strftime("%w", Alert.fecha),
            func.count(Alert.id)
        )
        .group_by(func.strftime("%w", Alert.fecha))
        .all()
    )

    alertas_dias = [0] * 7
    for dia, cant in alertas_por_dia:
        alertas_dias[int(dia)] = cant

    # BULTOS POR HORA
    bultos_por_hora = (
        Bulto.query.with_entities(
            func.strftime("%H", Bulto.fecha_hora),
            func.count(Bulto.id)
        )
        .group_by(func.strftime("%H", Bulto.fecha_hora))
        .all()
    )

    horas = {str(h).zfill(2): 0 for h in range(6, 18)}
    for h, cant in bultos_por_hora:
        if h in horas:
            horas[h] = cant

    # PRODUCTIVIDAD
    equipos = Equipo.query.all()

    if not equipos:
        prod_labels = []
        prod_values = []
        estado_labels = []
        estado_values = []
    else:
        prod_labels = [e.codigo for e in equipos]
        prod_values = [e.productividad or 0 for e in equipos]

        estados = {}
        for e in equipos:
            estado = e.estado or "Sin estado"
            estados[estado] = estados.get(estado, 0) + 1

        estado_labels = list(estados.keys())
        estado_values = list(estados.values())

    # RENDER TEMPLATE COMPLETO
    return render_template(
        "dashboard.html",
        total_stock=total_stock,
        bultos_hoy=bultos_hoy,
        alertas_activas=alertas_activas,
        errores_hoy=errores_hoy,
        criticos=criticos,
        bajos=bajos,
        normales=normales,
        vacios=vacios,
        alertas_dias=alertas_dias,
        horas_bultos=horas,
        prod_labels=prod_labels,
        prod_values=prod_values,
        estado_labels=estado_labels,
        estado_values=estado_values
    )
