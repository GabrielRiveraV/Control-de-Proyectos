import os
from flask import (
    Blueprint,
    current_app,
    render_template,
    request,
    redirect,
    url_for,
    flash
)
from werkzeug.utils import secure_filename
from utils.auditoria import registrar_auditoria
from flask_login import login_required, current_user
from routes.auth import solo_admin
from database import conectar_db

visitas_bp = Blueprint(
    'visitas',
    __name__
)


def archivo_permitido(nombre_archivo):

    return (
        '.' in nombre_archivo and
        nombre_archivo.rsplit('.', 1)[1].lower()
        in current_app.config['ALLOWED_EXTENSIONS']
    )


def guardar_archivo_acta(archivo):

    import uuid

    if not archivo or archivo.filename == '':
        return None

    if not archivo_permitido(archivo.filename):
        return None

    extension = archivo.filename.rsplit('.', 1)[1].lower()
    nombre_archivo = secure_filename(f"acta_{uuid.uuid4().hex}.{extension}")

    os.makedirs(
        current_app.config['UPLOAD_FOLDER_ACTAS'],
        exist_ok=True
    )

    archivo.save(
        os.path.join(
            current_app.config['UPLOAD_FOLDER_ACTAS'],
            nombre_archivo
        )
    )

    return nombre_archivo

# ------------------------
# NUEVA VISITA
# ------------------------
@visitas_bp.route('/nueva_visita/<int:id_proyecto>')
@login_required
def nueva_visita(id_proyecto):

    conexion = conectar_db()
    cursor = conexion.cursor()

    # CONSULTA CONTRATO DEL PROYECTO
    cursor.execute("""
        SELECT
            c.id_contrato,
            c.no_contrato
        FROM contratos c
        INNER JOIN proyectos p
            ON c.id_proyecto = p.id_proyecto
        WHERE p.id_proyecto = %s
    """, (id_proyecto,))

    contrato = cursor.fetchone()

    print("ID PROYECTO:", id_proyecto)
    print("CONTRATO:", contrato)

    conexion.close()

    # VALIDACIÓN
    if not contrato:
        return f"""
        ⚠️ No se encontró contrato
        para el proyecto ID {id_proyecto}
        """

    return render_template(
        'nueva_visita.html',
        contrato=contrato
    )
    
