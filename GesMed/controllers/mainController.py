from flask import (
    Blueprint,
    request,
    render_template,
    redirect,
    url_for,
    flash,
    session,
    Response,
)
from io import BytesIO
from datetime import datetime, date
from xhtml2pdf import pisa

from models.mainModel import (
    get_user_by_rfc,
    get_dashboard_data,
    get_index_data,
    insert_medico,
    insert_paciente,
    insert_cita,
    get_paciente_nombre,
    get_medico_nombre,
    update_cita_pdf,
    insert_receta,
    get_pdf_receta,
    deactivate_cita,
    get_active_medicos,
    delete_medico,
    delete_paciente,
    update_medico,
    update_paciente,
)


mainBP = Blueprint('main', __name__)


@mainBP.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        rfc = request.form.get('rfc', '').strip()
        password = request.form.get('password', '').strip()
        if not rfc or not password:
            flash('Es necesario llenar todos los campos en rojo', 'error')
            return render_template('login.html')
        user = get_user_by_rfc(rfc)
        if user:
            stored_password = user[4]
            if password == stored_password:
                session['user_id'] = user[0]
                session['nombre_medico'] = f"Dr. {user[1]} {user[2]} {user[3]}"
                session['rol'] = user[5]
                flash('¡Login exitoso!', 'success')
                if user[5] == 'admin':
                    return redirect(url_for('main.dashboard'))
                elif user[5] == 'medico':
                    return redirect(url_for('main.index'))
                else:
                    return redirect(url_for('main.login'))
            else:
                flash('Contraseña incorrecta', 'error')
        else:
            flash('Usuario no encontrado', 'error')
    return render_template('login.html')


@mainBP.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    data = get_dashboard_data()
    citas = [
        dict(
            zip(
                [
                    'ID_Cita',
                    'Nombre_Paciente',
                    'AP_Paciente',
                    'AM_Paciente',
                    'Fecha',
                    'Nombre_Medico',
                    'AP_Medico',
                    'AM_Medico',
                ],
                cita,
            )
        )
        for cita in data['citas']
    ]
    return render_template(
        'dashboard.html',
        nombre_medico=session.get('nombre_medico'),
        rol=session.get('rol'),
        user_id=session.get('user_id'),
        total_medicos=data['total_medicos'],
        total_admins=data['total_admins'],
        total_pacientes=data['total_pacientes'],
        medicos=data['medicos'],
        pacientes=data['pacientes'],
        citas=citas,
    )


@mainBP.route('/index')
def index():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    id_medico = session['user_id']
    pacientes, citas = get_index_data(id_medico)
    citas = [
        dict(
            zip(
                [
                    'ID_Cita',
                    'Nombre_Paciente',
                    'AP_Paciente',
                    'AM_Paciente',
                    'Fecha',
                    'Nombre_Medico',
                    'AP_Medico',
                    'AM_Medico',
                ],
                cita,
            )
        )
        for cita in citas
    ]
    total_pacientes = len(pacientes)
    return render_template(
        'index.html',
        nombre_medico=session.get('nombre_medico'),
        rol=session.get('rol'),
        user_id=id_medico,
        pacientes=pacientes,
        citas=citas,
        total_pacientes=total_pacientes,
    )


