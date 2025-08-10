from flask import Flask, request, render_template, redirect, url_for, flash, session, jsonify
from flask_mysqldb import MySQL
from config import Config
from xhtml2pdf import pisa
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from flask import Response
import mysql.connector
import MySQLdb


gesmed = Flask(__name__)
gesmed.config.from_object(Config)

mysql = MySQL(gesmed)

@gesmed.route("/DBCheck")
def dbCheck():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT 1")
        return jsonify({"status": "Ok", "message": "Conectado con exitote!!! ;)"}), 200
    except MySQLdb.MySQLError as e:
        return jsonify({"status": "Error", "message": str(e)}), 500





@gesmed.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        rfc = request.form.get("rfc")
        password = request.form.get("password")

        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT ID_Medico, Nombre_Medico, AP_Medico, AM_Medico, Contrasena, Rol
            FROM Medicos
            WHERE RFC_Medico = %s
        """, (rfc,))
        user = cursor.fetchone()
        cursor.close()

        if user:
            stored_password = user[4]
            if password == stored_password:
                session["user_id"] = user[0]
                session["nombre_medico"] = f"Dr. {user[1]} {user[2]} {user[3]}"
                session["rol"] = user[5]
                flash("¡Login exitoso!", "success")

                if user[5] == "admin":
                    return redirect(url_for("dashboard"))
                elif user[5] == "medico":
                    return redirect(url_for("index"))
                else:
                    return redirect(url_for("login"))
            else:
                flash("Contraseña incorrecta", "error")
        else:
            flash("Usuario no encontrado", "error")

    return render_template("login.html")





@gesmed.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    cursor = mysql.connection.cursor()

    # Totales
    cursor.execute("SELECT COUNT(*) FROM Medicos WHERE estado = 1")
    total_medicos = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM Medicos WHERE Rol = 'admin' AND estado = 1")
    total_admins = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM Pacientes WHERE estado = 1")
    total_pacientes = cursor.fetchone()[0]
    
    # Médicos
    cursor.execute("SELECT ID_Medico, NombreCompleto(Nombre_Medico, AP_Medico, AM_Medico) AS Nombre_Completo, Nombre_Medico, AP_Medico, AM_Medico, RFC_Medico, Cedula, Correo_Medico, Rol FROM Medicos WHERE estado = 1")
    medicos = cursor.fetchall()
    
    # Médicos sin funcion de NombreCompleto
    cursor.execute("SELECT ID_Medico, Nombre_Medico, AP_Medico, AM_Medico, RFC_Medico, Cedula, Correo_Medico, Rol FROM Medicos WHERE estado = 1")
    medicos2 = cursor.fetchall()

    # Pacientes
    cursor.execute("""
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
    """)
    pacientes = cursor.fetchall() 
    
    
    # Citas
    cursor.execute("""
        SELECT
            C.ID_Cita, P.Nombre_Paciente, P.AP_Paciente, P.AM_Paciente,
            C.Fecha,
            M.Nombre_Medico, M.AP_Medico, M.AM_Medico
        FROM Citas C
        JOIN Pacientes P ON C.ID_Paciente = P.ID_Paciente
        JOIN Medicos M ON C.ID_Medico = M.ID_Medico
        WHERE C.estado = 1
    """)
    citas = cursor.fetchall()

    cursor.close()

  
    citas = [dict(zip(
        ["ID_Cita", "Nombre_Paciente", "AP_Paciente", "AM_Paciente", "Fecha", "Nombre_Medico", "AP_Medico", "AM_Medico"],
        cita)) for cita in citas]

    return render_template(
        "dashboard.html",
        nombre_medico=session.get("nombre_medico"),
        rol=session.get("rol"),
        user_id=session.get("user_id"),
        total_medicos=total_medicos,
        total_admins=total_admins,
        total_pacientes=total_pacientes,
        medicos=medicos,
        pacientes=pacientes,
        citas=citas
    )
  
@gesmed.route("/index")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))

    id_medico = session["user_id"]  

    cursor = mysql.connection.cursor()

    # Obtener pacientes de este médico
    cursor.execute("""
        SELECT ID_Paciente, ID_Medico, Nombre_Paciente, AP_Paciente, AM_Paciente, FechaNacimiento 
        FROM Pacientes
        WHERE ID_Medico = %s AND estado = 1
    """, (id_medico,))
    pacientes = cursor.fetchall()

    # Obtener citas de este médico
    cursor.execute("""
        SELECT
            C.ID_Cita, P.Nombre_Paciente, P.AP_Paciente, P.AM_Paciente,
            C.Fecha,
            M.Nombre_Medico, M.AP_Medico, M.AM_Medico
        FROM Citas C
        JOIN Pacientes P ON C.ID_Paciente = P.ID_Paciente
        JOIN Medicos M ON C.ID_Medico = M.ID_Medico
        WHERE C.ID_Medico = %s AND C.estado = 1 AND P.estado = 1 AND M.estado = 1
    """, (id_medico,))
    citas = cursor.fetchall()

    cursor.close()

    citas = [dict(zip(
        ["ID_Cita", "Nombre_Paciente", "AP_Paciente", "AM_Paciente", "Fecha", "Nombre_Medico", "AP_Medico", "AM_Medico"],
        cita)) for cita in citas]

    # Cantidad de pacientes para mostrar en la tarjeta
    total_pacientes = len(pacientes)

    return render_template("index.html",
        nombre_medico=session.get("nombre_medico"),
        rol=session.get("rol"),
        user_id=id_medico,
        pacientes=pacientes,
        citas=citas,
        total_pacientes=total_pacientes
    )



@gesmed.route("/agregar_medico", methods=["POST"])
def agregar_medico():
    if "user_id" not in session or session.get("rol") != "admin":
        flash("No tienes permisos para agregar médicos.", "error")
        return redirect(url_for("dashboard"))

    
    nombre = request.form.get("nombre")
    apellido_paterno = request.form.get("apellido_paterno")
    apellido_materno = request.form.get("apellido_materno")
    cedula = request.form.get("cedula")
    correo = request.form.get("correo")
    contrasena = request.form.get("contrasena")
    verif_contrasena = request.form.get("verif_contrasena")
    rfc = request.form.get("rfc")
    rol = request.form.get("rol")

    if contrasena != verif_contrasena:
        flash("Las contraseñas no coinciden.", "error")
        return redirect(url_for("dashboard"))

    cursor = mysql.connection.cursor()

    try:
        cursor.execute("""
            INSERT INTO Medicos (RFC_Medico, Nombre_Medico, AP_Medico, AM_Medico, Cedula, Correo_Medico, Contrasena, Rol)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (rfc, nombre, apellido_paterno, apellido_materno, cedula, correo, contrasena, rol))

        mysql.connection.commit()
        flash("Médico agregado correctamente.", "success")

    except Exception as e:
        mysql.connection.rollback()
        flash(f"Error al agregar médico: {str(e)}", "error")

    finally:
        cursor.close()

    return redirect(url_for("dashboard"))





