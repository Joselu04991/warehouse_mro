from models import db
from datetime import datetime

class RegistroTurno(db.Model):
    __tablename__ = "registro_turno"

    id = db.Column(db.Integer, primary_key=True)
    turno = db.Column(db.String(20))  # Mañana, Tarde, Noche
    user_id = db.Column(db.Integer)
    registros = db.Column(db.Integer, default=0)
    fecha = db.Column(db.Date)
