from datetime import datetime

import pandas as pd
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
)
from flask_login import login_required, current_user

from models import db
from models.warehouse2d import WarehouseLocation
from models.alerts import Alert
from utils.excel import load_warehouse2d_excel, sort_location_advanced

warehouse2d_bp = Blueprint("warehouse2d", __name__, url_prefix="/warehouse2d")


STATUS_RANK = {
    "vacío": 0,
    "normal": 1,
    "bajo": 2,
    "crítico": 3,
}


@warehouse2d_bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload_warehouse2d():

    if request.method == "POST":
        file = request.files.get("file")

        if not file:
            flash("Debe seleccionar un archivo Excel.", "warning")
            return redirect(url_for("warehouse2d.upload_warehouse2d"))

        try:
            df = load_warehouse2d_excel(file)
        except ValueError as e:
            flash(str(e), "danger")
            return redirect(url_for("warehouse2d.upload_warehouse2d"))
        except Exception:
            flash("Error al procesar el archivo 2D. Revise formato y columnas.", "danger")
            return redirect(url_for("warehouse2d.upload_warehouse2d"))

        WarehouseLocation.query.delete()
        db.session.commit()

        for _, row in df.iterrows():

            cod = str(row.get("Código del Material", "")).strip()
            desc = str(row.get("Texto breve de material", "")).strip()
            umb = str(row.get("Unidad de medida base", "")).strip()
            ubi = str(row.get("Ubicación", "")).strip()

            seg = float(row.get("Stock de seguridad", 0) or 0)
            maxi = float(row.get("Stock máximo", 0) or 0)
            libre = float(row.get("Libre utilización", 0) or 0)

            item = WarehouseLocation(
                material_code=cod,
                material_text=desc,
                base_unit=umb,
                ubicacion=ubi,
                stock_seguridad=seg,
                stock_maximo=maxi,
                libre_utilizacion=libre,
            )

            db.session.add(item)

            estado = item.status

            if estado == "crítico":
                mensaje = (
                    f"Stock crítico en {ubi}: {cod} ({desc}) "
                    f"Libre={libre}, Seguridad={seg}"
                )
                alerta = Alert(
                    message=mensaje
                )
                db.session.add(alerta)

        db.session.commit()

        flash("El layout 2D fue cargado correctamente.", "success")
        return redirect(url_for("warehouse2d.map_view"))

    return render_template("warehouse2d/upload.html")


@warehouse2d_bp.route("/map")
@login_required
def map_view():
    return render_template("warehouse2d/map.html")


@warehouse2d_bp.route("/map-data")
@login_required
def map_data():

    items = WarehouseLocation.query.all()
    por_ubicacion = {}

    for item in items:
        loc = item.ubicacion or "SIN UBICACIÓN"
        estado_item = item.status

        if loc not in por_ubicacion:
            por_ubicacion[loc] = {
                "location": loc,
                "total_libre": 0.0,
                "items": 0,
                "status": estado_item,
                "rank": STATUS_RANK.get(estado_item, 0),
            }

        por_ubicacion[loc]["total_libre"] += float(item.libre_utilizacion or 0)
        por_ubicacion[loc]["items"] += 1

        rank = STATUS_RANK.get(estado_item, 0)
        if rank > por_ubicacion[loc]["rank"]:
            por_ubicacion[loc]["rank"] = rank
            por_ubicacion[loc]["status"] = estado_item

    data_sorted = sorted(
        por_ubicacion.values(),
        key=lambda x: sort_location_advanced(x["location"])
    )

    for d in data_sorted:
        d.pop("rank", None)

    return jsonify(data_sorted)


@warehouse2d_bp.route("/location/<path:ubicacion>")
@login_required
def location_detail(ubicacion):

    items = (
        WarehouseLocation.query.filter_by(ubicacion=ubicacion.strip())
        .order_by(WarehouseLocation.material_code)
        .all()
    )

    detalle = []

    for item in items:
        detalle.append({
            "material_code": item.material_code,
            "material_text": item.material_text,
            "base_unit": item.base_unit,
            "stock_seguridad": item.stock_seguridad,
            "stock_maximo": item.stock_maximo,
            "libre_utilizacion": item.libre_utilizacion,
            "status": item.status,
        })

    return jsonify({
        "ubicacion": ubicacion,
        "items": detalle,
    })
