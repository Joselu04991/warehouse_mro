from models import db
from datetime import datetime
import json

class Alert(db.Model):
    __tablename__ = "alertas"

    id = db.Column(db.Integer, primary_key=True)

    # Campo REAL que usan tus rutas
    alert_type = db.Column(db.String(50), nullable=True)   # Ej: stock_critico, tecnico, IA

    # Compatibilidad con tu campo antiguo "tipo"
    tipo = db.Column(db.String(50), nullable=True)

    # Campo REAL que usan tus rutas
    message = db.Column(db.Text, nullable=True)

    # Compatibilidad con tu campo antiguo "mensaje"
    mensaje = db.Column(db.String(255), nullable=True)

    # Nivel usado por tus rutas (Alta, Media, Baja)
    severity = db.Column(db.String(20), default="info")  # info, warning, danger, critical

    # Compatibilidad con tu campo anterior "nivel"
    nivel = db.Column(db.String(20), default="info")

    # Área o módulo que genera la alerta
    origen = db.Column(db.String(100), default="Sistema")

    # Usuario que la generó (string simple o id)
    usuario = db.Column(db.String(120), nullable=True)

    # Estado interno
    estado = db.Column(db.String(20), default="activo")  # activo / cerrado

    # Fecha de creación
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    # Datos extras en JSON
    detalles = db.Column(db.Text, nullable=True)

    # ============================================================
    # Normalizador automático: asegura compatibilidad con todo
    # ============================================================
    def __init__(self, **kwargs):
        # Mapea campos que pueden venir desde rutas antiguas
        if "alert_type" in kwargs:
            kwargs.setdefault("tipo", kwargs["alert_type"])
        if "message" in kwargs:
            kwargs.setdefault("mensaje", kwargs["message"])
        if "severity" in kwargs:
            kwargs.setdefault("nivel", kwargs["severity"])

        super().__init__(**kwargs)

    # ============================================================
    # Guardar JSON en dict automáticamente
    # ============================================================
    def set_detalles(self, data: dict):
        self.detalles = json.dumps(data)

    def get_detalles(self):
        try:
            return json.loads(self.detalles) if self.detalles else {}
        except:
            return {}

    def __repr__(self):
        return f"<Alerta {self.tipo or self.alert_type}>"
