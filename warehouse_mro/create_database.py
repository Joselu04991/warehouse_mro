from app import app
from models import db
from models.user import User


with app.app_context():
    db.create_all()

    if not User.query.filter_by(username="admin").first():
        admin = User(username="admin", role="admin")
        admin.set_password("admin")
        db.session.add(admin)
        db.session.commit()
        print("Usuario admin/admin creado.")
    else:
        print("El usuario admin ya existe.")
