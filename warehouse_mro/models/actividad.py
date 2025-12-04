from models import db
from datetime import datetime

class ActividadUsuario(db.Model):
    __tablename__ = "actividad_usuario"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)

    descripcion = db.Column(db.String(255), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ActividadUsuario {self.id} - {self.descripcion}>"
