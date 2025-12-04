from models import db
from datetime import datetime

class Productividad(db.Model):
    __tablename__ = "productividad"

    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(120), nullable=False)
    actividad = db.Column(db.String(255), nullable=False)
    duracion = db.Column(db.Float, default=0.0)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Productividad {self.usuario} - {self.actividad}>"
