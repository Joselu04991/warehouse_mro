from models import db
from datetime import datetime

class Alert(db.Model):
    __tablename__ = "alerts"

    id = db.Column(db.Integer, primary_key=True)

    alert_type = db.Column(db.String(50), nullable=False)  # ejemplo: discrepancia, sistema, seguridad
    message = db.Column(db.String(500), nullable=False)
    severity = db.Column(db.String(20), nullable=False, default="Baja")  # Alta / Media / Baja

    created_at = db.Column(db.DateTime, default=datetime.now)

    # CAMPO CORRECTO
    resolved = db.Column(db.Boolean, default=False)

    def resolve(self):
        """Marca la alerta como resuelta"""
        self.resolved = True
        db.session.commit()

    def __repr__(self):
        return f"<Alert {self.alert_type} - {self.severity}>"
