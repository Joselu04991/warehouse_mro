from datetime import datetime
from . import db

class TechnicianError(db.Model):
    __tablename__ = "technician_errors"

    id = db.Column(db.Integer, primary_key=True)

    # Técnico responsable
    tecnico = db.Column(db.String(120), nullable=False)

    # Tipo de error (operativo, inventario, sistema, etc.)
    tipo_error = db.Column(db.String(120), nullable=False)

    # Nivel de gravedad (bajo, medio, alto)
    gravedad = db.Column(db.String(50), nullable=False)

    # Observación escrita
    observacion = db.Column(db.Text, nullable=True)

    # Pérdidas económicas
    dinero_perdido = db.Column(db.Float, nullable=False, default=0.0)

    # Puntaje automático
    puntaje = db.Column(db.Integer, nullable=False, default=0)

    # Fecha del error
    fecha_hora = db.Column(db.DateTime, default=datetime.utcnow)

    # Fecha de creación del registro (para el dashboard)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
