from decimal import Decimal

from flask import Blueprint, render_template
from flask_login import login_required

from database import conectar_db
from routes.permisos import solo_admin_o_jefe


dashboard_bp = Blueprint(
    'dashboard',
    __name__,
    url_prefix='/dashboard'
)


def numero(valor):
    if valor is None:
        return 0
    if isinstance(valor, Decimal):
        return float(valor)
    return valor


@dashboard_bp.route('/ejecutivo')
@login_required
@solo_admin_o_jefe
def ejecutivo():

    conexion = conectar_db()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            COUNT(*) AS total_proyectos,
            COALESCE(SUM(inversion_autorizada), 0) AS inversion_total,
            SUM(CASE WHEN estatus_proyecto IN ('Suspendido', 'Observado') THEN 1 ELSE 0 END) AS proyectos_alerta
        FROM proyectos
    """)
    resumen_proyectos = cursor.fetchone()

    cursor.execute("""
        SELECT
            COUNT(*) AS total_contratos,
            COALESCE(SUM(monto_contratado), 0) AS monto_contratado_total,
            SUM(CASE WHEN estatus_contrato IN ('Suspendido', 'Observado') THEN 1 ELSE 0 END) AS contratos_alerta
        FROM contratos
    """)
    resumen_contratos = cursor.fetchone()

    cursor.execute("SELECT COUNT(*) AS total_visitas FROM visitas")
    total_visitas = cursor.fetchone()['total_visitas']

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM proyectos p
        LEFT JOIN contratos c
            ON p.id_proyecto = c.id_proyecto
        WHERE c.id_contrato IS NULL
    """)
    proyectos_sin_contrato = cursor.fetchone()['total']

    resumen = {
        'total_proyectos': resumen_proyectos['total_proyectos'],
        'total_contratos': resumen_contratos['total_contratos'],
        'total_visitas': total_visitas,
        'inversion_total': numero(resumen_proyectos['inversion_total']),
        'monto_contratado_total': numero(resumen_contratos['monto_contratado_total']),
        'proyectos_sin_contrato': proyectos_sin_contrato,
        'proyectos_alerta': resumen_proyectos['proyectos_alerta'] or 0,
        'contratos_alerta': resumen_contratos['contratos_alerta'] or 0
    }

    cursor.execute("""
        SELECT
            estatus_proyecto AS estatus,
            COUNT(*) AS total
        FROM proyectos
        GROUP BY estatus_proyecto
        ORDER BY total DESC, estatus_proyecto
    """)
    estatus_proyectos = cursor.fetchall()

    cursor.execute("""
        SELECT
            estatus_contrato AS estatus,
            COUNT(*) AS total
        FROM contratos
        GROUP BY estatus_contrato
        ORDER BY total DESC, estatus_contrato
    """)
    estatus_contratos = cursor.fetchall()

    cursor.execute("""
        SELECT
            programa,
            COUNT(*) AS total,
            COALESCE(SUM(inversion_autorizada), 0) AS inversion
        FROM proyectos
        GROUP BY programa
        ORDER BY inversion DESC
        LIMIT 8
    """)
    programas = cursor.fetchall()

    cursor.execute("""
        SELECT
            DATE_FORMAT(fecha_visita, '%Y-%m') AS mes,
            COUNT(*) AS total
        FROM visitas
        WHERE fecha_visita IS NOT NULL
        GROUP BY DATE_FORMAT(fecha_visita, '%Y-%m')
        ORDER BY mes
        LIMIT 12
    """)
    visitas_mes = cursor.fetchall()

    cursor.execute("""
        SELECT
            p.nombre AS proyecto,
            p.programa,
            p.localidad,
            c.no_contrato,
            c.contratista,
            c.estatus_contrato,
            COUNT(v.id_visita) AS total_visitas,
            MAX(v.fecha_visita) AS ultima_visita,
            CASE
                WHEN c.id_contrato IS NULL THEN 'Sin contrato'
                WHEN c.estatus_contrato IN ('Suspendido', 'Observado') THEN c.estatus_contrato
                WHEN COUNT(v.id_visita) = 0 THEN 'Sin visitas'
                WHEN MAX(v.fecha_visita) < DATE_SUB(CURDATE(), INTERVAL 30 DAY) THEN 'Sin visita reciente'
                ELSE 'Seguimiento regular'
            END AS condicion
        FROM proyectos p
        LEFT JOIN contratos c
            ON p.id_proyecto = c.id_proyecto
        LEFT JOIN visitas v
            ON c.id_contrato = v.id_contrato
        GROUP BY
            p.id_proyecto,
            p.nombre,
            p.programa,
            p.localidad,
            c.id_contrato,
            c.no_contrato,
            c.contratista,
            c.estatus_contrato
        HAVING condicion <> 'Seguimiento regular'
        ORDER BY
            CASE condicion
                WHEN 'Suspendido' THEN 1
                WHEN 'Observado' THEN 2
                WHEN 'Sin contrato' THEN 3
                WHEN 'Sin visitas' THEN 4
                WHEN 'Sin visita reciente' THEN 5
                ELSE 6
            END,
            ultima_visita ASC
        LIMIT 12
    """)
    atencion = cursor.fetchall()

    cursor.execute("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN condicion = 'verde' THEN 1 ELSE 0 END) AS verde,
            SUM(CASE WHEN condicion = 'amarillo' THEN 1 ELSE 0 END) AS amarillo,
            SUM(CASE WHEN condicion = 'rojo' THEN 1 ELSE 0 END) AS rojo
        FROM (
            SELECT
                c.id_contrato,
                CASE
                    WHEN c.estatus_contrato IN ('Suspendido', 'Observado') THEN 'rojo'
                    WHEN COUNT(v.id_visita) = 0 THEN 'rojo'
                    WHEN MAX(v.fecha_visita) < DATE_SUB(CURDATE(), INTERVAL 30 DAY) THEN 'amarillo'
                    ELSE 'verde'
                END AS condicion
            FROM contratos c
            LEFT JOIN visitas v
                ON c.id_contrato = v.id_contrato
            GROUP BY c.id_contrato, c.estatus_contrato
        ) semaforo
    """)
    semaforo = cursor.fetchone()

    conexion.close()

    semaforo = {clave: numero(valor) for clave, valor in semaforo.items()}

    return render_template(
        'dashboard_ejecutivo.html',
        resumen=resumen,
        estatus_proyectos=estatus_proyectos,
        estatus_contratos=estatus_contratos,
        programas=programas,
        visitas_mes=visitas_mes,
        atencion=atencion,
        semaforo=semaforo,
        chart_estatus_contratos={
            'labels': [fila['estatus'] for fila in estatus_contratos],
            'data': [fila['total'] for fila in estatus_contratos]
        },
        chart_programas={
            'labels': [fila['programa'] or 'Sin programa' for fila in programas],
            'data': [numero(fila['inversion']) for fila in programas]
        },
        chart_visitas={
            'labels': [fila['mes'] for fila in visitas_mes],
            'data': [fila['total'] for fila in visitas_mes]
        }
    )
