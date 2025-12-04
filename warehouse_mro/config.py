import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "super_secret_key_change_me")

    # Base de datos SQLite
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "warehouse_mro.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Uploads
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB

    # YOLO
    YOLO_MODEL_PATH = os.path.join(BASE_DIR, "static", "models", "yolov8n.pt")


# Crear carpetas necesarias
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
