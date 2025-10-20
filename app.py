from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "clave_super_segura"  # Necesaria para manejar sesiones

## CONFIGURACIÓN BASE DE DATOS
app.config['SQLALCHEMY_DATABASE_URI'] = (
    "mssql+pyodbc://DESKTOP-PTOBCHL\\SQLEXPRESS/ml_project_aulaespejo?"
    "driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


## CLASE USUARIOS CON SUS ATRIBUTOS 
class Usuario(db.Model):
    __tablename__ = 'Usuarios'  # Coincidencia con la tabla de SQL Server

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(512), nullable=False)

    def __repr__(self):
        return f'<Usuario {self.nombre}>'

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# Ruta principal (Index)
@app.route('/')
def index():
    return render_template('index.html', name='Flask Marketing App')


# Ruta para iniciar sesión (mGET y POST)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        usuario = Usuario.query.filter_by(correo=correo).first()

        if usuario and usuario.check_password(password):
            session['user_id'] = usuario.id
            session['user_name'] = usuario.nombre
            flash('Inicio de sesión exitoso', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Datos incorrectos', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')


# Ruta para cerrar sesión
@app.route('/logout')
def logout():
    session.clear()
    flash("Sesión cerrada correctamente", "info")
    return redirect(url_for('login'))


# Ruta del panel principal (Dashboard)
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', user_name=session.get('user_name'))

# Ruta para registrar nuevos usuarios
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        correo = request.form.get('correo', '').strip().lower()
        password = request.form.get('password', '')

        # Validaciones 
        if not nombre or not correo or not password:
            flash("Por favor completa todos los campos.", "error")
            return redirect(url_for('register'))

        # Verificar si ya existe el correo
        if Usuario.query.filter_by(correo=correo).first():
            flash("El correo ya está registrado.", "error")
            return redirect(url_for('register'))

        # Crear nuevo usuario con contraseña encriptada
        password_hash = generate_password_hash(password)
        nuevo_usuario = Usuario(nombre=nombre, correo=correo, password_hash=password_hash)

        # Guardar en la base de datos
        db.session.add(nuevo_usuario)
        db.session.commit()

        flash("Registro exitoso. Ya puedes iniciar sesión.", "success")
        return redirect(url_for('login'))

    return render_template('registro.html')


if __name__ == '__main__':
    app.run(debug=True)