@mainBP.route('/agregar_medico', methods=['POST'])
def agregar_medico():
    if 'user_id' not in session or session.get('rol') != 'admin':
        flash('No tienes permisos para agregar médicos.', 'error')
        return redirect(url_for('main.dashboard'))
    nombre = request.form.get('nombre', '').strip()
    apellido_paterno = request.form.get('apellido_paterno', '').strip()
    apellido_materno = request.form.get('apellido_materno', '').strip()
    cedula = request.form.get('cedula', '').strip()
    correo = request.form.get('correo', '').strip()
    contrasena = request.form.get('contrasena', '').strip()
    verif_contrasena = request.form.get('verif_contrasena', '').strip()
    rfc = request.form.get('rfc', '').strip()
    rol = request.form.get('rol', '').strip()
    if not all([nombre, apellido_paterno, apellido_materno, cedula, correo, contrasena, verif_contrasena, rfc, rol]):
        flash('Es necesario llenar todos los campos en rojo', 'error')
        return redirect(url_for('main.dashboard'))
    if contrasena != verif_contrasena:
        flash('Las contraseñas no coinciden.', 'error')
        return redirect(url_for('main.dashboard'))
    try:
        insert_medico(rfc, nombre, apellido_paterno, apellido_materno, cedula, correo, contrasena, rol)
        flash('Médico agregado correctamente.', 'success')
    except Exception as e:
        flash(f'Error al agregar médico: {str(e)}', 'error')
    return redirect(url_for('main.dashboard'))


@mainBP.route('/agregar_paciente', methods=['POST'])
def agregar_paciente():
    if 'user_id' not in session:
        flash('Debes iniciar sesión para registrar pacientes.', 'error')
        return redirect(url_for('main.login'))
    nombre_medico = request.form.get('medico_nombre')
    nombre = request.form.get('nombre', '').strip()
    apellido_paterno = request.form.get('apellido_paterno', '').strip()
    apellido_materno = request.form.get('apellido_materno', '').strip()
    fecha_nacimiento = request.form.get('fecha_nacimiento', '').strip()
    alergias = request.form.get('alergias')
    antecedentes = request.form.get('antecedentes_familiares')
    enfermedades = request.form.get('enfermedades_cronicas')
    id_medico = session.get('user_id')
    if not all([nombre, apellido_paterno, apellido_materno, fecha_nacimiento]):
        flash('Es necesario llenar todos los campos en rojo', 'error')
        return redirect(url_for('main.dashboard'))
    try:
        fecha_nac_dt = datetime.strptime(fecha_nacimiento, '%Y-%m-%d').date()
        if fecha_nac_dt >= date.today():
            flash('No se pueden registrar pacientes recién nacidos.', 'error')
            return redirect(url_for('main.dashboard'))
    except ValueError:
        flash('Fecha de nacimiento inválida.', 'error')
        return redirect(url_for('main.dashboard'))
    try:
        insert_paciente(
            id_medico,
            nombre,
            apellido_paterno,
            apellido_materno,
            fecha_nacimiento,
            enfermedades,
            alergias,
            antecedentes,
        )
        flash('Paciente registrado correctamente.', 'success')
    except Exception as e:
        flash(f'Error al registrar paciente: {str(e)}', 'error')
    return redirect(url_for('main.dashboard'))


@mainBP.route('/agregar_cita', methods=['POST'])
def agregar_cita():
    try:
        id_paciente = request.form['id_paciente']
        id_medico = request.form['id_medico']
        fecha = request.form['fecha']

        def to_decimal(value, campo):
            return float(value)

        def to_int(value, campo):
            return int(value)

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
        if not fecha:
            raise ValueError("El campo 'fecha' es obligatorio.")
        id_cita = insert_cita(
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
        )
        nombre_paciente = get_paciente_nombre(id_paciente)
        nombre_medico = get_medico_nombre(id_medico)
        pdf_buffer = BytesIO()
        html = render_template(
            'pdf_receta.html',
            fecha=fecha,
            sintomas=sintomas,
            diagnostico=diagnostico,
            tratamiento=tratamiento,
            nombre_paciente=nombre_paciente,
            nombre_medico=nombre_medico,
        )
        status = pisa.CreatePDF(html, dest=pdf_buffer)
        if status.err:
            flash('No se pudo generar el PDF', 'danger')
            return redirect(url_for('main.dashboard'))
        update_cita_pdf(id_cita, pdf_buffer.getvalue())
        insert_receta(id_cita, id_medico)
        flash('Cita registrada y receta generada correctamente', 'success')
        return redirect(url_for('main.dashboard'))
    except Exception as e:
        flash(f'Error al registrar la cita: {str(e)}', 'danger')
        return redirect(url_for('main.dashboard'))


