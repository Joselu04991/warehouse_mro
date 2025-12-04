from flask import Flask, redirect, url_for
from flask_login import LoginManager
from config import Config
from models import db
from models.user import User
from routes import register_blueprints

# ==============================
#  LOGIN MANAGER
# ==============================
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message_category = "info"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ==============================
#  FACTORÍA CREATE_APP
# ==============================
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inicializar extensiones
    db.init_app(app)
    login_manager.init_app(app)

    # Registrar Blueprints
    register_blueprints(app)

    # Registrar filtros ANTES del return
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

    # Crear tablas
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
        print(">>> Tablas creadas.\n")

    return app


# ==============================
#  EJECUTAR SERVIDOR
# ==============================
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
