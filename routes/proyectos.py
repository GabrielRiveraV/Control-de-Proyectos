from flask import (
    Blueprint,
    render_template,
    request,
    redirect)
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

            c.no_contrato,

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
            c.no_contrato,
            c.id_contrato,
            c.archivo_contrato
            

        ORDER BY p.ejercicio_fiscal DESC,
                 p.id_proyecto DESC
        """

        cursor.execute(
            query,
            (
                f"%{busqueda}%",
                f"%{busqueda}%"
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

            c.no_contrato,

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
            c.no_contrato,
            c.id_contrato,
            c.archivo_contrato

        ORDER BY p.ejercicio_fiscal DESC,
                 p.id_proyecto DESC
        """)

    proyectos = cursor.fetchall()

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

    conexion = conectar_db()
    cursor = conexion.cursor()

    sql = """
        INSERT INTO proyectos (
            nombre,
            programa,
            un_ad,
            localidad,
            inversion_autorizada,
            ejercicio_fiscal
        )
        VALUES (%s, %s, %s, %s, %s, %s)
    """

    valores = (
        nombre,
        programa,
        un_ad,
        localidad,
        inversion,
        ejercicio_fiscal
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

    conexion = conectar_db()
    cursor = conexion.cursor()

    sql = """
        UPDATE proyectos
        SET nombre=%s, programa=%s, un_ad=%s, localidad=%s, inversion_autorizada=%s
        WHERE id_proyecto=%s
    """

    valores = (nombre, programa, un_ad, localidad, inversion, id)

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
@proyectos_bp.route('/eliminar_proyecto/<int:id>')
@login_required
@solo_admin
def eliminar_proyecto(id):
    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT nombre
        FROM proyectos
        WHERE id_proyecto = %s
    """, (id,))
    proyecto = cursor.fetchone()
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