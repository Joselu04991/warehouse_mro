from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Importar los modelos para registrarlos
from .user import User
from .inventory import InventoryItem
from .bultos import Bulto
from .alerts import Alert
from .technician_error import TechnicianError
from .equipos import Equipo
from .productividad import Productividad
from .auditoria import Auditoria
from .alertas_ai import AlertaIA
