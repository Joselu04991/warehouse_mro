from flask import Blueprint, render_template, request, flash
from flask_login import login_required
import pandas as pd
import os

analisis_oc_bp = Blueprint(
    "analisis_oc",
    __name__,
    url_prefix="/analisis_oc"
)

# ================================
#   PANTALLA PRINCIPAL (GET)
# ================================
@analisis_oc_bp.route("/upload", methods=["GET"])
@login_required
def upload_oc():
    return render_template("analisis_oc/upload_oc.html")


# ================================
#   PROCESAR EXCEL (POST)
# ================================
@analisis_oc_bp.route("/upload", methods=["POST"])
@login_required
def upload_oc_post():

    # -------------------------
    # 1. Validar archivo
    # -------------------------
    if "file" not in request.files:
        flash("Debes subir un archivo Excel", "danger")
        return render_template("analisis_oc/upload_oc.html")

    file = request.files["file"]

    if file.filename == "":
        flash("Debes seleccionar un archivo", "danger")
        return render_template("analisis_oc/upload_oc.html")

    # Extensión válida
    if not (file.filename.endswith(".xlsx") or file.filename.endswith(".xls")):
        flash("El archivo debe ser Excel (.xlsx / .xls)", "danger")
        return render_template("analisis_oc/upload_oc.html")

    try:
        # -------------------------
        # 2. Leer Excel
        # -------------------------
        df = pd.read_excel(file)

        # Normalizar columnas
        df.columns = [str(col).strip().lower() for col in df.columns]

        # -------------------------
        # 3. Columnas obligatorias (según tu Excel real)
        # -------------------------
        columnas_necesarias = [
            "orden de compra",
            "proveedor",
            "cantidad pedida",
            "cantidad recibida",
            "estado",
            "fecha"
        ]

        for col in columnas_necesarias:
            if col not in df.columns:
                flash(f"❌ Falta la columna obligatoria: {col}", "danger")
                return render_template("analisis_oc/upload_oc.html")

        # Limpieza de NaN
        df.fillna(0, inplace=True)

        # -------------------------
        # 4. KPIs
        # -------------------------
        resumen = {
            "total_lineas": len(df),
            "total_oc": df["orden de compra"].nunique(),
            "total_proveedores": df["proveedor"].nunique(),
            "total_pedido": df["cantidad pedida"].sum(),
            "total_recibido": df["cantidad recibida"].sum(),
        }

        if resumen["total_pedido"] > 0:
            resumen["porcentaje_atencion"] = round(
                (resumen["total_recibido"] / resumen["total_pedido"]) * 100,
                2
            )
        else:
            resumen["porcentaje_atencion"] = 0

        # -------------------------
        # 5. Gráficos
        # -------------------------

        # Por mes
        if "fecha" in df.columns:
            df["mes"] = pd.to_datetime(df["fecha"], errors="coerce").dt.strftime("%Y-%m")
            graf_por_mes = df.groupby("mes")["cantidad pedida"].sum().to_dict()
        else:
            graf_por_mes = {}

        # Proveedores top
        graf_por_proveedor = (
            df.groupby("proveedor")["cantidad pedida"]
            .sum()
            .sort_values(ascending=False)
            .head(10)
            .to_dict()
        )

        # Estados
        graf_por_estado = df["estado"].value_counts().to_dict()

        # -------------------------
        # 6. Renderizar HTML
        # -------------------------
        return render_template(
            "analisis_oc/upload_oc.html",
            df=df,
            resumen=resumen,
            graf_por_mes=graf_por_mes,
            graf_por_proveedor=graf_por_proveedor,
            graf_por_estado=graf_por_estado
        )

    except Exception as e:
        flash(f"Error al procesar el Excel: {str(e)}", "danger")
        return render_template("analisis_oc/upload_oc.html")
