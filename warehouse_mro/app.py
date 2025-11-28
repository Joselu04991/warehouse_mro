from flask import Flask, redirect, url_for
from flask_login import LoginManager
from config import Config
from models import db
from models.user import User
from routes import register_blueprints

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message_category = "info"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    db.init_app(app)
    login_manager.init_app(app)

    # 🔹 Registrar TODAS las rutas
    register_blueprints(app)

    with app.app_context():

        # 🔹 Crear tablas
        db.create_all()

        # 🔹 Crear owner por defecto
        owner = User.query.filter_by(role="owner").first()

        if not owner:
            default_owner = User(
                username="jcasti15",
                role="owner"
            )
            default_owner.set_password("admin123")
            db.session.add(default_owner)
            db.session.commit()
            print(">>> Owner creado: jcasti15 / admin123")

    return app


app = create_app()

@app.route("/")
def index_redirect():
    return redirect(url_for("auth.login"))

if __name__ == "__main__":
    app.run(debug=True)
