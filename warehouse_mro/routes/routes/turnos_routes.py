from flask import Blueprint, jsonify
from models.turnos import RegistroTurno
from models import db
from flask_login import current_user
from datetime import date
import qrcode
import io
from flask import send_file
turno_bp = Blueprint("turno", __name__, url_prefix="/turno")

@turno_bp.route("/registrar/<modulo>")
def registrar_turno(modulo):

    turno_actual = "Mañana"

    registro = RegistroTurno.query.filter_by(
        user_id=current_user.id,
        fecha=date.today(),
        turno=turno_actual
    ).first()

    if not registro:
        registro = RegistroTurno(
            user_id=current_user.id,
            turno=turno_actual,
            fecha=date.today(),
            registros=1
        )
        db.session.add(registro)
    else:
        registro.registros += 1

    db.session.commit()

    return jsonify({"msg": "OK", "turno": turno_actual})

@turno_bp.route("/qr/<codigo>")
def qr(codigo):
    buffer = io.BytesIO()
    img = qrcode.make(f"https://tuapp/material/{codigo}")
    img.save(buffer, "PNG")
    buffer.seek(0)
    return send_file(buffer, mimetype="image/png")