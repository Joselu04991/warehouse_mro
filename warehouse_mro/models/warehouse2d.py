from datetime import datetime
from . import db

class WarehouseLocation(db.Model):
    __tablename__ = "warehouse_locations"

    id = db.Column(db.Integer, primary_key=True)

    material_code = db.Column(db.String(64), nullable=True, index=True)
    material_text = db.Column(db.String(255), nullable=True)
    base_unit = db.Column(db.String(16), nullable=True)

    descripcion = db.Column(db.String(255), nullable=True)  # <-- NUEVO
    consumo_mes = db.Column(db.Float, nullable=False, default=0.0)  # <-- NUEVO

    stock_seguridad = db.Column(db.Float, nullable=False, default=0.0)
    stock_maximo = db.Column(db.Float, nullable=False, default=0.0)
    ubicacion = db.Column(db.String(32), nullable=False, index=True)
    libre_utilizacion = db.Column(db.Float, nullable=False, default=0.0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def status(self) -> str:

        if self.libre_utilizacion <= 0:
            return "vacío"
        if self.stock_maximo <= 0:
            return "normal"

        ratio = self.libre_utilizacion / self.stock_maximo

        if self.libre_utilizacion < self.stock_seguridad:
            return "crítico"
        if ratio < 0.5:
            return "bajo"
        return "normal"
