from app import create_app
from models import db
from models.user import User
import os

app = create_app()

db_path = os.path.join(os.path.dirname(__file__), "warehouse_mro.db")

with app.app_context():

    # ------------------------------
    # ELIMINAR BD SI ESTÁ EN USO
    # ------------------------------
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print(">>> BD eliminada correctamente.")
        except PermissionError:
            print("❌ ERROR: La BD está en uso. Cierra la app antes de continuar.")
            exit()

    # ------------------------------
    # CREAR TABLAS
    # ------------------------------
    print(">>> Creando tablas...")
    db.create_all()

    # ------------------------------
    # CREAR TU USUARIO OWNER
    # ------------------------------
    print(">>> Creando usuario JCASTI15...")

    user = User(
        username="JCASTI15",
        email="jose.castillo@sider.com.pe",
        role="owner",
        status="active",
        email_confirmed=True,     
        perfil_completado=True    
    )
    user.set_password("admin123")

    db.session.add(user)
    db.session.commit()

    print("=========================================")
    print(" Usuario creado correctamente")
    print(" Username: JCASTI15")
    print(" Password: admin123")
    print(" Rol: OWNER")
    print("=========================================")
