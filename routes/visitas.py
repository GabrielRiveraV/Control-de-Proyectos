import os
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)
from utils.auditoria import registrar_auditoria
from flask_login import login_required, current_user
from routes.auth import solo_admin
from database import conectar_db

visitas_bp = Blueprint(
    'visitas',
    __name__
)

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

            extension = archivo.filename.rsplit('.', 1)[1].lower()

            nombre_archivo = (
                f"acta_{uuid.uuid4().hex}.{extension}"
            )

            ruta_guardado = os.path.join(
                current_app.config['UPLOAD_FOLDER_ACTAS'],
                nombre_archivo
            )

            archivo.save(ruta_guardado)

        else:

            flash(
                'Archivo no permitido. Solo PDF.',
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
# ELIMINAR VISITA
# ------------------------
@visitas_bp.route('/eliminar_visita/<int:id_visita>')
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

        ruta_archivo = os.path.normpath(
            visita['archivo_acta']
        )

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