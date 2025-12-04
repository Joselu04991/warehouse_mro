from functools import wraps
from flask import request
from flask_login import current_user
from models import db
from models.auditoria import Auditoria

def auditar(modulo, accion):
    def wrapper(func):
        @wraps(func)
        def decorated(*args, **kwargs):

            resultado = func(*args, **kwargs)

            try:
                ip = request.remote_addr
                log = Auditoria(
                    user_id=current_user.id,
                    accion=accion,
                    modulo=modulo,
                    ip=ip
                )
                db.session.add(log)
                db.session.commit()
            except:
                pass

            return resultado
        return decorated
    return wrapper
