from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    flash,
    url_for
)

from flask_login import (
    login_user,
    logout_user,
    login_required,
    UserMixin
)

from werkzeug.security import check_password_hash
from utils.auditoria import registrar_auditoria
from functools import wraps
from flask import abort
from flask_login import current_user
from database import conectar_db


# =========================
# BLUEPRINT
# =========================

auth_bp = Blueprint(
    'auth',
    __name__
)


# =========================
# USER CLASS
# =========================

class User(UserMixin):

    def __init__(self, id, nombre, usuario, rol):

        self.id = id
        self.nombre = nombre
        self.usuario = usuario
        self.rol = rol


# =========================
# DECORADOR ADMIN
# =========================

def solo_admin(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):

        if current_user.rol != 'admin':
            abort(403)

        return f(*args, **kwargs)

    return decorated_function


# =========================
# LOGIN
# =========================

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        usuario = request.form['usuario']
        password = request.form['password']

        conexion = conectar_db()
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT
                id_usuario,
                nombre,
                usuario,
                password,
                rol
            FROM usuarios
            WHERE usuario = %s
        """, (usuario,))

        usuario_db = cursor.fetchone()

        conexion.close()

        if usuario_db and check_password_hash(usuario_db[3], password):

            user = User(
                usuario_db[0],
                usuario_db[1],
                usuario_db[2],
                usuario_db[4]
            )

            login_user(user)
            
            registrar_auditoria(
                user.nombre,
                'Inició sesión',
                'auth',
                request.remote_addr
            )

            return redirect('/')

        return "⚠️ Usuario o contraseña incorrectos"

    return render_template('login.html')


# ------------------------
# CERRAR SESIÓN (LOGOUT)
# ------------------------
@auth_bp.route('/logout')
@login_required
def logout():

    nombre_usuario = current_user.nombre

    registrar_auditoria(
        nombre_usuario,
        'Cerró sesión',
        'login',
        request.remote_addr
    )

    logout_user()

    flash('Sesión cerrada correctamente')

    return redirect(url_for('auth.login'))
