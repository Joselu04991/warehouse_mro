from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from models import db
from models.technician_error import TechnicianError
from datetime import datetime
from sqlalchemy import func
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os


technician_errors_bp = Blueprint(
    "technician_errors",
    __name__,
    url_prefix="/technician_errors"
)

# ---------------------------------------------------------
# NUEVO ERROR
# ---------------------------------------------------------
@technician_errors_bp.route("/new", methods=["GET", "POST"])
@login_required
def new_error():
    if request.method == "POST":
        tecnico = request.form["tecnico"]
        tipo_error = request.form["tipo_error"]
        gravedad = request.form["gravedad"]
        observacion = request.form["observacion"]

        # -----------------------------
        # SISTEMA DE COSTOS AUTOMÁTICOS
        # -----------------------------
        costos = {
            "Error en codificación": {"dinero": 150, "puntaje": 10},
            "Error en registro SAP": {"dinero": 300, "puntaje": 20},
            "Error en ubicación de material": {"dinero": 500, "puntaje": 40},
            "Error en conteo físico": {"dinero": 200, "puntaje": 15},
            "Error en despacho": {"dinero": 450, "puntaje": 35},
            "Error administrativo": {"dinero": 100, "puntaje": 5},
        }

        # Seguridad por si alguien envía un tipo raro
        if tipo_error not in costos:
            flash("Tipo de error desconocido.", "danger")
            return redirect(url_for("technician_errors.new_error"))

        dinero_perdido = costos[tipo_error]["dinero"]
        puntaje = costos[tipo_error]["puntaje"]

        nuevo = TechnicianError(
            tecnico=tecnico,
            tipo_error=tipo_error,
            gravedad=gravedad,
            observacion=observacion,
            fecha_hora=datetime.now(),
            dinero_perdido=dinero_perdido,
            puntaje=puntaje,
            creado_en=datetime.now()
        )

        db.session.add(nuevo)
        db.session.commit()

        flash("Error registrado exitosamente.", "success")
        return redirect(url_for("technician_errors.list_errors"))

    return render_template("technician_errors/form_new.html")

# ---------------------------------------------------------
# LISTA + ESTADÍSTICAS
# ---------------------------------------------------------
@technician_errors_bp.route("/list")
@login_required
def list_errors():
    errores = TechnicianError.query.order_by(
        TechnicianError.fecha_hora.desc()
    ).all()

    # Ranking por dinero perdido
    ranking = (
        db.session.query(
            TechnicianError.tecnico,
            func.sum(TechnicianError.dinero_perdido)
        )
        .group_by(TechnicianError.tecnico)
        .order_by(func.sum(TechnicianError.dinero_perdido).desc())
        .all()
    )
    ranking_dict = {r[0]: float(r[1]) for r in ranking}

    # Gráfico por día
    graf_raw = (
        db.session.query(
            func.date(TechnicianError.fecha_hora),
            func.sum(TechnicianError.dinero_perdido)
        )
        .group_by(func.date(TechnicianError.fecha_hora))
        .order_by(func.date(TechnicianError.fecha_hora))
        .all()
    )
    graf_por_dia = {str(r[0]): float(r[1]) for r in graf_raw}

    return render_template(
        "technician_errors/form_list.html",
        errores=errores,
        ranking=ranking_dict,
        graf_por_dia=graf_por_dia
    )


# ---------------------------------------------------------
# REPORTE PDF (NUEVO - SIN ERRORES)
# ---------------------------------------------------------
@technician_errors_bp.route("/reporte_pdf")
@login_required
def reporte_pdf():

    errores = TechnicianError.query.order_by(TechnicianError.fecha_hora.desc()).all()

    # Nombre del archivo PDF temporal
    pdf_path = "reporte_errores.pdf"

    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter

    # --------------------------
    # TÍTULO DEL REPORTE
    # --------------------------
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, height - 50, "Reporte de Errores Técnicos - SIDERPERU")

    c.setFont("Helvetica", 12)
    c.drawString(50, height - 80, f"Generado por: {current_user.username}")
    c.drawString(50, height - 100, f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # --------------------------
    # TABLA
    # --------------------------
    y = height - 140
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "Técnico")
    c.drawString(200, y, "Tipo")
    c.drawString(350, y, "S/ Perdido")
    c.drawString(450, y, "Puntaje")
    y -= 20

    c.setFont("Helvetica", 10)

    for e in errores:
        if y < 50:
            c.showPage()
            y = height - 50

        c.drawString(50, y, str(e.tecnico))
        c.drawString(200, y, str(e.tipo_error))
        c.drawString(350, y, f"S/ {e.dinero_perdido:.2f}")
        c.drawString(450, y, str(e.puntaje))

        y -= 18

    c.save()

    return send_file(pdf_path, as_attachment=True)
