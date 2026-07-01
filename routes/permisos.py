from functools import wraps

from flask import abort
from flask_login import current_user


def solo_supervisor(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):

        if current_user.rol != 'supervisor':
            abort(403)

        return f(*args, **kwargs)

    return decorated_function
