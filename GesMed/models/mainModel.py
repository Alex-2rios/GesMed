from app import mysql


def get_user_by_rfc(rfc):
    cursor = mysql.connection.cursor()
    cursor.execute(
        """
        SELECT ID_Medico, Nombre_Medico, AP_Medico, AM_Medico, Contrasena, Rol
        FROM Medicos
        WHERE RFC_Medico = %s
        """,
        (rfc,),
    )
    user = cursor.fetchone()
    cursor.close()
    return user


def get_dashboard_data():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM Medicos WHERE estado = 1")
    total_medicos = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM Medicos WHERE Rol = 'admin' AND estado = 1")
    total_admins = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM Pacientes WHERE estado = 1")
    total_pacientes = cursor.fetchone()[0]
    cursor.execute(
        """
        SELECT ID_Medico, NombreCompleto(Nombre_Medico, AP_Medico, AM_Medico) AS Nombre_Completo,
               Nombre_Medico, AP_Medico, AM_Medico, RFC_Medico, Cedula, Correo_Medico, Rol
        FROM Medicos WHERE estado = 1
        """
    )
    medicos = cursor.fetchall()
    cursor.execute(
        """
        SELECT ID_Medico, Nombre_Medico, AP_Medico, AM_Medico, RFC_Medico,
               Cedula, Correo_Medico, Rol FROM Medicos WHERE estado = 1
        """
    )
    medicos2 = cursor.fetchall()
    cursor.execute(
        """
        SELECT
            P.ID_Paciente,
            P.Nombre_Paciente, P.AP_Paciente, P.AM_Paciente,
            P.FechaNacimiento,
            CalcularEdad(FechaNacimiento),
            M.Nombre_Medico, M.AP_Medico, M.AM_Medico,
            P.EnfermedadesCronicas, P.Alergias, P.AntecedentesFamiliares
       FROM Pacientes P
       JOIN Medicos M ON P.ID_Medico = M.ID_Medico
       WHERE P.estado = 1 AND M.estado = 1
        """
    )
    pacientes = cursor.fetchall()
    cursor.execute(
        """
        SELECT
            C.ID_Cita, P.Nombre_Paciente, P.AP_Paciente, P.AM_Paciente,
            C.Fecha,
            M.Nombre_Medico, M.AP_Medico, M.AM_Medico
        FROM Citas C
        JOIN Pacientes P ON C.ID_Paciente = P.ID_Paciente
        JOIN Medicos M ON C.ID_Medico = M.ID_Medico
        WHERE C.estado = 1
        """
    )
    citas = cursor.fetchall()
    cursor.close()
    return {
        "total_medicos": total_medicos,
        "total_admins": total_admins,
        "total_pacientes": total_pacientes,
        "medicos": medicos,
        "medicos2": medicos2,
        "pacientes": pacientes,
        "citas": citas,
    }


def get_index_data(id_medico):
    cursor = mysql.connection.cursor()
    cursor.execute(
        """
        SELECT ID_Paciente, ID_Medico, Nombre_Paciente, AP_Paciente, AM_Paciente, FechaNacimiento
        FROM Pacientes
        WHERE ID_Medico = %s AND estado = 1
        """,
        (id_medico,),
    )
    pacientes = cursor.fetchall()
    cursor.execute(
        """
        SELECT
            C.ID_Cita, P.Nombre_Paciente, P.AP_Paciente, P.AM_Paciente,
            C.Fecha,
            M.Nombre_Medico, M.AP_Medico, M.AM_Medico
        FROM Citas C
        JOIN Pacientes P ON C.ID_Paciente = P.ID_Paciente
        JOIN Medicos M ON C.ID_Medico = M.ID_Medico
        WHERE C.ID_Medico = %s AND C.estado = 1 AND P.estado = 1 AND M.estado = 1
        """,
        (id_medico,),
    )
    citas = cursor.fetchall()
    cursor.close()
    return pacientes, citas


def insert_medico(rfc, nombre, ap_pat, ap_mat, cedula, correo, contrasena, rol):
    cursor = mysql.connection.cursor()
    cursor.execute(
        """
        INSERT INTO Medicos (RFC_Medico, Nombre_Medico, AP_Medico, AM_Medico, Cedula, Correo_Medico, Contrasena, Rol)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (rfc, nombre, ap_pat, ap_mat, cedula, correo, contrasena, rol),
    )
    mysql.connection.commit()
    cursor.close()


def insert_paciente(id_medico, nombre, ap_pat, ap_mat, fecha_nacimiento, enfermedades, alergias, antecedentes):
    cursor = mysql.connection.cursor()
    cursor.execute(
        """
        INSERT INTO Pacientes (ID_Medico, Nombre_Paciente, AP_Paciente, AM_Paciente, FechaNacimiento,
                               EnfermedadesCronicas, Alergias, AntecedentesFamiliares, estado)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1)
        """,
        (id_medico, nombre, ap_pat, ap_mat, fecha_nacimiento, enfermedades, alergias, antecedentes),
    )
    mysql.connection.commit()
    cursor.close()


def insert_cita(
    id_paciente,
    id_medico,
    fecha,
    peso,
    altura,
    temperatura,
    latidos,
    saturacion,
    glucosa,
    sintomas,
    diagnostico,
    tratamiento,
    estudios,
):
    cursor = mysql.connection.cursor()
    insertar_cita = (
        """
        INSERT INTO Citas (
            ID_Paciente, ID_Medico, Fecha, Peso, Altura, Temperatura, LatidosPorMinuto,
            SaturacionOxigeno, Glucosa, Sintomas, Diagnostico, Tratamiento, SolicitudEstudios, PDF_Receta
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
    )
    cursor.execute(
        insertar_cita,
        (
            id_paciente,
            id_medico,
            fecha,
            peso,
            altura,
            temperatura,
            latidos,
            saturacion,
            glucosa,
            sintomas,
            diagnostico,
            tratamiento,
            estudios,
            None,
        ),
    )
    mysql.connection.commit()
    id_cita = cursor.lastrowid
    cursor.close()
    return id_cita


