from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for
    )
from utils.auditoria import registrar_auditoria
from flask_login import (
    login_required,
    current_user)

from database import conectar_db
from routes.auth import solo_admin

proyectos_bp = Blueprint(
    'proyectos',
    __name__
)

# ------------------------
# RUTA PRINCIPAL
# ------------------------
@proyectos_bp.route('/')
@login_required
def inicio():

    conexion = conectar_db()
    cursor = conexion.cursor(dictionary=True)

    busqueda = request.args.get('busqueda')
    pagina = request.args.get('pagina', 1, type=int)

    por_pagina = 15

    offset = (pagina - 1) * por_pagina

    if busqueda:

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM proyectos
            WHERE nombre LIKE %s
            OR programa LIKE %s
        """,
        (
            f"%{busqueda}%",
            f"%{busqueda}%"
        ))

    else:

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM proyectos
        """)
    
    total_registros = cursor.fetchone()['total']

    if busqueda:

        query = """
        SELECT 
            p.id_proyecto, 
            p.nombre, 
            p.programa, 
            p.un_ad, 
            p.localidad, 
            p.inversion_autorizada,
            p.ejercicio_fiscal,
            p.estatus_proyecto,

            c.no_contrato,
            c.estatus_contrato,

            COUNT(v.id_visita) as total_visitas,

            CASE
                WHEN c.id_contrato IS NOT NULL THEN 1
                ELSE 0
            END as tiene_contrato,

            c.archivo_contrato,
            c.id_contrato

        FROM proyectos p

        LEFT JOIN contratos c 
            ON p.id_proyecto = c.id_proyecto

        LEFT JOIN visitas v 
            ON c.id_contrato = v.id_contrato

        WHERE p.nombre LIKE %s 
        OR p.programa LIKE %s

        GROUP BY 
            p.id_proyecto,
            p.nombre,
            p.programa,
            p.un_ad,
            p.localidad,
            p.inversion_autorizada,
            p.ejercicio_fiscal,
            p.estatus_proyecto,
            c.no_contrato,
            c.estatus_contrato,
            c.id_contrato,
            c.archivo_contrato
            

        ORDER BY p.ejercicio_fiscal DESC,
                p.id_proyecto DESC

        LIMIT %s, %s
        """

        cursor.execute(
            query,
            (
                f"%{busqueda}%",
                f"%{busqueda}%",
            offset,
            por_pagina
            )
        )

    else:

        cursor.execute("""
            SELECT
                p.id_proyecto,
                p.nombre,
                p.programa,
                p.un_ad,
                p.localidad,
                p.inversion_autorizada,
                p.ejercicio_fiscal,
                p.estatus_proyecto,

                c.no_contrato,
                c.estatus_contrato,

                COUNT(v.id_visita) as total_visitas,

                CASE
                    WHEN c.id_contrato IS NOT NULL THEN 1
                    ELSE 0
                END as tiene_contrato,

                c.archivo_contrato,
                c.id_contrato

            FROM proyectos p

            LEFT JOIN contratos c
                ON p.id_proyecto = c.id_proyecto

            LEFT JOIN visitas v
                ON c.id_contrato = v.id_contrato

            GROUP BY
                p.id_proyecto,
                p.nombre,
                p.programa,
                p.un_ad,
                p.localidad,
                p.inversion_autorizada,
                p.ejercicio_fiscal,
                p.estatus_proyecto,
                c.no_contrato,
                c.estatus_contrato,
                c.id_contrato,
                c.archivo_contrato

            ORDER BY p.ejercicio_fiscal DESC,
                    p.id_proyecto DESC

            LIMIT %s, %s
        """, (
    offset,
    por_pagina
))

    proyectos = cursor.fetchall()
    
    import math

    total_paginas = math.ceil(
        total_registros / por_pagina
    )

    # 🔹 MÉTRICAS
    cursor.execute("SELECT COUNT(*) AS total FROM proyectos")
    total_proyectos = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) AS total FROM contratos")
    total_contratos = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) AS total FROM visitas")
    total_visitas = cursor.fetchone()['total']

    # 🔹 GRÁFICA 1
    cursor.execute("""
        SELECT 
            DATE_FORMAT(fecha_visita, '%Y-%m') AS mes,
            COUNT(*) AS total
        FROM visitas
        GROUP BY DATE_FORMAT(fecha_visita, '%Y-%m')
    """)

    datos = cursor.fetchall()

    meses = [fila['mes'] for fila in datos]
    totales_visitas = [fila['total'] for fila in datos]

    # 🔹 GRÁFICA 2
    cursor.execute("""
        SELECT 
            programa,
            COUNT(*) AS total
        FROM proyectos
        GROUP BY programa
    """)

    datos2 = cursor.fetchall()

    programas = [fila['programa'] for fila in datos2]
    totales_programas = [fila['total'] for fila in datos2]

    # 🔹 Cerrar conexión
    conexion.close()

    return render_template(
        "index.html",
        proyectos=proyectos,
        
        pagina=pagina,
        total_paginas=total_paginas,
        busqueda=busqueda,
        
        total_proyectos=total_proyectos,
        total_contratos=total_contratos,
        total_visitas=total_visitas,
        meses=meses,
        totales_visitas=totales_visitas,
        programas=programas,
        totales_programas=totales_programas
    )
    
    