# ------------------------
# GUARDAR VISITA
# ------------------------
@visitas_bp.route('/guardar_visita', methods=['POST'])
@login_required
def guardar_visita():

    import uuid

    # FORMULARIO
    id_contrato = request.form.get('id_contrato')
    fecha = request.form.get('fecha')
    supervisor = request.form.get('supervisor')
    residente = request.form.get('residente')
    observaciones = request.form.get('observaciones')

    # ARCHIVO
    archivo = request.files.get('archivo_acta')

    nombre_archivo = None

    # VALIDACIÓN CONTRATO
    if not id_contrato:

        flash(
            'No se recibió el contrato.',
            'danger'
        )

        return redirect('/')

    # ------------------------
    # SUBIR PDF (OPCIONAL)
    # ------------------------
    if archivo and archivo.filename != '':

        if archivo_permitido(archivo.filename):

            nombre_archivo = guardar_archivo_acta(archivo)

        else:

            flash(
                'Archivo no permitido. Solo PDF, XLSX o XLS.',
                'danger'
            )

            return redirect('/')

    # ------------------------
    # GUARDAR EN BASE DE DATOS
    # ------------------------
    conexion = conectar_db()
    cursor = conexion.cursor()

    sql = """
        INSERT INTO visitas (
            id_contrato,
            fecha_visita,
            supervisor,
            residente_obra,
            observaciones,
            id_usuario,
            archivo_acta
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    valores = (
        id_contrato,
        fecha,
        supervisor,
        residente,
        observaciones,
        current_user.id,
        nombre_archivo
    )

    cursor.execute(sql, valores)
    
    registrar_auditoria(
        current_user.nombre,
        f'Registró visita al contrato ID {id_contrato}',
        'visitas',
        request.remote_addr
    )

    conexion.commit()
    conexion.close()

    flash(
        'Visita registrada correctamente.',
        'success'
    )

    return redirect('/')


# ------------------------
# SUBIR / REEMPLAZAR ACTA FIRMADA
# ------------------------
@visitas_bp.route('/subir_acta/<int:id_visita>', methods=['POST'])
@login_required
def subir_acta(id_visita):

    if current_user.rol != 'supervisor':
        flash('Solo los supervisores pueden subir actas firmadas.', 'danger')
        return redirect(request.referrer or '/')

    archivo = request.files.get('archivo_acta')

    if not archivo or archivo.filename == '':
        flash('Selecciona un archivo de acta.', 'danger')
        return redirect(request.referrer or '/')

    nombre_archivo = guardar_archivo_acta(archivo)

    if not nombre_archivo:
        flash('Archivo no permitido. Solo PDF, XLSX o XLS.', 'danger')
        return redirect(request.referrer or '/')

    conexion = conectar_db()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        SELECT archivo_acta
        FROM visitas
        WHERE id_visita = %s
    """, (id_visita,))

    visita = cursor.fetchone()

    if not visita:
        conexion.close()
        flash('La visita no existe.', 'danger')
        return redirect(request.referrer or '/')

    if visita['archivo_acta']:
        ruta_anterior = visita['archivo_acta']
        if not os.path.dirname(ruta_anterior):
            ruta_anterior = os.path.join(
                current_app.config['UPLOAD_FOLDER_ACTAS'],
                ruta_anterior
            )
        ruta_anterior = os.path.normpath(ruta_anterior)
        if os.path.exists(ruta_anterior):
            os.remove(ruta_anterior)

    cursor.execute("""
        UPDATE visitas
        SET archivo_acta = %s
        WHERE id_visita = %s
    """, (nombre_archivo, id_visita))

    registrar_auditoria(
        current_user.nombre,
        f'Subio acta firmada de visita ID {id_visita}',
        'visitas',
        request.remote_addr
    )

    conexion.commit()
    conexion.close()

    flash('Acta firmada subida correctamente.', 'success')
    return redirect(request.referrer or '/')

# ------------------------
# ELIMINAR VISITA
# ------------------------
@visitas_bp.route('/eliminar_visita/<int:id_visita>', methods=['POST'])
@login_required
@solo_admin
def eliminar_visita(id_visita):

    conexion = conectar_db()

    cursor = conexion.cursor(dictionary=True)

    # ------------------------
    # OBTENER VISITA
    # ------------------------
    cursor.execute("""
        SELECT archivo_acta
        FROM visitas
        WHERE id_visita = %s
    """, (id_visita,))

    visita = cursor.fetchone()

    # ------------------------
    # VALIDAR EXISTENCIA
    # ------------------------
    if not visita:

        conexion.close()

        flash('La visita no existe')

        return redirect('/')

    # ------------------------
    # ELIMINAR PDF
    # ------------------------
    if visita['archivo_acta']:

        ruta_archivo = visita['archivo_acta']

        if not os.path.dirname(ruta_archivo):

            ruta_archivo = os.path.join(
                current_app.config['UPLOAD_FOLDER_ACTAS'],
                ruta_archivo
            )

        ruta_archivo = os.path.normpath(ruta_archivo)

        if os.path.exists(ruta_archivo):

            os.remove(ruta_archivo)

    # ------------------------
    # ELIMINAR VISITA
    # ------------------------
    cursor.execute("""
        DELETE FROM visitas
        WHERE id_visita = %s
    """, (id_visita,))

    # ------------------------
    # AUDITORÍA
    # ------------------------
    registrar_auditoria(
        current_user.nombre,
        f'Eliminó visita ID {id_visita}',
        'visitas',
        request.remote_addr
    )

    conexion.commit()

    conexion.close()

    flash('Visita eliminada correctamente')

    return redirect(request.referrer)
