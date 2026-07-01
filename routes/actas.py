import os
import uuid
from decimal import Decimal, InvalidOperation

from flask import Blueprint, current_app, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from mysql.connector import Error as MySQLError
from werkzeug.utils import secure_filename

from database import conectar_db
from routes.permisos import solo_supervisor
from utils.auditoria import registrar_auditoria


actas_bp = Blueprint('actas', __name__, url_prefix='/actas')
EXTENSIONES_IMAGEN = {'jpg', 'jpeg', 'png', 'webp'}
UPLOAD_EVIDENCIAS = 'uploads/actas/evidencias'


def decimal_o_none(valor):
    if valor is None or valor == '':
        return None
    try:
        return Decimal(valor)
    except (InvalidOperation, TypeError):
        return None


def falta_tabla_actas(error):
    return getattr(error, 'errno', None) == 1146


def imagen_permitida(nombre_archivo):
    return (
        '.' in nombre_archivo
        and nombre_archivo.rsplit('.', 1)[1].lower() in EXTENSIONES_IMAGEN
    )


def guardar_imagen_acta(archivo):
    if not archivo or archivo.filename == '':
        return None
    if not imagen_permitida(archivo.filename):
        return None
    extension = archivo.filename.rsplit('.', 1)[1].lower()
    nombre_archivo = secure_filename(f"{uuid.uuid4().hex}.{extension}")
    carpeta = os.path.join(current_app.static_folder, UPLOAD_EVIDENCIAS)
    os.makedirs(carpeta, exist_ok=True)
    archivo.save(os.path.join(carpeta, nombre_archivo))
    return {
        'nombre_original': archivo.filename,
        'ruta_archivo': f"{UPLOAD_EVIDENCIAS}/{nombre_archivo}"
    }


def calcular_estimacion(cantidad_estimada, cantidad_verificada, precio_unitario):
    estimada = cantidad_estimada or Decimal('0')
    verificada = cantidad_verificada or Decimal('0')
    precio = precio_unitario or Decimal('0')
    diferencia = estimada - verificada
    importe = diferencia * precio
    return diferencia, importe


def obtener_contexto_visita(cursor, id_visita):
    cursor.execute("""
        SELECT
            v.id_visita,
            v.fecha_visita,
            v.supervisor,
            v.residente_obra AS residente_visita,
            v.observaciones AS observaciones_visita,
            c.id_contrato,
            c.no_contrato,
            c.fecha_contrato,
            c.contratista,
            c.monto_contratado,
            c.anticipo,
            c.periodo_ejecucion,
            c.plazo_ejecucion,
            c.residente_obra AS residente_contrato,
            p.id_proyecto,
            p.nombre AS proyecto,
            p.programa,
            p.un_ad,
            p.localidad,
            p.inversion_autorizada,
            p.ejercicio_fiscal
        FROM visitas v
        INNER JOIN contratos c ON v.id_contrato = c.id_contrato
        INNER JOIN proyectos p ON c.id_proyecto = p.id_proyecto
        WHERE v.id_visita = %s
    """, (id_visita,))

    return cursor.fetchone()


