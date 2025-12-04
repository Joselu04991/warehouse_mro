# routes/__init__.py

from .dashboard_routes import dashboard_bp
from .auth_routes import auth_bp
from .inventory_routes import inventory_bp
from .warehouse2d_routes import warehouse2d_bp
from .bultos_routes import bultos_bp
from .alerts_routes import alerts_bp
from .technician_errors_routes import technician_errors_bp
from .equipos_routes import equipos_bp
from .productividad_routes import productividad_bp
from .qr_routes import qr_bp
from .auditoria_routes import auditoria_bp
from .alertas_ai_routes import alertas_ai_bp
from .admin_roles_routes import roles_bp

def register_blueprints(app):

    print("\n========== CARGANDO BLUEPRINTS ==========\n")

    # 👉 ORDER: primero rutas principales, luego módulos secundarios
    app.register_blueprint(auth_bp)                # Login debe ir primero siempre
    print("👉 Cargado: auth")

    app.register_blueprint(dashboard_bp)
    print("👉 Cargado: dashboard")

    app.register_blueprint(inventory_bp)
    print("👉 Cargado: inventario")

    app.register_blueprint(warehouse2d_bp)
    print("👉 Cargado: warehouse2d")

    app.register_blueprint(bultos_bp)
    print("👉 Cargado: bultos")

    app.register_blueprint(alerts_bp)
    print("👉 Cargado: alertas")

    app.register_blueprint(technician_errors_bp)
    print("👉 Cargado: errores_tecnicos")

    app.register_blueprint(equipos_bp)
    print("👉 Cargado: equipos")

    app.register_blueprint(productividad_bp)
    print("👉 Cargado: productividad")

    app.register_blueprint(qr_bp)
    print("👉 Cargado: qr")

    app.register_blueprint(auditoria_bp)
    print("👉 Cargado: auditoria")

    app.register_blueprint(alertas_ai_bp)
    print("👉 Cargado: alertas_ai")

    app.register_blueprint(roles_bp)
    print("👉 Cargado: roles")
    print("\n========== BLUEPRINTS CARGADOS OK ==========\n")
