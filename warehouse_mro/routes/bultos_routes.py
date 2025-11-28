from flask import Blueprint, render_template, request, redirect, url_for, send_file, flash
from flask_login import login_required
from models.bultos import Bulto
from models import db
from datetime import datetime
import pandas as pd
import io
import calendar

bultos_bp = Blueprint("bultos", __name__, url_prefix="/bultos")


# =====================================================================
#   LISTA + KPIs + GRÁFICOS (COMPLETO)
# =====================================================================
@bultos_bp.route("/list")
@login_required
def list_bultos():

    # ---------------------------
    # FILTROS
    # ---------------------------
    chofer = request.args.get("chofer", "").strip()
    placa = request.args.get("placa", "").strip()
    desde = request.args.get("desde", "").strip()
    hasta = request.args.get("hasta", "").strip()

    query = Bulto.query

    if chofer:
        query = query.filter(Bulto.chofer.ilike(f"%{chofer}%"))

    if placa:
        query = query.filter(Bulto.placa.ilike(f"%{placa}%"))

    if desde:
        desde_dt = datetime.strptime(desde, "%Y-%m-%d")
        query = query.filter(Bulto.fecha_hora >= desde_dt)

    if hasta:
        hasta_dt = datetime.strptime(hasta, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        query = query.filter(Bulto.fecha_hora <= hasta_dt)

    bultos = query.order_by(Bulto.fecha_hora.asc()).all()

    # ---------------------------
    # KPIs
    # ---------------------------
    total_bultos = sum(b.cantidad for b in bultos)
    bultos_hoy = sum(b.cantidad for b in bultos if b.fecha_hora.date() == datetime.today().date())

    total_trailers = len(set(b.placa for b in bultos if b.placa))

    # ---------------------------
    # GRÁFICO: BULTOS POR DÍA
    # ---------------------------
    dias = []
    bultos_dias = []

    graf_dia = {}
    for b in bultos:
        d = b.fecha_hora.strftime("%d-%m")
        graf_dia[d] = graf_dia.get(d, 0) + b.cantidad

    for d, v in graf_dia.items():
        dias.append(d)
        bultos_dias.append(v)

    # ---------------------------
    # GRÁFICO: BULTOS POR SEMANA
    # ---------------------------
    semanas = []
    bultos_sem = []
    graf_sem = {}

    for b in bultos:
        week_num = b.fecha_hora.isocalendar().week
        graf_sem[week_num] = graf_sem.get(week_num, 0) + b.cantidad

    for s, v in graf_sem.items():
        semanas.append(f"Semana {s}")
        bultos_sem.append(v)

    semanas_totales = len(semanas)

    # ---------------------------
    # GRÁFICO: BULTOS POR MES
    # ---------------------------
    meses = []
    bultos_mes = []
    graf_mes = {}

    for b in bultos:
        m = b.fecha_hora.month
        graf_mes[m] = graf_mes.get(m, 0) + b.cantidad

    for m, v in graf_mes.items():
        meses.append(calendar.month_name[m])
        bultos_mes.append(v)

    # ---------------------------
    # INCONSISTENCIAS (simulado)
    # ---------------------------
    inconsistencias_mes = [0] * len(meses)
    inconsistencias = sum(inconsistencias_mes)

    # ---------------------------
    # FALTANTE POR MES (simulado)
    # ---------------------------
    faltante_mes = [0] * len(meses)

    return render_template(
        "bultos/list.html",
        bultos=bultos,
        total_bultos=total_bultos,
        bultos_hoy=bultos_hoy,
        total_trailers=total_trailers,
        semanas_totales=semanas_totales,
        inconsistencias=inconsistencias,
        dias=dias,
        bultos_dias=bultos_dias,
        semanas=semanas,
        bultos_sem=bultos_sem,
        meses=meses,
        bultos_mes=bultos_mes,
        inconsistencias_mes=inconsistencias_mes,
        faltante_mes=faltante_mes
    )


# =====================================================================
# NUEVO BULTO
# =====================================================================
@bultos_bp.route("/new", methods=["GET", "POST"])
@login_required
def new_bulto():

    if request.method == "POST":

        cantidad = request.form.get("cantidad")
        chofer = request.form.get("chofer")
        placa = request.form.get("placa")
        fecha_hora = request.form.get("fecha_hora")
        observacion = request.form.get("observacion")

        nuevo_bulto = Bulto(
            cantidad=int(cantidad),
            chofer=chofer,
            placa=placa,
            fecha_hora=datetime.fromisoformat(fecha_hora),
            observacion=observacion,
            creado_en=datetime.now()
        )

        db.session.add(nuevo_bulto)
        db.session.commit()

        flash("Bulto registrado correctamente", "success")
        return redirect(url_for("bultos.new_bulto"))

    return render_template("bultos/form_bulto.html")


# =====================================================================
# EXPORTAR EXCEL
# =====================================================================
@bultos_bp.route("/export")
@login_required
def export_excel():

    bultos = Bulto.query.order_by(Bulto.fecha_hora.desc()).all()

    data = [{
        "ID": b.id,
        "Cantidad": b.cantidad,
        "Chofer": b.chofer,
        "Placa": b.placa,
        "Fecha y Hora": b.fecha_hora,
        "Observación": b.observacion
    } for b in bultos]

    df = pd.DataFrame(data)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Bultos")

    output.seek(0)

    return send_file(
        output,
        download_name="bultos.xlsx",
        as_attachment=True,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
