from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from models import db

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    role = db.Column(db.String(20), default="user")
    status = db.Column(db.String(20), default="active")

    email_confirmed = db.Column(db.Boolean, default=True)
    email_token = db.Column(db.String(255), nullable=True)

    twofa_secret = db.Column(db.String(50), nullable=True)
    twofa_enabled = db.Column(db.Boolean, default=False)

    failed_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)

    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    phone = db.Column(db.String(20), nullable=True)
    location = db.Column(db.String(100), nullable=True)
    area = db.Column(db.String(100), nullable=True)

    photo = db.Column(db.String(255), nullable=True)
    theme = db.Column(db.String(20), default="light")

    perfil_completado = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
