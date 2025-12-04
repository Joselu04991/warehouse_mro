from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, current_app, send_file, session
)
from flask_login import (
    login_user, logout_user, login_required,
    current_user
)
from models import db
from models.user import User
from datetime import datetime, timedelta
import os
import re
import secrets
import pyotp
from werkzeug.utils import secure_filename
from utils.pdf_report import create_pdf_reporte  # si no lo usas, no pasa nada


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


# =====================================================================
# 🔒 EXPIRACIÓN AUTOMÁTICA DE SESIÓN (30 MIN INACTIVO)
# =====================================================================
@auth_bp.before_app_request
def verificar_expiracion_sesion():
    """
    Verifica si la sesión del usuario ha expirado por inactividad.
    Se actualiza last_activity en cada request.
    """

    # Si no hay actividad almacenada → nada que validar
    if "last_activity" not in session:
        session["last_activity"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        return

    # Convertir last_activity desde string a datetime NAIVE
    raw_value = session["last_activity"]

    try:
        # Detectar si viene como aware (con +00:00)
        if "+" in raw_value:
            raw_value = raw_value.split("+")[0]

        last_activity = datetime.strptime(raw_value, "%Y-%m-%d %H:%M:%S")
    except Exception:
        # Si algo falla, reiniciamos la actividad por seguridad
        session["last_activity"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        return

    # Calcular límite
    limite = last_activity + timedelta(minutes=30)

    # Comparación SEGURA (todo naive)
    if datetime.utcnow() > limite:
        logout_user()
        session.clear()
        flash("Tu sesión expiró por inactividad.", "warning")
        return redirect(url_for("auth.login"))

    # Actualizar timestamp
    session["last_activity"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
# =====================================================================
# 🔐 REGLAS DE CONTRASEÑA (REUTILIZABLES)
# =====================================================================
def validar_password(password):
    """
    Devuelve lista de errores de política de contraseña.
    Si la lista está vacía, la contraseña es válida.
    """
    reglas = [
        (r".{8,}", "Debe tener al menos 8 caracteres."),
        (r"[A-Z]", "Debe contener al menos una mayúscula."),
        (r"[a-z]", "Debe contener al menos una minúscula."),
        (r"[0-9]", "Debe contener al menos un número."),
        (r"[^A-Za-z0-9]", "Debe contener al menos un símbolo (ej: !@#%)."),
    ]

    errores = []
    for regex, msg in reglas:
        if not re.search(regex, password):
            errores.append(msg)

    return errores


# =====================================================================
# 🔐 LOGIN SEGURO + BLOQUEO + EMAIL + 2FA
# =====================================================================
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    Login seguro:
    - Bloqueo tras 5 intentos fallidos (15 min)
    - Verifica email confirmado
    - Si tiene 2FA habilitado, redirige a /auth/2fa-verify
    """

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()

        # Usuario no existe
        if not user:
            flash("Usuario o contraseña incorrectos.", "danger")
            return redirect(url_for("auth.login"))

        # Verificar si la cuenta está bloqueada
        if hasattr(user, "is_locked") and user.is_locked():
            # Intentamos calcular minutos restantes
            try:
                segundos = (user.locked_until - datetime.utcnow()).total_seconds()
                minutos = max(1, int(segundos // 60))
            except Exception:
                minutos = 15

            flash(f"Cuenta bloqueada. Inténtalo nuevamente en {minutos} minutos.", "danger")
            return redirect(url_for("auth.login"))

        # Validar contraseña
        if not user.check_password(password):
            # Manejo de intentos fallidos si el modelo lo soporta
            if hasattr(user, "failed_attempts"):
                user.failed_attempts = (user.failed_attempts or 0) + 1

                # Si llegó al límite, bloquear
                if user.failed_attempts >= 5 and hasattr(user, "lock"):
                    user.lock()  # este método lo implementas en User
                    flash("Demasiados intentos fallidos. Cuenta bloqueada por 15 minutos.", "danger")
                else:
                    flash("Contraseña incorrecta.", "danger")

                db.session.commit()
            else:
                flash("Contraseña incorrecta.", "danger")

            return redirect(url_for("auth.login"))

        # Si el modelo soporta reset de intentos
        if hasattr(user, "reset_attempts"):
            user.reset_attempts()

        # Verificar email confirmado si el campo existe
        if hasattr(user, "email_confirmed") and not user.email_confirmed:
            flash("Debes activar tu cuenta desde tu correo antes de iniciar sesión.", "warning")
            db.session.commit()
            return redirect(url_for("auth.login"))

        # Verificación 2FA si está habilitado
        if getattr(user, "twofa_enabled", False):
            session["2fa_user_id"] = user.id
            db.session.commit()
            return redirect(url_for("auth.twofa_verify"))

        # Login normal (sin 2FA)
        user.last_login = datetime.utcnow()
        db.session.commit()
        login_user(user)

        return redirect(url_for("dashboard.dashboard"))

    return render_template("auth/login.html")


# =====================================================================
# 🔐 2FA: VERIFICACIÓN DE CÓDIGO (LOGIN)
# =====================================================================
@auth_bp.route("/2fa-verificar", methods=["GET", "POST"])
def twofa_verify():
    """
    Pantalla donde el usuario ingresa el código 2FA después del login.
    """
    user_id = session.get("2fa_user_id")

    if not user_id:
        flash("No hay sesión pendiente de 2FA.", "warning")
        return redirect(url_for("auth.login"))

    user = User.query.get(user_id)
    if not user or not getattr(user, "twofa_enabled", False):
        flash("Error en 2FA. Intenta iniciar sesión nuevamente.", "danger")
        session.pop("2fa_user_id", None)
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        code = request.form.get("code", "").strip()
        if not code:
            flash("Ingresa el código 2FA.", "warning")
            return redirect(url_for("auth.twofa_verify"))

        totp = pyotp.TOTP(user.twofa_secret)
        if totp.verify(code):
            # Código correcto
            session.pop("2fa_user_id", None)
            user.last_login = datetime.utcnow()
            db.session.commit()
            login_user(user)
            return redirect(url_for("dashboard.dashboard"))
        else:
            flash("Código incorrecto. Inténtalo de nuevo.", "danger")

    return render_template("auth/2fa_verify.html", user=user)


# =====================================================================
# 📝 REGISTRO LIBRE (CUALQUIERA PUEDE REGISTRARSE)
# =====================================================================
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """
    Registro abierto para cualquier usuario.
    Primera vez crea usuario normal (owner ya lo tienes en app.py).
    Envía enlace de activación por 'correo' (por consola).
    """

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        password2 = request.form.get("password2", "")

        # Validar campos básicos
        if not username or not email or not password:
            flash("Todos los campos son obligatorios.", "warning")
            return redirect(url_for("auth.register"))

        if password != password2:
            flash("Las contraseñas no coinciden.", "danger")
            return redirect(url_for("auth.register"))

        # Validar políticas de contraseña
        errores = validar_password(password)
        if errores:
            for e in errores:
                flash(e, "danger")
            return redirect(url_for("auth.register"))

        # Validar existencia
        if User.query.filter_by(username=username).first():
            flash("Ese usuario ya existe.", "danger")
            return redirect(url_for("auth.register"))

        if User.query.filter_by(email=email).first():
            flash("Ese correo ya está registrado.", "danger")
            return redirect(url_for("auth.register"))

        # Token de activación
        token = secrets.token_urlsafe(32)

        nuevo_usuario = User(
            username=username,
            email=email,
            role="user",           # todos entran como user
            email_confirmed=False, # debe activar
            email_token=token,
            status="activo"
        )
        nuevo_usuario.set_password(password)

        db.session.add(nuevo_usuario)
        db.session.commit()

        # Enviar "correo"
        _enviar_email_activacion(email, token)

        flash("Cuenta creada. Revisa tu correo para activarla (se muestra en la consola).", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


# =====================================================================
# 📧 ENVIAR CORREO DE ACTIVACIÓN (MODO DEBUG: CONSOLA)
# =====================================================================
def _enviar_email_activacion(email, token):
    """
    Para producción usarías flask-mail o similar.
    Por ahora solo imprime el enlace en consola.
    """
    enlace = url_for("auth.activar_cuenta", token=token, _external=True)

    print("\n========== ACTIVACIÓN DE CUENTA ==========")
    print(f"Para: {email}")
    print(f"Enlace de activación: {enlace}")
    print("==========================================\n")


# =====================================================================
# ✔ ACTIVAR CUENTA DESDE ENLACE DE CORREO
# =====================================================================
@auth_bp.route("/activar/<token>")
def activar_cuenta(token):
    """
    Activa la cuenta del usuario cuyo token coincida.
    """

    user = User.query.filter_by(email_token=token).first()

    if not user:
        flash("Token inválido o expirado.", "danger")
        return redirect(url_for("auth.login"))

    user.email_confirmed = True
    user.email_token = None
    db.session.commit()

    flash("Cuenta activada con éxito. Ahora puedes iniciar sesión.", "success")
    return redirect(url_for("auth.login"))


# =====================================================================
# 🚪 LOGOUT
# =====================================================================
@auth_bp.route("/logout")
@login_required
def logout():
    """
    Cierra sesión y limpia la sesión de Flask.
    """
    logout_user()
    session.clear()
    flash("Sesión cerrada correctamente.", "info")
    return redirect(url_for("auth.login"))


# =====================================================================
# ⚙ 2FA: CONFIGURAR (HABILITAR DESDE PERFIL)
# =====================================================================
@auth_bp.route("/2fa-setup", methods=["GET", "POST"])
@login_required
def twofa_setup():
    """
    Permite al usuario habilitar 2FA.
    Genera un secreto y una URL otpauth para Google Authenticator.
    """
    if getattr(current_user, "twofa_enabled", False):
        flash("Ya tienes 2FA habilitado.", "info")
        return redirect(url_for("auth.perfil_usuario"))

    # Si todavía no tiene secreto, lo generamos
    if not current_user.twofa_secret:
        secret = pyotp.random_base32()
        current_user.twofa_secret = secret
        db.session.commit()
    else:
        secret = current_user.twofa_secret

    # Generar URL otpauth
    app_name = "Warehouse MRO"
    issuer = "SIDERPERU-GERDAU"
    otpauth_url = pyotp.totp.TOTP(secret).provisioning_uri(
        name=current_user.email or current_user.username,
        issuer_name=issuer
    )

    if request.method == "POST":
        code = request.form.get("code", "").strip()
        totp = pyotp.TOTP(secret)

        if totp.verify(code):
            current_user.twofa_enabled = True
            db.session.commit()
            flash("2FA habilitado correctamente.", "success")
            return redirect(url_for("auth.perfil_usuario"))
        else:
            flash("Código inválido. Escanea el QR y vuelve a intentar.", "danger")

    return render_template(
        "auth/2fa_setup.html",
        secret=secret,
        otpauth_url=otpauth_url
    )


# =====================================================================
# ⚙ 2FA: DESACTIVAR
# =====================================================================
@auth_bp.route("/2fa-disable", methods=["POST"])
@login_required
def twofa_disable():
    """
    Permite desactivar el 2FA.
    """
    if not getattr(current_user, "twofa_enabled", False):
        flash("No tienes 2FA activado.", "info")
        return redirect(url_for("auth.perfil_usuario"))

    current = request.form.get("current_password", "")

    if not current_user.check_password(current):
        flash("La contraseña actual es incorrecta.", "danger")
        return redirect(url_for("auth.perfil_usuario"))

    current_user.twofa_enabled = False
    current_user.twofa_secret = None
    db.session.commit()

    flash("2FA desactivado correctamente.", "success")
    return redirect(url_for("auth.perfil_usuario"))


# =====================================================================
# 📊 HELPER: KPIs + ACTIVIDAD USUARIO
# =====================================================================
def _get_kpis_y_actividad():
    """
    Devuelve:
    - kpi_inventarios
    - kpi_bultos
    - kpi_alertas
    - perfil_completado
    - actividad (últimos logs)
    """

    # KPIs
    try:
        from models.inventory import InventoryItem
        kpi_inventarios = InventoryItem.query.count()
    except Exception:
        kpi_inventarios = 0

    try:
        from models.bultos import Bulto
        kpi_bultos = Bulto.query.count()
    except Exception:
        kpi_bultos = 0

    try:
        from models.alerts import Alerta
        kpi_alertas = Alerta.query.count()
    except Exception:
        kpi_alertas = 0

    # Perfil completado
    perfil_completado = getattr(current_user, "perfil_completado", 0) or 0

    # Actividad
    try:
        from models.actividad import ActividadUsuario
        actividad = (
            ActividadUsuario.query
            .filter_by(user_id=current_user.id)
            .order_by(ActividadUsuario.fecha.desc())
            .limit(15)
            .all()
        )
    except Exception:
        actividad = []

    return kpi_inventarios, kpi_bultos, kpi_alertas, perfil_completado, actividad


# =====================================================================
# 👤 PERFIL DEL USUARIO
# =====================================================================
@auth_bp.route("/perfil")
@login_required
def perfil_usuario():
    """
    Muestra datos del usuario + algunos KPIs y actividad reciente.
    """
    kpi_inventarios, kpi_bultos, kpi_alertas, perfil_completado, actividad = _get_kpis_y_actividad()

    return render_template(
        "perfil_usuario.html",
        kpi_inventarios=kpi_inventarios,
        kpi_bultos=kpi_bultos,
        kpi_alertas=kpi_alertas,
        perfil_completado=perfil_completado,
        actividad=actividad,
    )


# =====================================================================
# ✏ EDITAR PERFIL BÁSICO
# =====================================================================
@auth_bp.route("/editar", methods=["GET", "POST"])
@login_required
def edit_user():
    """
    Permite editar los campos básicos del usuario:
    email, teléfono, ubicación, área.
    """

    if request.method == "POST":
        current_user.email = request.form.get("email") or None
        current_user.phone = request.form.get("phone") or None
        current_user.location = request.form.get("location") or None
        current_user.area = request.form.get("area") or None

        # Recalcular perfil_completado si tu modelo tiene ese método
        if hasattr(current_user, "actualizar_perfil"):
            current_user.actualizar_perfil(
                email=current_user.email,
                phone=current_user.phone,
                location=current_user.location,
                area=current_user.area,
            )
        else:
            db.session.commit()

        flash("Cambios guardados correctamente.", "success")
        return redirect(url_for("auth.perfil_usuario"))

    return render_template("auth/edit_user.html")


# =====================================================================
# 🔑 CAMBIAR CONTRASEÑA SEGURA
# =====================================================================
@auth_bp.route("/cambiar-password", methods=["GET", "POST"])
@login_required
def cambiar_password():
    """
    Permite cambiar la contraseña actual con validación fuerte.
    """

    if request.method == "POST":
        current = request.form.get("current_password", "")
        new = request.form.get("new_password", "")
        confirm = request.form.get("confirm_password", "")

        # Validar contraseña actual
        if not current_user.check_password(current):
            flash("La contraseña actual es incorrecta.", "danger")
            return redirect(url_for('auth.cambiar_password'))

        # Validar coincidencia
        if new != confirm:
            flash("La nueva contraseña no coincide con la confirmación.", "danger")
            return redirect(url_for("auth.cambiar_password"))

        # Validar reglas
        errores = validar_password(new)
        if errores:
            for e in errores:
                flash(e, "danger")
            return redirect(url_for("auth.cambiar_password"))

        # Evitar que sea igual a la anterior
        if current_user.check_password(new):
            flash("La nueva contraseña no puede ser igual a la anterior.", "danger")
            return redirect(url_for("auth.cambiar_password"))

        # Guardar nueva contraseña
        current_user.set_password(new)
        db.session.commit()

        flash("Contraseña actualizada correctamente.", "success")
        return redirect(url_for("auth.perfil_usuario"))

    return render_template("auth/change_password.html")


# =====================================================================
# 🖼 SUBIR FOTO DE PERFIL
# =====================================================================
@auth_bp.route("/subir-foto", methods=["GET", "POST"])
@login_required
def subir_foto():
    """
    Sube una foto de perfil JPG/PNG.
    Se guarda en static/uploads/users/user_<id>.ext
    """

    upload_folder = os.path.join(current_app.root_path, "static", "uploads", "users")
    os.makedirs(upload_folder, exist_ok=True)

    if request.method == "POST":

        if "photo" not in request.files:
            flash("No enviaste ninguna imagen.", "danger")
            return redirect(url_for("auth.subir_foto"))

        file = request.files["photo"]

        if file.filename == "":
            flash("Sube una imagen válida.", "warning")
            return redirect(url_for("auth.subir_foto"))

        ext = file.filename.rsplit(".", 1)[-1].lower()
        if ext not in {"jpg", "jpeg", "png"}:
            flash("Formato no permitido. Solo JPG/PNG.", "danger")
            return redirect(url_for("auth.subir_foto"))

        filename = secure_filename(f"user_{current_user.id}.{ext}")
        path = os.path.join(upload_folder, filename)

        file.save(path)

        # Guardar ruta en DB
        current_user.photo = f"uploads/users/{filename}"
        db.session.commit()

        flash("Foto actualizada correctamente.", "success")
        return redirect(url_for("auth.perfil_usuario"))

    return render_template("auth/upload_photo.html")


# =====================================================================
# 📂 PORTAL DE REPORTES PDF
# =====================================================================
@auth_bp.route("/reportes")
@login_required
def reportes_usuario():
    """
    Muestra el menú de reportes PDF para el usuario.
    """
    return render_template("auth/reportes_usuario.html")


# =====================================================================
# 📄 PDF 1 — NIVEL GERENCIA
# =====================================================================
@auth_bp.route("/descargar-datos")
@login_required
def descargar_datos_gerencia():
    """
    Genera un PDF de nivel gerencial con datos del usuario
    y algunos KPIs básicos.
    """
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from reportlab.lib.utils import ImageReader
    import io
    import qrcode

    (kpi_inventarios,
     kpi_bultos,
     kpi_alertas,
     perfil_completado,
     actividad) = _get_kpis_y_actividad()

    reports_folder = os.path.join(current_app.root_path, "static", "reports")
    os.makedirs(reports_folder, exist_ok=True)

    pdf_path = os.path.join(
        reports_folder,
        f"perfil_usuario_{current_user.id}_GERENCIA.pdf"
    )

    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter

    # Marca de agua suave
    c.saveState()
    c.setFont("Helvetica-Bold", 50)
    c.setFillColorRGB(0.95, 0.95, 0.95)
    c.translate(width / 4, height / 3)
    c.rotate(45)
    c.drawString(0, 0, "CONFIDENCIAL - GERENCIA")
    c.restoreState()

    # Encabezado azul Gerdau
    c.setFillColorRGB(0, 59/255, 113/255)
    c.rect(0, height - 90, width, 90, fill=1)

    c.setFont("Helvetica-Bold", 22)
    c.setFillColor(colors.white)
    c.drawString(30, height - 55, "Reporte de Usuario — Nivel Gerencial")

    c.setFont("Helvetica", 11)
    c.drawString(30, height - 70, "Sistema Warehouse MRO — SIDERPERU / GERDAU")

    # Logos
    try:
        sider_logo = os.path.join(current_app.root_path, "static", "img", "siderperu_logo.jpg")
        if os.path.exists(sider_logo):
            c.drawImage(sider_logo, width - 260, height - 82, width=120, height=50, mask="auto")
    except Exception:
        pass

    try:
        gerdau_logo = os.path.join(current_app.root_path, "static", "img", "gerdau_logo.jpg")
        if os.path.exists(gerdau_logo):
            c.drawImage(gerdau_logo, width - 130, height - 82, width=110, height=50, mask="auto")
    except Exception:
        pass

    # Bloque datos
    y = height - 120
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(colors.black)
    c.drawString(30, y, f"Usuario: {current_user.username}")
    y -= 20
    c.setFont("Helvetica", 12)
    c.drawString(30, y, f"Rol: {current_user.role}")
    y -= 20
    c.drawString(30, y, f"Correo: {current_user.email or 'No registrado'}")
    y -= 20
    c.drawString(30, y, f"Teléfono: {current_user.phone or 'No registrado'}")
    y -= 20
    c.drawString(30, y, f"Ubicación: {current_user.location or 'No registrada'}")
    y -= 20
    c.drawString(30, y, f"Área: {current_user.area or 'No asignada'}")
    y -= 20
    creado = current_user.created_at.strftime("%d/%m/%Y") if getattr(current_user, "created_at", None) else "Sin registro"
    c.drawString(30, y, f"Miembro desde: {creado}")
    y -= 20
    c.drawString(30, y, f"Perfil completado: {perfil_completado}%")

    # KPIs simples
    y -= 40
    c.setFont("Helvetica-Bold", 13)
    c.drawString(30, y, "Indicadores Operativos:")
    y -= 20
    c.setFont("Helvetica", 12)
    c.drawString(40, y, f"- Inventarios subidos: {kpi_inventarios}")
    y -= 18
    c.drawString(40, y, f"- Bultos registrados: {kpi_bultos}")
    y -= 18
    c.drawString(40, y, f"- Alertas reportadas: {kpi_alertas}")

    # QR con ID + fecha
    security_code = f"SEC-{current_user.id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    dashboard_url = url_for("dashboard.dashboard", _external=True)

    qr_buf = io.BytesIO()
    qr = qrcode.QRCode(box_size=3, border=2)
    qr.add_data(f"{dashboard_url} | {security_code}")
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="black", back_color="white")
    img_qr.save(qr_buf, format="PNG")
    qr_buf.seek(0)
    c.drawImage(ImageReader(qr_buf), width - 120, y - 80, width=80, height=80, mask="auto")

    # Actividad (resumen)
    y -= 120
    c.setFont("Helvetica-Bold", 13)
    c.drawString(30, y, "Actividad reciente:")
    y -= 20
    c.setFont("Helvetica", 10)

    if actividad:
        for log in actividad[:8]:
            if y < 60:
                c.showPage()
                y = height - 60
            fecha_txt = log.fecha.strftime("%d/%m/%Y %H:%M")
            c.drawString(30, y, f"{fecha_txt} — {log.descripcion[:80]}")
            y -= 15
    else:
        c.drawString(30, y, "No hay actividad registrada.")

    # Footer
    c.setFillColorRGB(0, 59/255, 113/255)
    c.rect(0, 0, width, 35, fill=1)
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.white)
    c.drawString(30, 15, "Reporte gerencial generado automáticamente — Warehouse MRO – SIDERPERU / GERDAU")
    c.drawRightString(width - 30, 15, f"Código: {security_code}")

    c.save()
    return send_file(pdf_path, as_attachment=True)


# =====================================================================
# 📄 PDF 2 — NIVEL CORPORATIVO
# =====================================================================
@auth_bp.route("/descargar-datos-corporativo")
@login_required
def descargar_datos_corporativo():
    """
    Genera un PDF con gráficos de barras y pie para
    consumo a nivel corporativo.
    """
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.graphics.shapes import Drawing
    from reportlab.graphics.charts.barcharts import VerticalBarChart
    from reportlab.graphics.charts.piecharts import Pie
    from reportlab.graphics import renderPDF
    from reportlab.lib import colors
    from reportlab.lib.utils import ImageReader
    import io
    import qrcode

    (kpi_inventarios,
     kpi_bultos,
     kpi_alertas,
     perfil_completado,
     actividad) = _get_kpis_y_actividad()

    reports_folder = os.path.join(current_app.root_path, "static", "reports")
    os.makedirs(reports_folder, exist_ok=True)

    pdf_path = os.path.join(
        reports_folder,
        f"perfil_usuario_{current_user.id}_CORPORATIVO.pdf"
    )

    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter

    # Portada
    c.setFillColorRGB(1, 1, 1)
    c.rect(0, 0, width, height, fill=1)

    try:
        sider_logo = os.path.join(current_app.root_path, "static", "img", "siderperu_logo.jpg")
        if os.path.exists(sider_logo):
            c.drawImage(sider_logo, 40, height - 140, width=220, height=70, mask="auto")
    except Exception:
        pass

    c.setFont("Helvetica-Bold", 26)
    c.setFillColorRGB(0, 59/255, 113/255)
    c.drawString(40, height - 190, "Reporte Corporativo de Usuario")

    c.setFont("Helvetica", 13)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(40, height - 220, "Sistema Warehouse MRO – SIDERPERU / GERDAU")
    c.drawString(40, height - 240, f"Usuario: {current_user.username}")
    c.drawString(40, height - 260, f"Generado el: {datetime.utcnow().strftime('%d/%m/%Y %H:%M')}")

    c.showPage()

    # Página 2: datos + gráficos
    width, height = letter

    # Encabezado
    c.setFillColorRGB(0, 59/255, 113/255)
    c.rect(0, height - 60, width, 60, fill=1)
    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(colors.white)
    c.drawString(30, height - 40, "Ficha de Usuario y KPIs")

    # Datos
    y = height - 90
    c.setFont("Helvetica-Bold", 13)
    c.setFillColor(colors.black)
    c.drawString(30, y, "Datos del usuario")
    y -= 20
    c.setFont("Helvetica", 11)
    c.drawString(30, y, f"Usuario: {current_user.username}")
    y -= 15
    c.drawString(30, y, f"Rol: {current_user.role}")
    y -= 15
    c.drawString(30, y, f"Correo: {current_user.email or 'No registrado'}")
    y -= 15
    c.drawString(30, y, f"Teléfono: {current_user.phone or 'No registrado'}")
    y -= 15
    c.drawString(30, y, f"Ubicación: {current_user.location or 'No registrada'}")
    y -= 15
    c.drawString(30, y, f"Área: {current_user.area or 'No asignada'}")
    y -= 15
    creado = current_user.created_at.strftime("%d/%m/%Y") if getattr(current_user, "created_at", None) else "Sin registro"
    c.drawString(30, y, f"Miembro desde: {creado}")
    y -= 15
    c.drawString(30, y, f"Perfil completado: {perfil_completado}%")

    # Gráfico de barras
    chart = Drawing(320, 180)
    bar = VerticalBarChart()
    bar.x = 40
    bar.y = 30
    bar.height = 130
    bar.width = 240
    bar.data = [[kpi_inventarios, kpi_bultos, kpi_alertas]]
    bar.categoryAxis.categoryNames = ["Inventarios", "Bultos", "Alertas"]
    bar.valueAxis.valueMin = 0
    max_val = max(bar.data[0]) if max(bar.data[0]) > 0 else 1
    bar.valueAxis.valueMax = max_val * 1.2
    bar.valueAxis.valueStep = max(1, int(max_val / 5))
    bar.bars[0].fillColor = colors.Color(0/255, 59/255, 113/255)
    chart.add(bar)
    renderPDF.draw(chart, c, 250, height - 280)

    # Gráfico pie
    total = kpi_inventarios + kpi_bultos + kpi_alertas
    if total > 0:
        pie_draw = Drawing(180, 160)
        pie = Pie()
        pie.x = 30
        pie.y = 15
        pie.width = 120
        pie.height = 120
        pie.data = [kpi_inventarios, kpi_bultos, kpi_alertas]
        pie.labels = ["Inv", "Bultos", "Alertas"]
        pie.slices[0].fillColor = colors.Color(0/255, 59/255, 113/255)
        pie.slices[1].fillColor = colors.Color(248/255, 192/255, 0/255)
        pie.slices[2].fillColor = colors.red
        pie_draw.add(pie)
        renderPDF.draw(pie_draw, c, 40, height - 380)

    # QR corporativo
    security_code = f"CORP-{current_user.id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    dashboard_url = url_for("dashboard.dashboard", _external=True)
    import io, qrcode
    from reportlab.lib.utils import ImageReader

    qr_buf = io.BytesIO()
    qr = qrcode.QRCode(box_size=3, border=2)
    qr.add_data(f"{dashboard_url} | {security_code}")
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="black", back_color="white")
    img_qr.save(qr_buf, format="PNG")
    qr_buf.seek(0)
    c.drawImage(ImageReader(qr_buf), width - 100, 60, width=60, height=60, mask="auto")

    # Footer
    c.setFillColorRGB(0, 59/255, 113/255)
    c.rect(0, 0, width, 35, fill=1)
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.white)
    c.drawString(30, 15, "Reporte corporativo — Warehouse MRO – SIDERPERU / GERDAU")
    c.drawRightString(width - 30, 15, f"Código: {security_code}")

    c.save()
    return send_file(pdf_path, as_attachment=True)


# =====================================================================
# 📄 PDF 3 — ESTILO TESIS
# =====================================================================
@auth_bp.route("/descargar-datos-tesis")
@login_required
def descargar_datos_tesis():
    """
    Genera un reporte estilo tesis con capítulos:
    I. Datos generales
    II. Resultados (KPIs)
    III. Conclusiones y Recomendaciones
    """
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors

    (kpi_inventarios,
     kpi_bultos,
     kpi_alertas,
     perfil_completado,
     actividad) = _get_kpis_y_actividad()

    reports_folder = os.path.join(current_app.root_path, "static", "reports")
    os.makedirs(reports_folder, exist_ok=True)

    pdf_path = os.path.join(
        reports_folder,
        f"perfil_usuario_{current_user.id}_TESIS.pdf"
    )

    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter

    # Portada
    c.setFont("Times-Bold", 18)
    c.drawCentredString(width/2, height - 80, "SIDERPERU – GERDAU")
    c.setFont("Times-Bold", 16)
    c.drawCentredString(width/2, height - 110, "Sistema Warehouse MRO")
    c.setFont("Times-Bold", 14)
    c.drawCentredString(width/2, height - 150, "REPORTE ESTILO TESIS DEL USUARIO")
    c.setFont("Times-Roman", 12)
    c.drawCentredString(width/2, height - 190, f"Usuario: {current_user.username}")
    c.drawCentredString(width/2, height - 210, f"Fecha: {datetime.utcnow().strftime('%d/%m/%Y')}")
    c.showPage()

    # Capítulo I — Datos generales
    c.setFont("Times-Bold", 14)
    c.drawString(60, height - 80, "CAPÍTULO I: DATOS GENERALES DEL USUARIO")
    y = height - 110
    c.setFont("Times-Roman", 12)
    c.drawString(60, y, f"Usuario: {current_user.username}")
    y -= 18
    c.drawString(60, y, f"Rol en el sistema: {current_user.role}")
    y -= 18
    c.drawString(60, y, f"Correo: {current_user.email or 'No registrado'}")
    y -= 18
    c.drawString(60, y, f"Teléfono: {current_user.phone or 'No registrado'}")
    y -= 18
    c.drawString(60, y, f"Ubicación: {current_user.location or 'No registrada'}")
    y -= 18
    c.drawString(60, y, f"Área: {current_user.area or 'No asignada'}")
    y -= 18
    creado = current_user.created_at.strftime("%d/%m/%Y") if getattr(current_user, "created_at", None) else "Sin registro"
    c.drawString(60, y, f"Miembro desde: {creado}")
    y -= 18
    c.drawString(60, y, f"Porcentaje de perfil completado: {perfil_completado}%")
    c.showPage()

    # Capítulo II — Resultados (KPIs)
    c.setFont("Times-Bold", 14)
    c.drawString(60, height - 80, "CAPÍTULO II: RESULTADOS (KPIs)")
    y = height - 110
    c.setFont("Times-Roman", 12)
    c.drawString(60, y, "2.1 Indicadores cuantitativos")
    y -= 20
    c.drawString(80, y, f"- Inventarios subidos: {kpi_inventarios}")
    y -= 18
    c.drawString(80, y, f"- Bultos registrados: {kpi_bultos}")
    y -= 18
    c.drawString(80, y, f"- Alertas reportadas: {kpi_alertas}")
    y -= 30

    c.drawString(60, y, "2.2 Interpretación de resultados:")
    y -= 20
    c.setFont("Times-Roman", 11)
    texto = (
        "Los indicadores muestran el nivel de participación del usuario dentro del sistema "
        "Warehouse MRO. Un mayor número de inventarios, bultos y alertas registradas "
        "evidencia un uso activo de la herramienta y una contribución directa a la gestión "
        "operativa del almacén industrial."
    )
    for linea in texto.split(". "):
        c.drawString(80, y, linea.strip())
        y -= 15

    c.showPage()

    # Capítulo III — Conclusiones y Recomendaciones
    c.setFont("Times-Bold", 14)
    c.drawString(60, height - 80, "CAPÍTULO III: CONCLUSIONES Y RECOMENDACIONES")
    y = height - 110

    c.setFont("Times-Bold", 12)
    c.drawString(60, y, "3.1 Conclusiones")
    y -= 20
    c.setFont("Times-Roman", 11)
    conclusiones = [
        "El usuario participa activamente en el registro de información clave para la gestión del almacén.",
        "El uso del sistema Warehouse MRO contribuye a mejorar la trazabilidad y control de materiales.",
        "La información registrada por el usuario es base para la toma de decisiones en la operación."
    ]
    for c_text in conclusiones:
        c.drawString(80, y, f"• {c_text}")
        y -= 15

    y -= 10
    c.setFont("Times-Bold", 12)
    c.drawString(60, y, "3.2 Recomendaciones")
    y -= 20
    c.setFont("Times-Roman", 11)
    recomendaciones = [
        "Mantener actualizado el registro de inventarios y bultos en cada turno.",
        "Reportar oportunamente cualquier incidencia mediante el módulo de alertas.",
        "Participar en las capacitaciones sobre el uso del sistema para aprovechar al máximo sus funciones."
    ]
    for r_text in recomendaciones:
        c.drawString(80, y, f"• {r_text}")
        y -= 15

    c.showPage()
    c.save()
    return send_file(pdf_path, as_attachment=True)
