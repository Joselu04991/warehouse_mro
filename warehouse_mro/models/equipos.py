from models import db

class Equipo(db.Model):
    __tablename__ = "equipos"  

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), nullable=False)
    descripcion = db.Column(db.String(200), nullable=False)
    area = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return f"<Equipo {self.codigo}>"
