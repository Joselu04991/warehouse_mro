from flask import Blueprint, render_template
from flask_login import login_required
from sqlalchemy import func
from datetime import date

from models.inventory import InventoryItem
from models.bultos import Bulto
from models.alerts import Alert
from models.warehouse2d import WarehouseLocation
from models.technician_error import TechnicianError

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@dashboard_bp.route("/")
@login_required
def dashboard():

    total_stock = InventoryItem.query.count()

    bultos_hoy = Bulto.query.filter(
        func.date(Bulto.fecha_hora) == date.today()
    ).count()

    alertas_activas = Alert.query.filter(Alert.resolved == False).count()

    errores_hoy = TechnicianError.query.filter(
        func.date(TechnicianError.creado_en) == date.today()
    ).count()


    criticos = sum(1 for i in WarehouseLocation.query.all() if i.status == "crítico")
    bajos = sum(1 for i in WarehouseLocation.query.all() if i.status == "bajo")
    normales = sum(1 for i in WarehouseLocation.query.all() if i.status == "normal")
    vacios = sum(1 for i in WarehouseLocation.query.all() if i.status == "vacío")

    # Alertas por día
    alertas_por_dia = (
        Alert.query.with_entities(
            func.strftime("%w", Alert.created_at),
            func.count(Alert.id)
        )
        .group_by(func.strftime("%w", Alert.created_at))
        .all()
    )

    alertas_dias = [0, 0, 0, 0, 0, 0, 0]
    for dia, cant in alertas_por_dia:
        alertas_dias[int(dia)] = cant

    # Bultos por hora
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
        horas_bultos=horas
    )
