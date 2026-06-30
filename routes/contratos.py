from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    flash,
    url_for
)
import os
from werkzeug.utils import secure_filename
from flask import send_from_directory
from flask_login import login_required, current_user
from utils.auditoria import registrar_auditoria
from database import conectar_db

from routes.auth import solo_admin


contratos_bp = Blueprint(
    'contratos',
    __name__
)

# ------------------------
# NUEVO CONTRATO
# ------------------------
@contratos_bp.route('/nuevo_contrato/<int:id_proyecto>')
@login_required
@solo_admin
def nuevo_contrato(id_proyecto):
    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("SELECT id_proyecto, nombre FROM proyectos WHERE id_proyecto = %s", (id_proyecto,))
    proyecto_seleccionado = cursor.fetchone()

    cursor.execute("SELECT id_proyecto, nombre FROM proyectos")
    proyectos = cursor.fetchall()

    conexion.close()

    return render_template(
        'nuevo_contrato.html',
        proyectos=proyectos,
        proyecto_seleccionado=proyecto_seleccionado
    )

# ------------------------
# GUARDAR CONTRATO
# ------------------------
@contratos_bp.route('/guardar_contrato', methods=['POST'])
@login_required
@solo_admin
def guardar_contrato():

    import uuid

    id_proyecto = request.form['id_proyecto']
    no_contrato = request.form['no_contrato']
    fecha = request.form['fecha']
    contratista = request.form['contratista']
    monto = request.form['monto']

    conexion = conectar_db()
    cursor = conexion.cursor()

    archivo_pdf = request.files.get('archivo_contrato')

    nombre_archivo = None

    # ------------------------
    # SUBIR PDF
    # ------------------------
    if archivo_pdf and archivo_pdf.filename != '':

        if archivo_pdf.filename.lower().endswith('.pdf'):

            # EVITAR NOMBRES DUPLICADOS
            extension = archivo_pdf.filename.rsplit('.', 1)[1].lower()

            nombre_archivo = (
                f"{uuid.uuid4().hex}.{extension}"
            )

            nombre_archivo = secure_filename(nombre_archivo)

            ruta_guardado = os.path.join(
                'static/uploads/contratos',
                nombre_archivo
            )

            archivo_pdf.save(ruta_guardado)

            registrar_auditoria(
                current_user.nombre,
                f'Subió PDF de contrato: {nombre_archivo}',
                'contratos',
                request.remote_addr
            )

    # ------------------------
    # INSERTAR CONTRATO
    # ------------------------
    sql = """
        INSERT INTO contratos (
            id_proyecto,
            no_contrato,
            fecha_contrato,
            contratista,
            monto_contratado,
            archivo_contrato
        )
        VALUES (%s, %s, %s, %s, %s, %s)
    """

    try:

        cursor.execute(
            sql,
            (
                id_proyecto,
                no_contrato,
                fecha,
                contratista,
                monto,
                nombre_archivo
            )
        )

        registrar_auditoria(
            current_user.nombre,
            f'Registró contrato: {no_contrato}',
            'contratos',
            request.remote_addr
        )

        conexion.commit()

    except Exception as e:

        conexion.rollback()

        print(e)

        return "⚠️ Este proyecto ya tiene un contrato asignado"

    finally:

        conexion.close()

    return redirect('/')

#-----------------------------
# VER CONTRATO
#-----------------------------

@contratos_bp.route('/ver_contrato/<int:id_contrato>')
@login_required
def ver_contrato(id_contrato):

    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            archivo_contrato,
            no_contrato
        FROM contratos
        WHERE id_contrato = %s
    """, (id_contrato,))

    contrato = cursor.fetchone()

    if not contrato:

        conexion.close()

        flash('Contrato no encontrado.', 'danger')

        return redirect(url_for('proyectos.inicio'))

    conexion.close()

    if not contrato or not contrato[0]:

        flash('Contrato PDF no encontrado.', 'danger')

        return redirect(url_for('proyectos.inicio'))

    return send_from_directory(
        'static/uploads/contratos',
        contrato[0]
    )
    
#-----------------------------
# ELIMINAR CONTRATO
#-----------------------------
@contratos_bp.route('/eliminar_contrato/<int:id_contrato>', methods=['POST'])
@login_required
@solo_admin
def eliminar_contrato(id_contrato):

    conexion = conectar_db()
    cursor = conexion.cursor(dictionary=True)

    # OBTENER PDF
    cursor.execute("""
        SELECT
            archivo_contrato,
            no_contrato
        FROM contratos
        WHERE id_contrato = %s
    """, (id_contrato,))

    contrato = cursor.fetchone()

    if not contrato:

        conexion.close()

        flash('Contrato no encontrado.', 'danger')

        return redirect(url_for('proyectos.inicio'))

    registrar_auditoria(
        current_user.nombre,
        f'Eliminó contrato: {contrato["no_contrato"]}',
        'contratos',
        request.remote_addr
    )

    if contrato['archivo_contrato']:

        ruta_pdf = os.path.join(
            'static/uploads/contratos',
            contrato['archivo_contrato']
        )

        if os.path.exists(ruta_pdf):

            os.remove(ruta_pdf)

    # ELIMINAR CONTRATO
    # CASCADE elimina:
    # visitas
    # avances
    # convenios
    # observaciones

    cursor.execute("""
        DELETE FROM contratos
        WHERE id_contrato = %s
    """, (id_contrato,))

    conexion.commit()

    conexion.close()

    flash(
        'Contrato y registros relacionados eliminados.',
        'success'
    )

    return redirect(url_for('proyectos.inicio'))
