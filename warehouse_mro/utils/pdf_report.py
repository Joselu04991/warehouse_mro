import os
import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics import renderPDF
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
import qrcode
from flask import current_app
from models.user import User
from models.inventory import InventoryItem
from models.bultos import Bulto
from models.alerts import Alert
from models.actividad import ActividadUsuario


def create_pdf_reporte(user_id):
    """
    Genera el PDF Ultra Pro del usuario.
    Usado por el scheduler y también por /descargar-datos.
    """
    user = User.query.get(user_id)
    if not user:
        return None

    # KPIs
    kpi_inventarios = InventoryItem.query.count()
    kpi_bultos = Bulto.query.count()
    kpi_alertas = Alert.query.count()

    # Actividad
    actividad = (
        ActividadUsuario.query
        .filter_by(user_id=user.id)
        .order_by(ActividadUsuario.fecha.desc())
        .limit(15)
        .all()
    )

    perfil_completado = getattr(user, "perfil_completado", 0)

    security_code = f"SEC-{user.id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

    # ========= RUTA PDF ============
    reports_folder = os.path.join(current_app.root_path, "static", "reports")
    os.makedirs(reports_folder, exist_ok=True)

    pdf_path = os.path.join(
        reports_folder,
        f"perfil_usuario_{user.id}_ULTRA_PRO.pdf"
    )

    # ========= CREAR CANVAS ========
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter

    # ========= MARCA DE AGUA =========
    c.saveState()
    c.setFont("Helvetica-Bold", 60)
    c.setFillColorRGB(0.93, 0.93, 0.93)
    c.translate(width / 4, height / 3)
    c.rotate(45)
    c.drawString(0, 0, "GERDAU - CONFIDENCIAL")
    c.restoreState()

    # ========= ENCABEZADO ==========

    c.setFillColorRGB(0, 59/255, 113/255)
    c.rect(0, height - 90, width, 90, fill=1)

    c.setFont("Helvetica-Bold", 22)
    c.setFillColor(colors.white)
    c.drawString(30, height - 55, "Reporte Corporativo del Usuario")

    c.setFont("Helvetica", 11)
    c.drawString(30, height - 70, "Sistema Warehouse MRO - SIDERPERU / GERDAU")

    # LOGO SIDERPERU EXACTO
    try:
        logo_path = os.path.join(current_app.root_path, "static", "img", "gerdau_logo.jpg")
        c.drawImage(logo_path, width - 150, height - 82, width=120, height=50, mask="auto")
    except Exception as e:
        print("No se pudo cargar logo:", e)

    # ========= FOTO + DATOS ==========
    top = height - 130

    if hasattr(user, "photo") and user.photo:
        try:
            photo_path = os.path.join(current_app.root_path, "static", user.photo)
            c.drawImage(photo_path, 30, top - 130, width=120, height=120, mask="auto")
        except:
            pass

    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(170, top, f"Usuario: {user.username}")

    c.setFont("Helvetica", 12)
    c.drawString(170, top - 20, f"Rol: {user.role}")
    c.drawString(170, top - 40, f"Correo: {user.email or 'No registrado'}")
    c.drawString(170, top - 60, f"Teléfono: {user.phone or 'No registrado'}")
    c.drawString(170, top - 80, f"Ubicación: {user.location or 'No registrada'}")
    c.drawString(170, top - 100, f"Área: {user.area or 'No asignada'}")

    creado = user.created_at.strftime("%d/%m/%Y") if user.created_at else "Sin registro"
    c.drawString(170, top - 120, f"Miembro desde: {creado}")

    c.drawString(170, top - 140, f"Perfil completado: {perfil_completado}%")

    # ========= GRÁFICO DE BARRAS ==========
    chart = Drawing(400, 200)
    bar = VerticalBarChart()

    bar.x = 50
    bar.y = 30
    bar.width = 300
    bar.height = 150
    bar.data = [[kpi_inventarios, kpi_bultos, kpi_alertas]]

    bar.categoryAxis.categoryNames = ["Inventarios", "Bultos", "Alertas"]
    bar.bars[0].fillColor = colors.Color(0/255, 59/255, 113/255)

    chart.add(bar)
    renderPDF.draw(chart, c, 30, top - 350)

    # ========= GRÁFICO PIE ==========
    total = kpi_inventarios + kpi_bultos + kpi_alertas
    if total > 0:
        pie_draw = Drawing(200, 160)
        pie = Pie()
        pie.x = 40
        pie.y = 15
        pie.width = 120
        pie.height = 120
        pie.data = [kpi_inventarios, kpi_bultos, kpi_alertas]
        pie.labels = ["Inv", "Bultos", "Alertas"]
        pie_draw.add(pie)
        renderPDF.draw(pie_draw, c, width - 240, top - 330)

    # ========= QR ==========
    qr_buf = io.BytesIO()
    qr = qrcode.QRCode(box_size=3, border=2)
    qr.add_data(f"Reporte generado para usuario {user.id}")
    qr.make(fit=True)
    img = qr.make_image()
    img.save(qr_buf, format="PNG")
    qr_buf.seek(0)
    c.drawImage(ImageReader(qr_buf), width - 120, top - 200, width=70, height=70)

    # ========= ACTIVIDAD ===========
    y = top - 380
    c.setFont("Helvetica-Bold", 14)
    c.drawString(30, y, "Actividad reciente:")

    y -= 20
    c.setFont("Helvetica", 10)

    if actividad:
        for log in actividad:
            if y < 70:
                c.showPage()
                y = height - 50

            fecha = log.fecha.strftime("%d/%m/%Y %H:%M")
            c.drawString(30, y, f"{fecha} — {log.descripcion}")
            y -= 18
    else:
        c.drawString(30, y, "No hay actividad registrada.")

    # ========= FOOTER ===========
    c.setFillColorRGB(0, 59/255, 113/255)
    c.rect(0, 0, width, 40, fill=1)

    c.setFont("Helvetica", 8)
    c.setFillColor(colors.white)
    c.drawString(30, 20, "Sistema Warehouse MRO — GERDAU / SIDERPERU")
    c.drawRightString(width - 30, 20, f"Código de seguridad: {security_code}")

    c.save()
    return pdf_path