@gesmed.route("/agregar_paciente", methods=["POST"])
def agregar_paciente():
    if "user_id" not in session:
        flash("Debes iniciar sesión para registrar pacientes.", "error")
        return redirect(url_for("login"))

    nombre_medico = request.form.get("medico_nombre")  # solo informativo
    nombre = request.form.get("nombre")
    apellido_paterno = request.form.get("apellido_paterno")
    apellido_materno = request.form.get("apellido_materno")
    fecha_nacimiento = request.form.get("fecha_nacimiento")
    alergias = request.form.get("alergias")
    antecedentes = request.form.get("antecedentes_familiares")
    enfermedades = request.form.get("enfermedades_cronicas")

    id_medico = session.get("user_id")  # este es el médico que está logueado

    if not nombre or not apellido_paterno or not fecha_nacimiento:
        flash("Faltan campos obligatorios.", "error")
        return redirect(url_for("dashboard"))

    try:
        cursor = mysql.connection.cursor()
        cursor.execute("""
            INSERT INTO Pacientes (ID_Medico, Nombre_Paciente, AP_Paciente, AM_Paciente, FechaNacimiento,
                                   EnfermedadesCronicas, Alergias, AntecedentesFamiliares, estado)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1)
        """, (id_medico, nombre, apellido_paterno, apellido_materno,
              fecha_nacimiento, enfermedades, alergias, antecedentes))
        mysql.connection.commit()
        flash("Paciente registrado correctamente.", "success")

    except Exception as e:
        mysql.connection.rollback()
        flash(f"Error al registrar paciente: {str(e)}", "error")

    finally:
        cursor.close()

    return redirect(url_for("dashboard"))