# ------------------------
# FORMULARIO
# ------------------------
@proyectos_bp.route('/nuevo_proyecto')
@login_required
@solo_admin
def nuevo_proyecto():
    return render_template('formulario.html')

# ------------------------
# GUARDAR DATOS
# ------------------------
@proyectos_bp.route('/guardar_proyecto', methods=['POST'])
@login_required
@solo_admin
def guardar_proyecto():

    nombre = request.form['nombre']
    programa = request.form['programa']
    un_ad = request.form['un_ad']
    localidad = request.form['localidad']
    inversion = request.form['inversion']
    ejercicio_fiscal = request.form['ejercicio_fiscal']
    estatus_proyecto = request.form.get('estatus_proyecto') or 'Planeacion'

    conexion = conectar_db()
    cursor = conexion.cursor()

    sql = """
        INSERT INTO proyectos (
            nombre,
            programa,
            un_ad,
            localidad,
            inversion_autorizada,
            ejercicio_fiscal,
            estatus_proyecto
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    valores = (
        nombre,
        programa,
        un_ad,
        localidad,
        inversion,
        ejercicio_fiscal,
        estatus_proyecto
    )

    cursor.execute(sql, valores)

    conexion.commit()

    registrar_auditoria(
        current_user.nombre,
        f'Creó proyecto: {nombre}',
        'proyectos',
        request.remote_addr
    )

    conexion.close()

    return redirect('/')

# ------------------------
# RUTA PARA EDITAR
# ------------------------
@proyectos_bp.route('/editar_proyecto/<int:id>')
@login_required
@solo_admin
def editar_proyecto(id):
    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("SELECT * FROM proyectos WHERE id_proyecto = %s", (id,))
    proyecto = cursor.fetchone()

    conexion.close()
    return render_template('editar.html', proyecto=proyecto)

# ------------------------
# RUTA PARA ACTUALIZAR
# ------------------------
@proyectos_bp.route('/actualizar_proyecto', methods=['POST'])
@login_required
@solo_admin
def actualizar_proyecto():
    id = request.form['id']
    nombre = request.form['nombre']
    programa = request.form['programa']
    un_ad = request.form['un_ad']
    localidad = request.form['localidad']
    inversion = request.form['inversion']
    estatus_proyecto = request.form.get('estatus_proyecto') or 'Planeacion'

    conexion = conectar_db()
    cursor = conexion.cursor()

    sql = """
        UPDATE proyectos
        SET nombre=%s, programa=%s, un_ad=%s, localidad=%s, inversion_autorizada=%s, estatus_proyecto=%s
        WHERE id_proyecto=%s
    """

    valores = (nombre, programa, un_ad, localidad, inversion, estatus_proyecto, id)

    cursor.execute(sql, valores)
    
    registrar_auditoria(
        current_user.nombre,
        f'Editó proyecto ID {id}: {nombre}',
        'proyectos',
        request.remote_addr
    )
    
    conexion.commit()
    conexion.close()

    return redirect('/')

# ------------------------
# RUTA PARA ELIMINAR PROYECTO
# ------------------------
@proyectos_bp.route('/eliminar_proyecto/<int:id>', methods=['POST'])
@login_required
@solo_admin
def eliminar_proyecto(id):
    conexion = conectar_db()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        SELECT nombre
        FROM proyectos
        WHERE id_proyecto = %s
    """, (id,))
    proyecto = cursor.fetchone()

    if not proyecto:

        conexion.close()

        return redirect('/')

    nombre_proyecto = proyecto['nombre']

    cursor.execute("DELETE FROM proyectos WHERE id_proyecto = %s", (id,))
    
    registrar_auditoria(
        current_user.nombre,
        f'Eliminó proyecto: {nombre_proyecto}',
        'proyectos',
        request.remote_addr
    )
    
    conexion.commit()
    conexion.close()

    return redirect('/')

