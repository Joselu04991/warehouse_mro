from flask import Blueprint, render_template, request
from flask_login import login_required
import qrcode
import io
from flask import send_file

qr_bp = Blueprint("qr", __name__, url_prefix="/qr")


@qr_bp.route("/vista")
@login_required
def vista_qr():
    return render_template("qr/vista_qr.html")


@qr_bp.route("/generar", methods=["POST"])
@login_required
def generar_qr():

    data = request.form.get("data", "")
    if data.strip() == "":
        data = "SIN-DATO"

    qr = qrcode.QRCode(box_size=8, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, "PNG")
    buffer.seek(0)

    return send_file(buffer, mimetype="image/png", as_attachment=True, download_name="qr.png")
