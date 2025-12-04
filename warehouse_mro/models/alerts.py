from models import db
from datetime import datetime

class Alert(db.Model):
    __tablename__ = "alertas"

    id = db.Column(db.Integer, primary_key=True)

    # Tipo de alerta: STOCK / TECNICO / BULTOS / IA / SISTEMA
    tipo = db.Column(db.String(50), nullable=False)

    # Descripción corta
    mensaje = db.Column(db.String(255), nullable=False)

    # Nivel visual de alerta
    nivel = db.Column(db.String(20), default="info")   # info, warning, danger, critical

    # Área o módulo que genera la alerta
    origen = db.Column(db.String(100), default="Sistema")

    # Usuario que la generó (si aplica)
    usuario = db.Column(db.String(120), nullable=True)

    # Estado
    estado = db.Column(db.String(20), default="activo")  # activo / cerrado

    # Fecha automática
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    # Datos adicionales (JSON)
    detalles = db.Column(db.Text, nullable=True)  # puedes guardar dict -> JSON

    def __repr__(self):
        return f"<Alerta {self.tipo} - {self.mensaje[:20]}>"
