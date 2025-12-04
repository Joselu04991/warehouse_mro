from datetime import datetime

import pandas as pd
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_file,
)
from flask_login import login_required
from sqlalchemy import func

from models import db
from models.inventory import InventoryItem
from models.alerts import Alert
from utils.validators import roles_required
from utils.excel import (
    load_inventory_excel,
    load_warehouse2d_excel,  # por si luego lo quieres usar aquí
    generate_discrepancies_excel,
    sort_location_advanced,
)

inventory_bp = Blueprint("inventory", __name__, url_prefix="/inventory")


# =====================================================================================
#                                  CARGA INVENTARIO
# =====================================================================================

@inventory_bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload_inventory():
    """
    Carga el inventario base desde Excel (sistema).
    Usa el validador flexible load_inventory_excel.
    """
    if request.method == "POST":
        file = request.files.get("file")
        if not file:
            flash("Debe seleccionar un archivo de Excel.", "warning")
            return redirect(url_for("inventory.upload_inventory"))

        try:
            df = load_inventory_excel(file)
        except ValueError as e:
            flash(str(e), "danger")
            return redirect(url_for("inventory.upload_inventory"))
        except Exception:
            flash("Error al leer el archivo de inventario. Verifique el formato.", "danger")
            return redirect(url_for("inventory.upload_inventory"))

        # Limpiamos inventario anterior
        InventoryItem.query.delete()
        db.session.commit()

        # Insertamos nuevo inventario
        for _, row in df.iterrows():
            item = InventoryItem(
                material_code=str(row["Código del Material"]).strip(),
                material_text=str(row["Texto breve de material"]).strip(),
                base_unit=str(row["Unidad de medida base"]).strip(),
                location=str(row["Ubicación"]).strip(),
                libre_utilizacion=float(row["Libre utilización"] or 0),
            )

            db.session.add(item)

        db.session.commit()
        flash("Inventario cargado correctamente.", "success")
        return redirect(url_for("inventory.list_inventory"))

    return render_template("inventory/upload.html")


# =====================================================================================
#                                   LISTA INVENTARIO
# =====================================================================================

@inventory_bp.route("/list")
@login_required
def list_inventory():
    """
    Muestra el inventario actual, ordenado por ubicación usando sort_location_advanced.
    """
    items = InventoryItem.query.all()
    items_sorted = sorted(items, key=lambda x: sort_location_advanced(x.location))
    return render_template("inventory/list.html", items=items_sorted)


# =====================================================================================
#                        DISCREPANCIAS USANDO EXCEL DE CONTEO
# =====================================================================================

