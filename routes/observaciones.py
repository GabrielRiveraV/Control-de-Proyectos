from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from database import conectar_db
from utils.auditoria import registrar_auditoria


observaciones_bp = Blueprint(
    'observaciones',
    __name__,
    url_prefix='/observaciones'
)


TIPOS = ['Fisica', 'Documental', 'Financiera', 'Administrativa', 'Otra']
PRIORIDADES = ['Baja', 'Media', 'Alta', 'Critica']
ESTATUS = ['Abierta', 'En seguimiento', 'Atendida', 'Solventada', 'Cerrada']


def puede_gestionar():
    return current_user.rol in ('admin', 'jefe')


def puede_crear():
    return current_user.rol in ('admin', 'jefe', 'supervisor')


@observaciones_bp.route('/')
@login_required
def index():

    conexion = conectar_db()
    cursor = conexion.cursor(dictionary=True)

    estatus = request.args.get('estatus') or ''
    prioridad = request.args.get('prioridad') or ''
    busqueda = request.args.get('busqueda') or ''

    filtros = []
    valores = []

    if estatus:
        filtros.append('o.estatus = %s')
        valores.append(estatus)

    if prioridad:
        filtros.append('o.prioridad = %s')
        valores.append(prioridad)

    if busqueda:
        filtros.append('(p.nombre LIKE %s OR o.titulo LIKE %s OR o.descripcion LIKE %s)')
        valores.extend([f'%{busqueda}%', f'%{busqueda}%', f'%{busqueda}%'])

    where = f"WHERE {' AND '.join(filtros)}" if filtros else ''

    cursor.execute(f"""
        SELECT
            o.id_observacion,
            o.titulo,
            o.tipo,
            o.prioridad,
            o.estatus,
            o.responsable,
            o.fecha_compromiso,
            o.fecha_cierre,
            o.created_at,
            p.nombre AS proyecto,
            c.no_contrato,
            v.fecha_visita,
            u.nombre AS creador
        FROM observaciones o
        INNER JOIN proyectos p
            ON o.id_proyecto = p.id_proyecto
        LEFT JOIN contratos c
            ON o.id_contrato = c.id_contrato
        LEFT JOIN visitas v
            ON o.id_visita = v.id_visita
        LEFT JOIN usuarios u
            ON o.id_usuario_creador = u.id_usuario
        {where}
        ORDER BY
            CASE o.prioridad
                WHEN 'Critica' THEN 1
                WHEN 'Alta' THEN 2
                WHEN 'Media' THEN 3
                ELSE 4
            END,
            o.created_at DESC
        LIMIT 300
    """, valores)

    observaciones = cursor.fetchall()

    cursor.execute("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN estatus IN ('Abierta', 'En seguimiento') THEN 1 ELSE 0 END) AS abiertas,
            SUM(CASE WHEN prioridad IN ('Alta', 'Critica') AND estatus <> 'Cerrada' THEN 1 ELSE 0 END) AS alto_riesgo,
            SUM(CASE WHEN fecha_compromiso < CURDATE() AND estatus NOT IN ('Cerrada', 'Solventada') THEN 1 ELSE 0 END) AS vencidas
        FROM observaciones
    """)
    resumen = cursor.fetchone()

    conexion.close()

    return render_template(
        'observaciones.html',
        observaciones=observaciones,
        resumen=resumen,
        tipos=TIPOS,
        prioridades=PRIORIDADES,
        estatus_opciones=ESTATUS,
        filtros={
            'estatus': estatus,
            'prioridad': prioridad,
            'busqueda': busqueda
        }
    )


@observaciones_bp.route('/nueva')
@login_required
def nueva():

    if not puede_crear():
        flash('No tienes permiso para crear observaciones.', 'danger')
        return redirect(url_for('observaciones.index'))

    id_visita = request.args.get('id_visita', type=int)
    id_contrato = request.args.get('id_contrato', type=int)
    id_proyecto = request.args.get('id_proyecto', type=int)

    conexion = conectar_db()
    cursor = conexion.cursor(dictionary=True)

    contexto = None

    if id_visita:
        cursor.execute("""
            SELECT
                v.id_visita,
                v.fecha_visita,
                v.observaciones AS observaciones_visita,
                c.id_contrato,
                c.no_contrato,
                p.id_proyecto,
                p.nombre AS proyecto
            FROM visitas v
            INNER JOIN contratos c
                ON v.id_contrato = c.id_contrato
            INNER JOIN proyectos p
                ON c.id_proyecto = p.id_proyecto
            WHERE v.id_visita = %s
        """, (id_visita,))
        contexto = cursor.fetchone()

    elif id_contrato:
        cursor.execute("""
            SELECT
                c.id_contrato,
                c.no_contrato,
                p.id_proyecto,
                p.nombre AS proyecto
            FROM contratos c
            INNER JOIN proyectos p
                ON c.id_proyecto = p.id_proyecto
            WHERE c.id_contrato = %s
        """, (id_contrato,))
        contexto = cursor.fetchone()

    elif id_proyecto:
        cursor.execute("""
            SELECT
                p.id_proyecto,
                p.nombre AS proyecto,
                c.id_contrato,
                c.no_contrato
            FROM proyectos p
            LEFT JOIN contratos c
                ON p.id_proyecto = c.id_proyecto
            WHERE p.id_proyecto = %s
        """, (id_proyecto,))
        contexto = cursor.fetchone()

    cursor.execute("""
        SELECT
            p.id_proyecto,
            p.nombre,
            c.id_contrato,
            c.no_contrato
        FROM proyectos p
        LEFT JOIN contratos c
            ON p.id_proyecto = c.id_proyecto
        ORDER BY p.nombre
    """)
    proyectos = cursor.fetchall()

    conexion.close()

    return render_template(
        'observacion_form.html',
        contexto=contexto,
        proyectos=proyectos,
        tipos=TIPOS,
        prioridades=PRIORIDADES,
        estatus_opciones=ESTATUS
    )


@observaciones_bp.route('/guardar', methods=['POST'])
@login_required
def guardar():

    if not puede_crear():
        flash('No tienes permiso para crear observaciones.', 'danger')
        return redirect(url_for('observaciones.index'))

    id_proyecto = request.form.get('id_proyecto', type=int)
    id_contrato = request.form.get('id_contrato', type=int)
    id_visita = request.form.get('id_visita', type=int)
    titulo = request.form.get('titulo')
    descripcion = request.form.get('descripcion')
    tipo = request.form.get('tipo') or 'Fisica'
    prioridad = request.form.get('prioridad') or 'Media'
    responsable = request.form.get('responsable') or None
    fecha_compromiso = request.form.get('fecha_compromiso') or None

    if not id_proyecto or not titulo or not descripcion:
        flash('Proyecto, titulo y descripcion son obligatorios.', 'danger')
        return redirect(request.referrer or url_for('observaciones.nueva'))

    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("""
        INSERT INTO observaciones (
            id_proyecto,
            id_contrato,
            id_visita,
            id_usuario_creador,
            titulo,
            descripcion,
            tipo,
            prioridad,
            estatus,
            responsable,
            fecha_compromiso
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'Abierta', %s, %s)
    """, (
        id_proyecto,
        id_contrato,
        id_visita,
        current_user.id,
        titulo,
        descripcion,
        tipo,
        prioridad,
        responsable,
        fecha_compromiso
    ))

    registrar_auditoria(
        current_user.nombre,
        f'Creo observacion formal: {titulo}',
        'observaciones',
        request.remote_addr
    )

    conexion.commit()
    conexion.close()

    flash('Observacion registrada correctamente.', 'success')
    return redirect(url_for('observaciones.index'))


@observaciones_bp.route('/<int:id_observacion>', methods=['GET', 'POST'])
@login_required
def detalle(id_observacion):

    conexion = conectar_db()
    cursor = conexion.cursor(dictionary=True)

    if request.method == 'POST':

        if not puede_gestionar():
            conexion.close()
            flash('Solo admin o jefe pueden actualizar el seguimiento.', 'danger')
            return redirect(url_for('observaciones.detalle', id_observacion=id_observacion))

        estatus = request.form.get('estatus') or 'Abierta'
        prioridad = request.form.get('prioridad') or 'Media'
        responsable = request.form.get('responsable') or None
        fecha_compromiso = request.form.get('fecha_compromiso') or None
        fecha_cierre = request.form.get('fecha_cierre') or None

        cursor.execute("""
            UPDATE observaciones
            SET
                estatus = %s,
                prioridad = %s,
                responsable = %s,
                fecha_compromiso = %s,
                fecha_cierre = %s
            WHERE id_observacion = %s
        """, (
            estatus,
            prioridad,
            responsable,
            fecha_compromiso,
            fecha_cierre,
            id_observacion
        ))

        registrar_auditoria(
            current_user.nombre,
            f'Actualizo observacion ID {id_observacion}',
            'observaciones',
            request.remote_addr
        )

        conexion.commit()
        flash('Observacion actualizada correctamente.', 'success')

    cursor.execute("""
        SELECT
            o.*,
            p.nombre AS proyecto,
            p.localidad,
            c.no_contrato,
            c.contratista,
            v.fecha_visita,
            u.nombre AS creador
        FROM observaciones o
        INNER JOIN proyectos p
            ON o.id_proyecto = p.id_proyecto
        LEFT JOIN contratos c
            ON o.id_contrato = c.id_contrato
        LEFT JOIN visitas v
            ON o.id_visita = v.id_visita
        LEFT JOIN usuarios u
            ON o.id_usuario_creador = u.id_usuario
        WHERE o.id_observacion = %s
    """, (id_observacion,))

    observacion = cursor.fetchone()
    conexion.close()

    if not observacion:
        flash('Observacion no encontrada.', 'danger')
        return redirect(url_for('observaciones.index'))

    return render_template(
        'observacion_detalle.html',
        observacion=observacion,
        prioridades=PRIORIDADES,
        estatus_opciones=ESTATUS,
        puede_gestionar=puede_gestionar()
    )
