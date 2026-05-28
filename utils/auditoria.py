from database import conectar_db


def registrar_auditoria(
    usuario,
    accion,
    modulo,
    ip
):

    conexion = conectar_db()

    cursor = conexion.cursor()

    sql = """
        INSERT INTO auditoria (
            usuario,
            accion,
            modulo,
            ip
        )
        VALUES (%s, %s, %s, %s)
    """

    valores = (
        usuario,
        accion,
        modulo,
        ip
    )

    cursor.execute(sql, valores)

    conexion.commit()

    conexion.close()