@gesmed.route('/agregar_cita', methods=['POST'])
def agregar_cita():
    try:
        print("Formulario recibido:", request.form)

        # Obtener datos y convertir con validación
        id_paciente = request.form['id_paciente']
        id_medico = request.form['id_medico']
        fecha = request.form['fecha']

        def to_decimal(value, campo):
            try:
                return float(value)
            except (ValueError, TypeError):
                raise ValueError(f"El campo '{campo}' debe ser un número válido.")

        def to_int(value, campo):
            try:
                return int(value)
            except (ValueError, TypeError):
                raise ValueError(f"El campo '{campo}' debe ser un entero válido.")

        peso = to_decimal(request.form['peso'], 'peso')
        altura = to_decimal(request.form['altura'], 'altura')
        temperatura = to_decimal(request.form['temperatura'], 'temperatura')
        latidos = to_int(request.form['latidos'], 'latidos')
        saturacion = to_decimal(request.form['saturacion'], 'saturacion')
        glucosa = to_decimal(request.form['glucosa'], 'glucosa')

        sintomas = request.form['sintomas']
        diagnostico = request.form['diagnostico']
        tratamiento = request.form['tratamiento']
        estudios = request.form['estudios']

        # Validar que fecha no esté vacía
        if not fecha:
            raise ValueError("El campo 'fecha' es obligatorio.")

        # Mostrar valores para debug
        print("Valores a insertar:", id_paciente, id_medico, fecha, peso, altura, temperatura, latidos,
              saturacion, glucosa, sintomas, diagnostico, tratamiento, estudios)

        cursor = mysql.connection.cursor()
        insertar_cita = """
        INSERT INTO Citas (
            ID_Paciente, ID_Medico, Fecha, Peso, Altura, Temperatura, LatidosPorMinuto,
            SaturacionOxigeno, Glucosa, Sintomas, Diagnostico, Tratamiento, SolicitudEstudios, PDF_Receta
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        cursor.execute(insertar_cita, (
            id_paciente, id_medico, fecha, peso, altura, temperatura, latidos,
            saturacion, glucosa, sintomas, diagnostico, tratamiento, estudios, None
        ))
        mysql.connection.commit()
        id_cita = cursor.lastrowid
        print(f"Cita insertada con ID {id_cita}")

        cursor = mysql.connection.cursor()
        
        # Consulta nombre completo del paciente antes de generar el PDF
        cursor.execute("""
        SELECT CONCAT(Nombre_Paciente, ' ', AP_Paciente, ' ', AM_Paciente) 
        FROM Pacientes 
        WHERE ID_Paciente = %s
        """, (id_paciente,))
        nombre_paciente = cursor.fetchone()
        if nombre_paciente:
            nombre_paciente = nombre_paciente[0]
        else:
            nombre_paciente = "Paciente desconocido"

        # Consulta nombre completo del médico
        cursor.execute("""
        SELECT CONCAT(Nombre_Medico, ' ', AP_Medico, ' ', AM_Medico)
        FROM Medicos
        WHERE ID_Medico = %s
        """, (id_medico,))
        nombre_medico = cursor.fetchone()
        if nombre_medico:
            nombre_medico = nombre_medico[0]
        else:
            nombre_medico = "Médico desconocido"




        # Generar PDF
        pdf_buffer = BytesIO()
        html = render_template("pdf_receta.html", fecha=fecha, sintomas=sintomas, diagnostico=diagnostico,
                       tratamiento=tratamiento, nombre_paciente=nombre_paciente, nombre_medico=nombre_medico)


        status = pisa.CreatePDF(html, dest=pdf_buffer)
        if status.err:
            print("Error al generar PDF")
            flash("No se pudo generar el PDF", "danger")
            return redirect(url_for('dashboard'))

        # Actualizar cita con PDF
        cursor.execute("UPDATE Citas SET PDF_Receta = %s WHERE ID_Cita = %s", (pdf_buffer.getvalue(), id_cita))
        mysql.connection.commit()
        print("PDF agregado a la cita.")

        # Insertar en Recetas
        cursor.execute("INSERT INTO Recetas (ID_Cita, ID_Medico, FechaGeneracion) VALUES (%s, %s, CURDATE())", (id_cita, id_medico))
        mysql.connection.commit()
        print("Receta registrada.")

        flash("Cita registrada y receta generada correctamente", "success")
        return redirect(url_for('dashboard'))

    except Exception as e:
        print("Error en agregar_cita:", e)
        flash(f"Error al registrar la cita: {str(e)}", "danger")
        return redirect(url_for('dashboard'))


    
@gesmed.route("/cita/pdf/<int:id>")
def ver_pdf(id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT PDF_Receta FROM Citas WHERE ID_Cita = %s", (id,))
    resultado = cursor.fetchone()
    cursor.close()

    if resultado and resultado[0]:
        return Response(resultado[0], mimetype='application/pdf')
    else:
        return "PDF no encontrado", 404



@gesmed.route('/eliminar_cita/<int:id>', methods=['POST'])
def eliminar_cita(id):
    try:
        cursor = mysql.connection.cursor()
        # Cambiar estado de las recetas relacionadas a 0 (inactivas)
        cursor.execute("UPDATE Recetas SET estado = 0 WHERE ID_Cita = %s", (id,))
        # Cambiar estado de la cita a 0 (inactiva)
        cursor.execute("UPDATE Citas SET estado = 0 WHERE ID_Cita = %s", (id,))
        mysql.connection.commit()
        flash("Cita eliminada correctamente.", "success")
    except Exception as e:
        print("Error al eliminar cita:", e)
        flash("Error al eliminar la cita.", "danger")
    return redirect(url_for('dashboard'))



@gesmed.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada exitosamente", "info")
    return redirect(url_for("login"))


@gesmed.route("/medicos")
def listar_medicos():
    if "user_id" not in session or session.get("rol") != "admin":
        return redirect(url_for("login"))

    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT ID_Medico, Nombre_Medico, AP_Medico, AM_Medico, RFC_Medico, Cedula, Correo_Medico, Rol
        FROM Medicos
        WHERE estado = 1
    """)
    medicos = cursor.fetchall()
    cursor.close()

    return render_template("medicos.html", medicos=medicos)


