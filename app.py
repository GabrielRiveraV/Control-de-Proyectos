import mysql.connector
from flask import Flask, render_template, request, redirect

app = Flask(__name__)

def conectar_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="xls3780n",
        database="control_proyectos"
    )

# ------------------------
# RUTA PRINCIPAL
# ------------------------
@app.route('/')
def inicio():
    conexion = conectar_db()
    cursor = conexion.cursor()

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
            c.no_contrato,
            COUNT(v.id_visita) as total_visitas,

            CASE
                WHEN c.id_contrato IS NOT NULL THEN 1
                ELSE 0
            END as tiene_contrato

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
            c.no_contrato,
            c.id_contrato
        """

        cursor.execute(query, (f"%{busqueda}%", f"%{busqueda}%"))

    else:
        cursor.execute("""
        SELECT 
            p.id_proyecto, 
            p.nombre, 
            p.programa, 
            p.un_ad, 
            p.localidad, 
            p.inversion_autorizada,
            c.no_contrato,
            COUNT(v.id_visita) as total_visitas,

            CASE
                WHEN c.id_contrato IS NOT NULL THEN 1
                ELSE 0
            END as tiene_contrato

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
            c.no_contrato,
            c.id_contrato
        """)

    proyectos = cursor.fetchall()

    # 🔹 MÉTRICAS
    cursor.execute("SELECT COUNT(*) FROM proyectos")
    total_proyectos = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM contratos")
    total_contratos = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM visitas")
    total_visitas = cursor.fetchone()[0]

    # 🔹 GRÁFICA 1
    cursor.execute("""
        SELECT DATE_FORMAT(fecha_visita, '%Y-%m'), COUNT(*)
        FROM visitas
        GROUP BY DATE_FORMAT(fecha_visita, '%Y-%m')
    """)

    datos = cursor.fetchall()

    meses = [fila[0] for fila in datos]
    totales_visitas = [fila[1] for fila in datos]

    # 🔹 GRÁFICA 2
    cursor.execute("""
        SELECT programa, COUNT(*) 
        FROM proyectos 
        GROUP BY programa
    """)

    datos2 = cursor.fetchall()

    programas = [fila[0] for fila in datos2]
    totales_programas = [fila[1] for fila in datos2]

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
@app.route('/nuevo_proyecto')
def nuevo_proyecto():
    return render_template('formulario.html')

# ------------------------
# GUARDAR DATOS
# ------------------------
@app.route('/guardar_proyecto', methods=['POST'])
def guardar_proyecto():
    nombre = request.form['nombre']
    programa = request.form['programa']
    un_ad = request.form['un_ad']
    localidad = request.form['localidad']
    inversion = request.form['inversion']

    conexion = conectar_db()
    cursor = conexion.cursor()

    sql = """
        INSERT INTO proyectos (nombre, programa, un_ad, localidad, inversion_autorizada)
        VALUES (%s, %s, %s, %s, %s)
    """

    valores = (nombre, programa, un_ad, localidad, inversion)

    cursor.execute(sql, valores)
    conexion.commit()
    conexion.close()

    return redirect('/')

# ------------------------
# RUTA PARA ELIMINAR
# ------------------------
@app.route('/eliminar_proyecto/<int:id>')
def eliminar_proyecto(id):
    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("DELETE FROM proyectos WHERE id_proyecto = %s", (id,))
    conexion.commit()
    conexion.close()

    return redirect('/')

# ------------------------
# RUTA PARA EDITAR
# ------------------------
@app.route('/editar_proyecto/<int:id>')
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
@app.route('/actualizar_proyecto', methods=['POST'])
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
    conexion.commit()
    conexion.close()

    return redirect('/')

# ------------------------
# NUEVO CONTRATO
# ------------------------
@app.route('/nuevo_contrato/<int:id_proyecto>')
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
@app.route('/guardar_contrato', methods=['POST'])
def guardar_contrato():
    id_proyecto = request.form['id_proyecto']
    no_contrato = request.form['no_contrato']
    fecha = request.form['fecha']
    contratista = request.form['contratista']
    monto = request.form['monto']

    conexion = conectar_db()
    cursor = conexion.cursor()

    sql = """
        INSERT INTO contratos (id_proyecto, no_contrato, fecha_contrato, contratista, monto_contratado)
        VALUES (%s, %s, %s, %s, %s)
    """

    try:
        cursor.execute(sql, (id_proyecto, no_contrato, fecha, contratista, monto))
        conexion.commit()
    except:
        conexion.close()
        return "⚠️ Este proyecto ya tiene un contrato asignado"

    conexion.close()
    return redirect('/')

# ------------------------
# NUEVA VISITA
# ------------------------
@app.route('/nueva_visita/<int:id_proyecto>')
def nueva_visita(id_proyecto):
    conexion = conectar_db()
    cursor = conexion.cursor()

    # 🔍 CONSULTA (AQUÍ VA EL JOIN)
    cursor.execute("""
        SELECT c.id_contrato, c.no_contrato
        FROM contratos c
        INNER JOIN proyectos p ON c.id_proyecto = p.id_proyecto
        WHERE p.id_proyecto = %s
    """, (id_proyecto,))

    contrato = cursor.fetchone()

    # 🧪 DEBUG (AQUÍ)
    print("ID PROYECTO:", id_proyecto)
    print("CONTRATO:", contrato)

    conexion.close()

    # 🚨 VALIDACIÓN (AQUÍ)
    if not contrato:
        return f"⚠️ No se encontró contrato para el proyecto ID {id_proyecto}"

    return render_template('nueva_visita.html', contrato=contrato)

# ------------------------
# GUARDAR VISITA
# ------------------------
@app.route('/guardar_visita', methods=['POST'])
def guardar_visita():
    id_contrato = request.form.get('id_contrato')
    fecha = request.form.get('fecha')
    supervisor = request.form.get('supervisor')
    residente = request.form.get('residente')
    observaciones = request.form.get('observaciones')

    # 🔴 VALIDACIÓN IMPORTANTE
    if not id_contrato:
        return "⚠️ Error: No se recibió el contrato. Verifica que el proyecto tenga un contrato asignado."

    conexion = conectar_db()
    cursor = conexion.cursor()

    sql = """
        INSERT INTO visitas (id_contrato, fecha_visita, supervisor, residente_obra, observaciones)
        VALUES (%s, %s, %s, %s, %s)
    """

    valores = (id_contrato, fecha, supervisor, residente, observaciones)

    cursor.execute(sql, valores)
    conexion.commit()
    conexion.close()

    return redirect('/')

# ------------------------
# VISITAS GENERALES
# ------------------------
@app.route('/visitas')
def ver_visitas():
    conexion = conectar_db()
    cursor = conexion.cursor()

    busqueda = request.args.get('busqueda')

    if busqueda:
        cursor.execute("""
            SELECT c.no_contrato, p.nombre, v.fecha_visita, 
                   v.supervisor, v.residente_obra, v.observaciones
            FROM visitas v
            JOIN contratos c ON v.id_contrato = c.id_contrato
            JOIN proyectos p ON c.id_proyecto = p.id_proyecto
            WHERE p.nombre LIKE %s
            ORDER BY v.fecha_visita DESC
        """, (f"%{busqueda}%",))
    else:
        cursor.execute("""
            SELECT c.no_contrato, p.nombre, v.fecha_visita, 
                   v.supervisor, v.residente_obra, v.observaciones
            FROM visitas v
            JOIN contratos c ON v.id_contrato = c.id_contrato
            JOIN proyectos p ON c.id_proyecto = p.id_proyecto
            ORDER BY v.fecha_visita DESC
        """)

    visitas = cursor.fetchall()
    conexion.close()

    return render_template('visitas.html', visitas=visitas)

# ------------------------
# VISITAS POR PROYECTO
# ------------------------
@app.route('/visitas_proyecto/<int:id_proyecto>')
def visitas_proyecto(id_proyecto):
    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT p.nombre, c.no_contrato, v.fecha_visita, v.supervisor, v.residente_obra, v.observaciones
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
# LOGIN
# ------------------------
from flask import session

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        password = request.form['password']

        conexion = conectar_db()
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT id_usuario, nombre, rol 
            FROM usuarios 
            WHERE usuario=%s AND password=%s
        """, (usuario, password))

        user = cursor.fetchone()
        conexion.close()

        if user:
            session['id_usuario'] = user[0]
            session['nombre'] = user[1]
            session['rol'] = user[2]

            return redirect('/')
        else:
            return "Usuario o contraseña incorrectos"

    return render_template('login.html')

# ------------------------
# EJECUCIÓN
# ------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)