def obtener_o_crear_acta(cursor, conexion, visita):
    cursor.execute("""
        SELECT *
        FROM actas_visita
        WHERE id_visita = %s
    """, (visita['id_visita'],))

    acta = cursor.fetchone()

    if acta:
        return acta

    cursor.execute("""
        INSERT INTO actas_visita (
            id_visita,
            id_usuario,
            fecha_acta,
            situacion_obra,
            observacion_fisica,
            elaborado_por,
            cargo_elabora,
            cargo_vo_bo
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        visita['id_visita'],
        current_user.id,
        visita['fecha_visita'],
        'En proceso',
        visita['observaciones_visita'],
        current_user.nombre,
        'Fiscalizacion de Obra',
        'Jefe de Fiscalizacion'
    ))

    conexion.commit()

    cursor.execute("""
        SELECT *
        FROM actas_visita
        WHERE id_visita = %s
    """, (visita['id_visita'],))

    return cursor.fetchone()


def obtener_detalles(cursor, id_acta):
    cursor.execute("""
        SELECT *
        FROM acta_conceptos
        WHERE id_acta = %s
        ORDER BY orden, id_concepto
    """, (id_acta,))
    conceptos = cursor.fetchall()

    cursor.execute("""
        SELECT *
        FROM acta_estimaciones
        WHERE id_acta = %s
        ORDER BY orden, id_estimacion
    """, (id_acta,))
    estimaciones = cursor.fetchall()

    cursor.execute("""
        SELECT *
        FROM acta_tramos
        WHERE id_acta = %s
        ORDER BY orden, id_tramo
    """, (id_acta,))
    tramos = cursor.fetchall()

    cursor.execute("""
        SELECT *
        FROM acta_hallazgos
        WHERE id_acta = %s
        ORDER BY orden, id_hallazgo
    """, (id_acta,))
    hallazgos = cursor.fetchall()

    cursor.execute("""
        SELECT *
        FROM acta_evidencias
        WHERE id_acta = %s
        ORDER BY tipo, orden, id_evidencia
    """, (id_acta,))
    evidencias = cursor.fetchall()

    fotos = [e for e in evidencias if e['tipo'] == 'foto']
    croquis = [e for e in evidencias if e['tipo'] == 'croquis']

    return conceptos, estimaciones, tramos, hallazgos, fotos, croquis


@actas_bp.route('/expediente/<int:id_visita>', methods=['GET', 'POST'])
@login_required
@solo_supervisor
def expediente_acta(id_visita):
    conexion = conectar_db()
    cursor = conexion.cursor(dictionary=True)

    visita = obtener_contexto_visita(cursor, id_visita)

    if not visita:
        conexion.close()
        flash('Visita no encontrada.', 'danger')
        return redirect(url_for('ver_visitas'))

    try:
        acta = obtener_o_crear_acta(cursor, conexion, visita)
    except MySQLError as error:
        conexion.close()
        if falta_tabla_actas(error):
            flash('El módulo de actas aún no tiene sus tablas en MySQL. Aplica la migración 001_generacion_actas.sql.', 'danger')
            return redirect(url_for('ver_visitas'))
        raise

    if request.method == 'POST':
        accion = request.form.get('accion', 'guardar')
        estado = 'finalizada' if accion == 'finalizar' else 'borrador'

        cursor.execute("""
            UPDATE actas_visita
            SET
                fecha_acta = %s,
                estado = %s,
                avance_programado = %s,
                avance_fisico = %s,
                situacion_obra = %s,
                observacion_fisica = %s,
                notas = %s,
                elaborado_por = %s,
                vo_bo = %s,
                cargo_elabora = %s,
                cargo_vo_bo = %s
            WHERE id_acta = %s
        """, (
            request.form.get('fecha_acta') or None,
            estado,
            decimal_o_none(request.form.get('avance_programado')),
            decimal_o_none(request.form.get('avance_fisico')),
            request.form.get('situacion_obra') or None,
            request.form.get('observacion_fisica') or None,
            request.form.get('notas') or None,
            request.form.get('elaborado_por') or None,
            request.form.get('vo_bo') or None,
            request.form.get('cargo_elabora') or None,
            request.form.get('cargo_vo_bo') or None,
            acta['id_acta']
        ))

        for tabla in ('acta_conceptos', 'acta_estimaciones', 'acta_tramos', 'acta_hallazgos'):
            cursor.execute(f"DELETE FROM {tabla} WHERE id_acta = %s", (acta['id_acta'],))

        conceptos = request.form.getlist('concepto[]')
        for idx, concepto in enumerate(conceptos, start=1):
            if not concepto.strip():
                continue
            cursor.execute("""
                INSERT INTO acta_conceptos (
                    id_acta, clave, concepto, unidad, importe, porcentaje_verificado, orden
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                acta['id_acta'],
                request.form.getlist('concepto_clave[]')[idx - 1],
                concepto,
                request.form.getlist('concepto_unidad[]')[idx - 1],
                decimal_o_none(request.form.getlist('concepto_importe[]')[idx - 1]),
                decimal_o_none(request.form.getlist('concepto_porcentaje[]')[idx - 1]),
                idx
            ))

        estimaciones = request.form.getlist('estimacion_concepto[]')
        for idx, concepto in enumerate(estimaciones, start=1):
            if not concepto.strip():
                continue
            cantidad_estimada = decimal_o_none(request.form.getlist('cantidad_estimada[]')[idx - 1])
            cantidad_verificada = decimal_o_none(request.form.getlist('cantidad_verificada[]')[idx - 1])
            precio_unitario = decimal_o_none(request.form.getlist('precio_unitario[]')[idx - 1])
            diferencia, importe = calcular_estimacion(
                cantidad_estimada,
                cantidad_verificada,
                precio_unitario
            )
            cursor.execute("""
                INSERT INTO acta_estimaciones (
                    id_acta, clave, concepto, unidad, cantidad_estimada,
                    cantidad_verificada, precio_unitario, diferencia, importe, orden
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                acta['id_acta'],
                request.form.getlist('estimacion_clave[]')[idx - 1],
                concepto,
                request.form.getlist('estimacion_unidad[]')[idx - 1],
                cantidad_estimada,
                cantidad_verificada,
                precio_unitario,
                diferencia,
                importe,
                idx
            ))

        ubicaciones = request.form.getlist('tramo_ubicacion[]')
        for idx, ubicacion in enumerate(ubicaciones, start=1):
            if not ubicacion.strip():
                continue
            cursor.execute("""
                INSERT INTO acta_tramos (
                    id_acta, ubicacion, tramo, volumen, unidad, orden
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                acta['id_acta'],
                ubicacion,
                request.form.getlist('tramo_descripcion[]')[idx - 1],
                decimal_o_none(request.form.getlist('tramo_volumen[]')[idx - 1]),
                request.form.getlist('tramo_unidad[]')[idx - 1],
                idx
            ))

        hallazgos = request.form.getlist('hallazgo[]')
        for idx, hallazgo in enumerate(hallazgos, start=1):
            if not hallazgo.strip():
                continue
            cursor.execute("""
                INSERT INTO acta_hallazgos (id_acta, descripcion, orden)
                VALUES (%s, %s, %s)
            """, (acta['id_acta'], hallazgo, idx))


        croquis_archivo = request.files.get('croquis_archivo')
        croquis_guardado = guardar_imagen_acta(croquis_archivo)
        if croquis_guardado:
            cursor.execute("DELETE FROM acta_evidencias WHERE id_acta = %s AND tipo = 'croquis'", (acta['id_acta'],))
            cursor.execute("""
                INSERT INTO acta_evidencias (
                    id_acta, tipo, titulo, descripcion, nombre_original, ruta_archivo, orden
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                acta['id_acta'],
                'croquis',
                request.form.get('croquis_titulo') or 'Croquis de ubicacion',
                request.form.get('croquis_descripcion') or None,
                croquis_guardado['nombre_original'],
                croquis_guardado['ruta_archivo'],
                1
            ))

        archivos_foto = request.files.getlist('evidencia_archivo[]')
        titulos_foto = request.form.getlist('evidencia_titulo[]')
        descripciones_foto = request.form.getlist('evidencia_descripcion[]')
        for idx, archivo in enumerate(archivos_foto, start=1):
            foto_guardada = guardar_imagen_acta(archivo)
            if not foto_guardada:
                continue
            cursor.execute("""
                INSERT INTO acta_evidencias (
                    id_acta, tipo, titulo, descripcion, nombre_original, ruta_archivo, orden
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                acta['id_acta'],
                'foto',
                titulos_foto[idx - 1] if idx - 1 < len(titulos_foto) else None,
                descripciones_foto[idx - 1] if idx - 1 < len(descripciones_foto) else None,
                foto_guardada['nombre_original'],
                foto_guardada['ruta_archivo'],
                idx
            ))

        registrar_auditoria(
            current_user.nombre,
            f'Actualizo expediente de acta de visita ID {id_visita}',
            'actas',
            request.remote_addr
        )

        conexion.commit()
        conexion.close()

        flash('Expediente del acta guardado correctamente.', 'success')
        return redirect(url_for('actas.expediente_acta', id_visita=id_visita))

    conceptos, estimaciones, tramos, hallazgos, fotos, croquis = obtener_detalles(cursor, acta['id_acta'])
    conexion.close()

    return render_template(
        'expediente_acta.html',
        visita=visita,
        acta=acta,
        conceptos=conceptos,
        estimaciones=estimaciones,
        tramos=tramos,
        hallazgos=hallazgos,
        fotos=fotos,
        croquis=croquis
    )


@actas_bp.route('/imprimir/<int:id_visita>')
@login_required
@solo_supervisor
def imprimir_acta(id_visita):
    conexion = conectar_db()
    cursor = conexion.cursor(dictionary=True)

    visita = obtener_contexto_visita(cursor, id_visita)

    if not visita:
        conexion.close()
        flash('Visita no encontrada.', 'danger')
        return redirect(url_for('ver_visitas'))

    try:
        acta = obtener_o_crear_acta(cursor, conexion, visita)
        conceptos, estimaciones, tramos, hallazgos, fotos, croquis = obtener_detalles(cursor, acta['id_acta'])
    except MySQLError as error:
        conexion.close()
        if falta_tabla_actas(error):
            flash('El módulo de actas aún no tiene sus tablas en MySQL. Aplica la migración 001_generacion_actas.sql.', 'danger')
            return redirect(url_for('ver_visitas'))
        raise

    conexion.close()

    return render_template(
        'acta_imprimir.html',
        visita=visita,
        acta=acta,
        conceptos=conceptos,
        estimaciones=estimaciones,
        tramos=tramos,
        hallazgos=hallazgos,
        fotos=fotos,
        croquis=croquis
    )