@gesmed.route("/eliminar_medico/<int:id>", methods=["POST"])
def eliminar_medico(id):
    if "user_id" not in session or session.get("rol") != "admin":
        flash("No tienes permisos para eliminar médicos.", "error")
        return redirect(url_for("dashboard"))

    try:
        cursor = mysql.connection.cursor()

        # Eliminar citas de pacientes de este médico
        cursor.execute("""
            DELETE FROM Citas
            WHERE ID_Paciente IN (
                SELECT ID_Paciente FROM Pacientes WHERE ID_Medico = %s
            )
        """, (id,))

        # Eliminar pacientes de este médico
        cursor.execute("DELETE FROM Pacientes WHERE ID_Medico = %s", (id,))

        # Eliminar citas directamente del médico (por si existen)
        cursor.execute("DELETE FROM Citas WHERE ID_Medico = %s", (id,))

        # Finalmente eliminar al médico
        cursor.execute("UPDATE Medicos SET estado = 0 WHERE ID_Medico = %s", (id,))
        mysql.connection.commit()
        flash("Médico y datos relacionados eliminados correctamente.", "success")
    except Exception as e:
        mysql.connection.rollback()
        flash(f"Error al eliminar médico: {str(e)}", "error")
    finally:
        cursor.close()

    return redirect(url_for("dashboard"))

