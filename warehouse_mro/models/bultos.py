from models import db
from datetime import datetime

class Bulto(db.Model):
    __tablename__ = "bultos"

    id = db.Column(db.Integer, primary_key=True)
    cantidad = db.Column(db.Integer, nullable=False)
    chofer = db.Column(db.String(120), nullable=False)
    placa = db.Column(db.String(20), nullable=False)
    fecha_hora = db.Column(db.DateTime, default=datetime.now)
    observacion = db.Column(db.String(255))

    creado_en = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f"<Bulto {self.id} - {self.placa}>"