def get_paciente_nombre(id_paciente):
    cursor = mysql.connection.cursor()
    cursor.execute(
        """
        SELECT CONCAT(Nombre_Paciente, ' ', AP_Paciente, ' ', AM_Paciente)
        FROM Pacientes
        WHERE ID_Paciente = %s
        """,
        (id_paciente,),
    )
    resultado = cursor.fetchone()
    cursor.close()
    return resultado[0] if resultado else "Paciente desconocido"


def get_medico_nombre(id_medico):
    cursor = mysql.connection.cursor()
    cursor.execute(
        """
        SELECT CONCAT(Nombre_Medico, ' ', AP_Medico, ' ', AM_Medico)
        FROM Medicos
        WHERE ID_Medico = %s
        """,
        (id_medico,),
    )
    resultado = cursor.fetchone()
    cursor.close()
    return resultado[0] if resultado else "Médico desconocido"


def update_cita_pdf(id_cita, pdf_bytes):
    cursor = mysql.connection.cursor()
    cursor.execute("UPDATE Citas SET PDF_Receta = %s WHERE ID_Cita = %s", (pdf_bytes, id_cita))
    mysql.connection.commit()
    cursor.close()


def insert_receta(id_cita, id_medico):
    cursor = mysql.connection.cursor()
    cursor.execute(
        "INSERT INTO Recetas (ID_Cita, ID_Medico, FechaGeneracion) VALUES (%s, %s, CURDATE())",
        (id_cita, id_medico),
    )
    mysql.connection.commit()
    cursor.close()


def get_pdf_receta(id_cita):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT PDF_Receta FROM Citas WHERE ID_Cita = %s", (id_cita,))
    resultado = cursor.fetchone()
    cursor.close()
    return resultado


def deactivate_cita(id_cita):
    cursor = mysql.connection.cursor()
    cursor.execute("UPDATE Recetas SET estado = 0 WHERE ID_Cita = %s", (id_cita,))
    cursor.execute("UPDATE Citas SET estado = 0 WHERE ID_Cita = %s", (id_cita,))
    mysql.connection.commit()
    cursor.close()


def get_active_medicos():
    cursor = mysql.connection.cursor()
    cursor.execute(
        """
        SELECT ID_Medico, Nombre_Medico, AP_Medico, AM_Medico, RFC_Medico, Cedula, Correo_Medico, Rol
        FROM Medicos
        WHERE estado = 1
        """
    )
    medicos = cursor.fetchall()
    cursor.close()
    return medicos


def delete_medico(id_medico):
    cursor = mysql.connection.cursor()
    cursor.execute(
        """
        DELETE FROM Citas
        WHERE ID_Paciente IN (
            SELECT ID_Paciente FROM Pacientes WHERE ID_Medico = %s
        )
        """,
        (id_medico,),
    )
    cursor.execute("DELETE FROM Pacientes WHERE ID_Medico = %s", (id_medico,))
    cursor.execute("DELETE FROM Citas WHERE ID_Medico = %s", (id_medico,))
    cursor.execute("UPDATE Medicos SET estado = 0 WHERE ID_Medico = %s", (id_medico,))
    mysql.connection.commit()
    cursor.close()


def delete_paciente(id_paciente):
    cursor = mysql.connection.cursor()
    cursor.execute("UPDATE Citas SET estado = 0 WHERE ID_Paciente = %s", (id_paciente,))
    cursor.execute("UPDATE Pacientes SET estado = 0 WHERE ID_Paciente = %s", (id_paciente,))
    mysql.connection.commit()
    cursor.close()


def update_medico(id_medico, nombre, ap_pat, ap_mat, rfc, cedula, correo, rol):
    cursor = mysql.connection.cursor()
    cursor.execute(
        """
        UPDATE Medicos
        SET Nombre_Medico=%s, AP_Medico=%s, AM_Medico=%s, RFC_Medico=%s,
            Cedula=%s, Correo_Medico=%s, Rol=%s
        WHERE ID_Medico=%s
        """,
        (nombre, ap_pat, ap_mat, rfc, cedula, correo, rol, id_medico),
    )
    mysql.connection.commit()
    cursor.close()


def update_paciente(
    id_paciente,
    nombre,
    ap_pat,
    ap_mat,
    fecha_nacimiento,
    enfermedades,
    alergias,
    antecedentes,
):
    cursor = mysql.connection.cursor()
    cursor.execute(
        """
        UPDATE Pacientes
        SET
            Nombre_Paciente = %s,
            AP_Paciente = %s,
            AM_Paciente = %s,
            FechaNacimiento = %s,
            EnfermedadesCronicas = %s,
            Alergias = %s,
            AntecedentesFamiliares = %s
        WHERE ID_Paciente = %s
        """,
        (nombre, ap_pat, ap_mat, fecha_nacimiento, enfermedades, alergias, antecedentes, id_paciente),
    )
    mysql.connection.commit()
    cursor.close()
