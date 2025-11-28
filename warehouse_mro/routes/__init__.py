# routes/__init__.py

from .dashboard_routes import dashboard_bp
from .inventory_routes import inventory_bp
from .warehouse2d_routes import warehouse2d_bp
from .bultos_routes import bultos_bp
from .alerts_routes import alerts_bp
from .technician_errors_routes import technician_errors_bp
from .auth_routes import auth_bp
from routes.analisis_oc_routes import analisis_oc_bp

def register_blueprints(app):

    # Dashboard principal
    app.register_blueprint(dashboard_bp)

    # Inventario general
    app.register_blueprint(inventory_bp)

    # Mapa 2D avanzado
    app.register_blueprint(warehouse2d_bp)

    # Módulo de bultos (ingresos de camiones)
    app.register_blueprint(bultos_bp)

    # Alertas (críticos, stock, sistema)
    app.register_blueprint(alerts_bp)

    # Errores técnicos (impacto económico)
    app.register_blueprint(technician_errors_bp)

    # Autenticación (login, registro usuarios)
    app.register_blueprint(auth_bp)

    app.register_blueprint(analisis_oc_bp)