@inventory_bp.route("/discrepancies", methods=["GET", "POST"])
@login_required
def discrepancies():
    """
    Genera discrepancias usando un Excel de conteo físico.
    El Excel de conteo tiene las mismas columnas que el inventario,
    donde 'Libre utilización' representa el stock contado.
    """
    if request.method == "POST":
        file = request.files.get("file")
        if not file:
            flash("Debe seleccionar un archivo de conteo físico.", "warning")
            return redirect(url_for("inventory.discrepancies"))

        try:
            counted_df = load_inventory_excel(file)
        except ValueError as e:
            flash(str(e), "danger")
            return redirect(url_for("inventory.discrepancies"))
        except Exception:
            flash("Error al leer el archivo de conteo físico. Verifique el formato.", "danger")
            return redirect(url_for("inventory.discrepancies"))

        # Normalizamos claves
        counted_df["Código del Material"] = (
            counted_df["Código del Material"].astype(str).str.strip()
        )
        counted_df["Ubicación"] = counted_df["Ubicación"].astype(str).str.strip()

        # Agrupamos conteo físico por Código + Ubicación
        counted_group = (
            counted_df.groupby(
                ["Código del Material", "Ubicación"], as_index=False
            )["Libre utilización"]
            .sum()
            .rename(
                columns={
                    "Código del Material": "Código Material",
                    "Libre utilización": "Stock contado",
                }
            )
        )

        # Inventario del sistema agrupado
        system_q = (
            db.session.query(
                InventoryItem.material_code.label("Código Material"),
                InventoryItem.material_text.label("Descripción"),
                InventoryItem.base_unit.label("Unidad"),
                InventoryItem.location.label("Ubicación"),
                func.sum(InventoryItem.libre_utilizacion).label("Stock sistema"),
            )
            .group_by(
                InventoryItem.material_code,
                InventoryItem.material_text,
                InventoryItem.base_unit,
                InventoryItem.location,
            )
        )

        system_df = pd.read_sql(system_q.statement, db.session.bind)

        # Merge sistema vs conteo
        merged = system_df.merge(
            counted_group,
            on=["Código Material", "Ubicación"],
            how="outer",
        )

        merged["Stock sistema"] = merged["Stock sistema"].fillna(0.0)
        merged["Stock contado"] = merged["Stock contado"].fillna(0.0)
        merged["Descripción"] = merged["Descripción"].fillna("SIN DESCRIPCIÓN")
        merged["Unidad"] = merged["Unidad"].fillna("")

        # Diferencia = contado - sistema
        merged["Diferencia"] = merged["Stock contado"] - merged["Stock sistema"]

        # Estado
        estados = []
        for _, r in merged.iterrows():
            diff = r["Diferencia"]
            if diff == 0:
                estado = "OK"
            elif diff < 0:
                if diff <= -10:
                    estado = "CRÍTICO"
                else:
                    estado = "FALTA"
            else:
                if diff >= 10:
                    estado = "SOBRA"
                else:
                    estado = "SOBRA"
            estados.append(estado)
        merged["Estado"] = estados

        # Orden final de columnas
        df_final = merged[
            [
                "Código Material",
                "Descripción",
                "Unidad",
                "Ubicación",
                "Stock sistema",
                "Stock contado",
                "Diferencia",
                "Estado",
            ]
        ].copy()

        # Generar alertas por discrepancias negativas grandes
        for _, r in df_final.iterrows():
            if r["Diferencia"] <= -10:
                msg = (
                    f"Discrepancia crítica en {r['Código Material']} - {r['Ubicación']}: "
                    f"Sistema={r['Stock sistema']}, Conteo={r['Stock contado']}."
                )
                alert = Alerta(
                    alert_type="discrepancia",
                    message=msg,
                    severity="Alta",
                )
                db.session.add(alert)
        db.session.commit()

        # Generar Excel profesional
        output = generate_discrepancies_excel(df_final)
        filename = f"discrepancias_inventario_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype=(
                "application/vnd.openxmlformats-"
                "officedocument.spreadsheetml.sheet"
            ),
        )

    return render_template("inventory/discrepancies.html")


# =====================================================================================
#                  CONTEO EN HTML (SIN EXCEL) + DISCREPANCIAS
# =====================================================================================

@inventory_bp.route("/count", methods=["GET", "POST"])
@login_required
def count_inventory():
    """
    Permite hacer el conteo directamente en el HTML:
    - GET: muestra inventario con campo 'Stock contado'
    - POST: genera Excel de discrepancias usando lo que se digitó
    """
    if request.method == "GET":
        items = InventoryItem.query.all()
        items_sorted = sorted(items, key=lambda x: sort_location_advanced(x.location))
        return render_template("inventory/count.html", items=items_sorted)

    # POST: recibir conteo desde formulario
    items = InventoryItem.query.all()
    filas = []

    for item in items:
        field_name = f"count_{item.id}"
        raw_val = request.form.get(field_name, "").strip()

        try:
            contado = float(raw_val) if raw_val != "" else 0.0
        except ValueError:
            contado = 0.0

        sistema = float(item.libre_utilizacion or 0.0)
        diferencia = contado - sistema

        # Estado
        if diferencia == 0:
            estado = "OK"
        elif diferencia < 0:
            if diferencia <= -10:
                estado = "CRÍTICO"
            else:
                estado = "FALTA"
        else:
            if diferencia >= 10:
                estado = "SOBRA"
            else:
                estado = "SOBRA"

        filas.append(
            {
                "Código Material": item.material_code,
                "Descripción": item.material_text,
                "Unidad": item.base_unit,
                "Ubicación": item.location,
                "Stock sistema": sistema,
                "Stock contado": contado,
                "Diferencia": diferencia,
                "Estado": estado,
            }
        )

        # Alerta por discrepancia crítica
        if diferencia <= -10:
            msg = (
                f"Discrepancia crítica en {item.material_code} - {item.location}: "
                f"Sistema={sistema}, Conteo={contado}."
            )
            alert = Alert(
                alert_type="discrepancia",
                message=msg,
                severity="Alta",
            )
            db.session.add(alert)

    db.session.commit()

    df_final = pd.DataFrame(filas)

    output = generate_discrepancies_excel(df_final)
    filename = f"discrepancias_inventario_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype=(
            "application/vnd.openxmlformats-"
            "officedocument.spreadsheetml.sheet"
        ),
    )
