from flask import Blueprint, render_template
from flask_login import login_required

alertas_ai_bp = Blueprint("alertas_ai", __name__, url_prefix="/alertas-ai")

@alertas_ai_bp.route("/listado")
@login_required
def listado_ai():

    # Datos de ejemplo para probar
    alertas = [
        {"tipo": "Predicción Stock Crítico", "material": "M00123", "riesgo": "Alto", "fecha": "2025-12-01"},
        {"tipo": "Anomalía en Inventario", "material": "M00421", "riesgo": "Medio", "fecha": "2025-12-01"},
        {"tipo": "Uso irregular de bultos", "material": "B099", "riesgo": "Alto", "fecha": "2025-11-30"},
    ]

    return render_template("alertas_ai/listado_ai.html", alertas=alertas)
