from flask import Blueprint, render_template
from flask_login import login_required
from models.alerts import Alert

alerts_bp = Blueprint("alerts", __name__, url_prefix="/alerts")

@alerts_bp.route("/")
@login_required
def list_alerts():
    alerts = Alert.query.order_by(Alert.fecha.desc()).all()
    return render_template("alerts/list.html", alerts=alerts)
