from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "clave_super_segura"  # Necesaria para manejar sesiones

## CONFIGURACION BASE DE DATOS
app.config['SQLALCHEMY_DATABASE_URI'] = (
    "mssql+pyodbc://DESKTOP-PTOBCHL\\SQLEXPRESS/ml_project_aulaespejo?"
    "driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

## CLASE USUARIOS CON SUS ATRIBUTOS 
class Usuario(db.Model):
    __tablename__ = 'Usuarios'  # Asegura coincidencia con la tabla de SQL Server

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


# Ruta para mostrar el login (GET)
@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html')


# Ruta para procesar el login (POST)
@app.route('/login', methods=['POST'])
def login_post():
    correo = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')

    user = Usuario.query.filter_by(correo=correo).first()

    if not user or not user.check_password(password):
        flash("❌ Correo o contraseña incorrectos", "error")
        return redirect(url_for('login'))

    session['user_id'] = user.id
    session['user_name'] = user.nombre
    flash("✅ Sesión iniciada correctamente", "success")
    return redirect(url_for('index'))


# Ruta para cerrar sesión
@app.route('/logout')
def logout():
    session.clear()
    flash("Sesión cerrada correctamente", "info")
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
