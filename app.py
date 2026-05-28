import os
import mysql.connector
from routes.auth import (
    auth_bp,
    User,
    solo_admin
)
from routes.contratos import contratos_bp
from routes.proyectos import proyectos_bp
from routes.visitas import visitas_bp
from database import conectar_db
from functools import wraps
from dotenv import load_dotenv
from config import Config
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)
from flask_wtf.csrf import CSRFProtect
from werkzeug.utils import secure_filename

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    abort,
    flash,
    url_for
)

from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user
)


# =========================
# CONFIGURACIÓN FLASK
# =========================

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = app.config['SECRET_KEY']
csrf = CSRFProtect(app)

# =========================
# LOGIN MANAGER
# =========================

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
app.register_blueprint(auth_bp)
app.register_blueprint(proyectos_bp)
app.register_blueprint(contratos_bp)
app.register_blueprint(visitas_bp)
@login_manager.user_loader
def load_user(user_id):

    conexion = conectar_db()

    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            id_usuario,
            nombre,
            usuario,
            rol
        FROM usuarios
        WHERE id_usuario = %s
    """, (user_id,))

    usuario_db = cursor.fetchone()

    conexion.close()

    if usuario_db:

        return User(
            usuario_db[0],
            usuario_db[1],
            usuario_db[2],
            usuario_db[3]
        )

    return None

# =========================
# FUNCIONES AUXILIARES
# =========================
app.config['UPLOAD_FOLDER_CONTRATOS'] = (
    'static/uploads/contratos'
)
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

def archivo_permitido(nombre_archivo):

    return (
        '.' in nombre_archivo and
        nombre_archivo.rsplit('.', 1)[1].lower()
        in app.config['ALLOWED_EXTENSIONS']
    )

    # =========================
    # SUBIDA DE ARCHIVO
    # =========================

    if archivo and archivo.filename != '':

        if archivo_permitido(archivo.filename):

            # OBTENER EXTENSIÓN
            extension = archivo.filename.rsplit('.', 1)[1].lower()

            # NOMBRE ÚNICO
            nombre_unico = f"{uuid.uuid4()}.{extension}"

            # NOMBRE SEGURO
            nombre_seguro = secure_filename(nombre_unico)

            # RUTA COMPLETA
            ruta_guardado = os.path.join(
                app.config['UPLOAD_FOLDER'],
                nombre_seguro
            )

            # GUARDAR ARCHIVO
            archivo.save(ruta_guardado)

            # GUARDAR RUTA EN DB
            nombre_archivo = ruta_guardado

        else:

            return """
            ⚠️ Tipo de archivo no permitido.
            Solo PDF y Excel.
            """

    # =========================
    # GUARDAR EN MYSQL
    # =========================

    conexion = conectar_db()

    cursor = conexion.cursor()

    sql = """
        INSERT INTO visitas (
            id_contrato,
            fecha_visita,
            supervisor,
            residente_obra,
            observaciones,
            archivo_acta
        )
        VALUES (%s, %s, %s, %s, %s, %s)
    """

    valores = (
        id_contrato,
        fecha,
        supervisor,
        residente,
        observaciones,
        nombre_archivo
    )

    cursor.execute(sql, valores)
    conexion.commit()
    conexion.close()
    return redirect('/')

#RUTAS------------RUTAS---------------RUTAS------------RUTAS--------------
# ------------------------
# VISITAS GENERALES
# ------------------------
@app.route('/visitas')
@login_required
def ver_visitas():

    conexion = conectar_db()
    cursor = conexion.cursor()

    busqueda = request.args.get('busqueda')

    if busqueda:

        cursor.execute("""
            SELECT 
                v.id_visita,
                c.no_contrato,
                p.nombre,
                v.fecha_visita,
                v.supervisor,
                v.residente_obra,
                v.observaciones,
                v.archivo_acta

            FROM visitas v

            JOIN contratos c 
                ON v.id_contrato = c.id_contrato

            JOIN proyectos p 
                ON c.id_proyecto = p.id_proyecto

            WHERE p.nombre LIKE %s

            ORDER BY v.fecha_visita DESC

        """, (f"%{busqueda}%",))

    else:

        cursor.execute("""
            SELECT 
                v.id_visita,
                c.no_contrato,
                p.nombre,
                v.fecha_visita,
                v.supervisor,
                v.residente_obra,
                v.observaciones,
                v.archivo_acta

            FROM visitas v

            JOIN contratos c 
                ON v.id_contrato = c.id_contrato

            JOIN proyectos p 
                ON c.id_proyecto = p.id_proyecto

            ORDER BY v.fecha_visita DESC
        """)

    visitas = cursor.fetchall()

    conexion.close()

    return render_template(
        'visitas.html',
        visitas=visitas
    )
    
# ------------------------
# VISITAS POR PROYECTO
# ------------------------
@app.route('/visitas_proyecto/<int:id_proyecto>')
@login_required
def visitas_proyecto(id_proyecto):
    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("""
            SELECT 
        v.id_visita,
        p.nombre,
        c.no_contrato,
        v.fecha_visita,
        v.supervisor,
        v.residente_obra,
        v.observaciones,
        v.archivo_acta
        FROM visitas v
        JOIN contratos c ON v.id_contrato = c.id_contrato
        JOIN proyectos p ON c.id_proyecto = p.id_proyecto
        WHERE p.id_proyecto = %s
        ORDER BY v.fecha_visita DESC
    """, (id_proyecto,))

    visitas = cursor.fetchall()
    conexion.close()
    return render_template('visitas_proyecto.html', visitas=visitas)

# ------------------------
# EJECUCIÓN
# ------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug = True)