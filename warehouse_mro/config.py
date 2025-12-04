import os

# Ruta base del proyecto
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Clave secreta Flask
    SECRET_KEY = "clave_super_secreta_mro_2025"

    # 🔥 Base de datos nueva para evitar conflictos
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'warehouse_mro_v2.db')}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Carpetas
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    REPORT_FOLDER = os.path.join(BASE_DIR, "static", "reports")

# Crear carpetas automáticamente si no existen
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(Config.REPORT_FOLDER, exist_ok=True)