# ------------------------
# PANEL DE AUDITORÍA
# ------------------------
@proyectos_bp.route('/auditoria')
@login_required
@solo_admin
def auditoria():

    conexion = conectar_db()

    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            id_auditoria,
            usuario,
            accion,
            modulo,
            ip,
            fecha
        FROM auditoria
        ORDER BY fecha DESC
        LIMIT 300
    """)

    registros = cursor.fetchall()

    conexion.close()

    return render_template(
        'auditoria.html',
        registros=registros
    )

# ------------------------
# RUTA PARA EL EXPEDIENTE DE LOS CONTRATOS
# ------------------------
#Función auxiliar
def decimal_o_none(valor):
    if valor == '':
        return None
    return valor
#-------------------------
@proyectos_bp.route(
    '/expediente_contrato/<int:id_contrato>',
    methods=['GET', 'POST']
)
@login_required
def expediente_contrato(id_contrato):

    conexion = conectar_db()
    cursor = conexion.cursor(dictionary=True)

    if request.method == 'POST':

        no_contrato = request.form.get('no_contrato')
        contratista = request.form.get('contratista')
        fecha_contrato = request.form.get('fecha_contrato')

        inversion_autorizada = decimal_o_none(request.form.get('inversion_autorizada'))
        monto_contratado = decimal_o_none(request.form.get('monto_contratado'))
        anticipo = decimal_o_none(request.form.get('anticipo'))
        
        periodo_ejecucion = request.form.get('periodo_ejecucion') or None
        plazo_ejecucion = request.form.get('plazo_ejecucion') or None
        fecha_inicio_real = request.form.get('fecha_inicio_real') or None
        fecha_terminacion_real = request.form.get('fecha_terminacion_real') or None
        convenio_diferimiento = request.form.get('convenio_diferimiento') or None
        convenio_suspension = request.form.get('convenio_suspension') or None
        monto_ejercido = request.form.get('monto_ejercido') or None
        saldo = request.form.get('saldo') or None
        residente_obra = request.form.get('residente_obra') or None
        documentacion_relacionada = request.form.get('documentacion_relacionada') or None
        informacion_auditorias = request.form.get('informacion_auditorias') or None
        estatus_contrato = request.form.get('estatus_contrato') or 'En ejecucion'

        cursor.execute("""
            UPDATE contratos
            SET
                no_contrato = %s,
                fecha_contrato = %s,
                contratista = %s,
                inversion_autorizada = %s,
                monto_contratado = %s,
                anticipo = %s,
                periodo_ejecucion = %s,
                plazo_ejecucion = %s,
                fecha_inicio_real = %s,
                fecha_terminacion_real = %s,
                convenio_diferimiento = %s,
                convenio_suspension = %s,
                monto_ejercido = %s,
                saldo = %s,
                residente_obra = %s,
                documentacion_relacionada = %s,
                informacion_auditorias = %s,
                estatus_contrato = %s
            WHERE id_contrato = %s
        """, (

            no_contrato,
            fecha_contrato,
            contratista,
            inversion_autorizada,
            monto_contratado,
            anticipo,
            periodo_ejecucion,
            plazo_ejecucion,
            fecha_inicio_real,
            fecha_terminacion_real,
            convenio_diferimiento,
            convenio_suspension,
            monto_ejercido,
            saldo,
            residente_obra,
            documentacion_relacionada,
            informacion_auditorias,
            estatus_contrato,
            id_contrato))
        
        conexion.commit()
        cursor.close()
        conexion.close()

        return redirect(
            url_for(
                'proyectos.expediente_contrato',
                id_contrato=id_contrato
            )
        )

    cursor.execute("""
        SELECT
            c.*,

            p.nombre,
            p.programa,
            p.un_ad,
            p.localidad,
            p.ejercicio_fiscal,
            p.estatus_proyecto

        FROM contratos c

        INNER JOIN proyectos p
            ON c.id_proyecto = p.id_proyecto

        WHERE c.id_contrato = %s
    """, (id_contrato,))

    contrato = cursor.fetchone()
    
    cursor.execute("""
        SELECT
            id_visita,
            fecha_visita,
            supervisor,
            residente_obra,
            observaciones,
            archivo_acta
        FROM visitas
        WHERE id_contrato = %s
        ORDER BY fecha_visita DESC
    """, (id_contrato,))

    visitas = cursor.fetchall()

    conexion.close()

    return render_template(
        "expediente_contrato.html",
        contrato=contrato,
        visitas=visitas
    )
