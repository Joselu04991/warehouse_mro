from flask import Flask, redirect, url_for
from flask_login import LoginManager
from config import Config
from models import db
from models.user import User
from routes import register_blueprints
import os
# ==============================
# LOGIN MANAGER
# ==============================
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message_category = "info"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ==============================
# FACTORÍA CREATE_APP
# ==============================
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inicializar extensiones
    db.init_app(app)
    login_manager.init_app(app)

    # Registrar blueprints
    register_blueprints(app)

    # Registrar filtros
    @app.template_filter("format_fecha")
    def format_fecha(value):
        try:
            return value.strftime("%d/%m/%Y %H:%M")
        except Exception:
            return value

    # Ruta raíz
    @app.route("/")
    def index():
        return redirect(url_for("auth.login"))

    # Crear tablas y OWNER
    with app.app_context():
        from models.user import User
        from models.inventory import InventoryItem
        from models.bultos import Bulto
        from models.alerts import Alert
        from models.technician_error import TechnicianError
        from models.equipos import Equipo
        from models.productividad import Productividad
        from models.auditoria import Auditoria
        from models.alertas_ai import AlertaIA

        print("\n>>> Creando tablas si no existen...")
        db.create_all()
        db.session.commit()
        print(">>> Tablas creadas.\n")

        # ============================
        # CREAR TU USUARIO OWNER AQUÍ
        # ============================
        owner_email = "jose.castillo@sider.com.pe"
        owner_username = "JCASTI15"
        owner_password = "Admin123#"

        owner = User.query.filter_by(email=owner_email).first()

        if not owner:
            print(">>> Creando usuario OWNER...")

            new_owner = User(
                username=owner_username,
                email=owner_email,
                role="owner",
                status="active",
                email_confirmed=True,
            )
            new_owner.set_password(owner_password)

            db.session.add(new_owner)
            db.session.commit()

            print(">>> OWNER creado correctamente.")
        else:
            # Reforzar que siempre sea OWNER
            owner.role = "owner"
            owner.email_confirmed = True
            db.session.commit()
            print(">>> OWNER verificado y actualizado.")

    return app


# ==============================
# EJECUTAR SERVIDOR LOCAL
# ==============================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))