@mainBP.route('/cita/pdf/<int:id>')
def ver_pdf(id):
    resultado = get_pdf_receta(id)
    if resultado and resultado[0]:
        return Response(resultado[0], mimetype='application/pdf')
    else:
        return 'PDF no encontrado', 404


@mainBP.route('/eliminar_cita/<int:id>', methods=['POST'])
def eliminar_cita(id):
    try:
        deactivate_cita(id)
        flash('Cita eliminada correctamente.', 'success')
    except Exception:
        flash('Error al eliminar la cita.', 'danger')
    return redirect(url_for('main.dashboard'))


@mainBP.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada exitosamente', 'info')
    return redirect(url_for('main.login'))


@mainBP.route('/medicos')
def listar_medicos():
    if 'user_id' not in session or session.get('rol') != 'admin':
        return redirect(url_for('main.login'))
    medicos = get_active_medicos()
    return render_template('medicos.html', medicos=medicos)


@mainBP.route('/eliminar_medico/<int:id>', methods=['POST'])
def eliminar_medico(id):
    if 'user_id' not in session or session.get('rol') != 'admin':
        flash('No tienes permisos para eliminar médicos.', 'error')
        return redirect(url_for('main.dashboard'))
    try:
        delete_medico(id)
        flash('Médico y datos relacionados eliminados correctamente.', 'success')
    except Exception as e:
        flash(f'Error al eliminar médico: {str(e)}', 'error')
    return redirect(url_for('main.dashboard'))


@mainBP.route('/eliminar_paciente/<int:id>', methods=['POST'])
def eliminar_paciente(id):
    if 'user_id' not in session:
        flash('Debes iniciar sesión para eliminar pacientes.', 'error')
        return redirect(url_for('main.login'))
    try:
        delete_paciente(id)
        flash('Paciente y citas relacionadas eliminadas correctamente.', 'success')
    except Exception as e:
        flash(f'Error al eliminar paciente: {str(e)}', 'error')
    return redirect(url_for('main.dashboard'))


@mainBP.route('/actualizar_medico/<int:id>', methods=['POST'])
def actualizar_medico(id):
    if 'user_id' not in session or session.get('rol') != 'admin':
        flash('No tienes permisos para actualizar médicos.', 'error')
        return redirect(url_for('main.dashboard'))
    nombre = request.form.get('nombre')
    apellido_paterno = request.form.get('apellido_paterno')
    apellido_materno = request.form.get('apellido_materno')
    rfc = request.form.get('rfc')
    cedula = request.form.get('cedula')
    correo = request.form.get('correo')
    rol = request.form.get('rol')
    try:
        update_medico(id, nombre, apellido_paterno, apellido_materno, rfc, cedula, correo, rol)
        flash('Médico actualizado correctamente.', 'success')
    except Exception as e:
        flash(f'Error al actualizar médico: {str(e)}', 'error')
    return redirect(url_for('main.dashboard'))


@mainBP.route('/actualizar_paciente/<int:id>', methods=['POST'])
def actualizar_paciente(id):
    try:
        nombre = request.form['nombre']
        ap_paterno = request.form['apellido_paterno']
        ap_materno = request.form['apellido_materno']
        fecha_nacimiento = request.form['fecha_nacimiento']
        enfermedades_cronicas = request.form['enfermedades_cronicas']
        alergias = request.form['alergias']
        antecedentes = request.form['antecedentes_familiares']
        update_paciente(
            id,
            nombre,
            ap_paterno,
            ap_materno,
            fecha_nacimiento,
            enfermedades_cronicas,
            alergias,
            antecedentes,
        )
        flash('Paciente actualizado correctamente', 'success')
    except Exception as e:
        flash(f'Error al actualizar paciente: {e}', 'error')
    return redirect(url_for('main.dashboard'))