@gesmed.route("/eliminar_paciente/<int:id>", methods=["POST"])
def eliminar_paciente(id):
    if "user_id" not in session:
        flash("Debes iniciar sesión para eliminar pacientes.", "error")
        return redirect(url_for("login"))

    try:
        cursor = mysql.connection.cursor()

        # Eliminar citas del paciente
        cursor.execute("UPDATE Citas SET estado = 0 WHERE ID_Paciente = %s", (id,))

        # Luego eliminar al paciente
        cursor.execute("UPDATE Pacientes SET estado = 0 WHERE ID_Paciente = %s", (id,))
        mysql.connection.commit()
        flash("Paciente y citas relacionadas eliminadas correctamente.", "success")
    except Exception as e:
        mysql.connection.rollback()
        flash(f"Error al eliminar paciente: {str(e)}", "error")
    finally:
        cursor.close()

    return redirect(url_for("dashboard"))



@gesmed.route("/actualizar_medico/<int:id>", methods=["POST"])
def actualizar_medico(id):
    if "user_id" not in session or session.get("rol") != "admin":
        flash("No tienes permisos para actualizar médicos.", "error")
        return redirect(url_for("dashboard"))

    nombre = request.form.get("nombre")
    apellido_paterno = request.form.get("apellido_paterno")
    apellido_materno = request.form.get("apellido_materno")
    rfc = request.form.get("rfc")
    cedula = request.form.get("cedula")
    correo = request.form.get("correo")
    rol = request.form.get("rol")

    try:
        cursor = mysql.connection.cursor()
        cursor.execute("""
            UPDATE Medicos
            SET Nombre_Medico=%s, AP_Medico=%s, AM_Medico=%s, RFC_Medico=%s,
                Cedula=%s, Correo_Medico=%s, Rol=%s
            WHERE ID_Medico=%s
        """, (nombre, apellido_paterno, apellido_materno, rfc, cedula, correo, rol, id))

        mysql.connection.commit()
        flash("Médico actualizado correctamente.", "success")

    except Exception as e:
        mysql.connection.rollback()
        flash(f"Error al actualizar médico: {str(e)}", "error")

    finally:
        cursor.close()

    return redirect(url_for("dashboard"))


@gesmed.route("/actualizar_paciente/<int:id>", methods=["POST"])
def actualizar_paciente(id):
    try:
        nombre = request.form["nombre"]
        ap_paterno = request.form["apellido_paterno"]
        ap_materno = request.form["apellido_materno"]
        fecha_nacimiento = request.form["fecha_nacimiento"]
        enfermedades_cronicas = request.form["enfermedades_cronicas"]
        alergias = request.form["alergias"]
        antecedentes = request.form["antecedentes_familiares"]

        cursor = mysql.connection.cursor()
        cursor.execute("""
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
        """, (nombre, ap_paterno, ap_materno, fecha_nacimiento, enfermedades_cronicas, alergias, antecedentes, id))

        mysql.connection.commit()
        flash("Paciente actualizado correctamente", "success")
    except Exception as e:
        mysql.connection.rollback()
        flash(f"Error al actualizar paciente: {e}", "error")

    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    gesmed.run(port=3000, debug=True)