from models import db
from datetime import datetime

class Auditoria(db.Model):
    __tablename__ = "auditoria"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    accion = db.Column(db.String(255))
    modulo = db.Column(db.String(100))
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    ip = db.Column(db.String(100))
