from models import db
from datetime import datetime

class AlertaIA(db.Model):
    __tablename__ = "alertas_ai"

    id = db.Column(db.Integer, primary_key=True)
    categoria = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    nivel = db.Column(db.String(20), default="info")
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<AlertaIA {self.categoria} - {self.nivel}>"
