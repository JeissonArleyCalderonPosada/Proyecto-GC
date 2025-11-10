from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from prediccionTemperatura import predecir_tiempo
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import openai
import os
import logging
from preguntasFrecuentes import obtener_respuesta
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
CORS(app)
app.secret_key = "clave_super_segura"

#Configuracion de la base de datos
load_dotenv()  # carga las variables del archivo .env

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Configuración de OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    logging.warning("OPENAI_API_KEY no encontrada.")

# ===== MODELOS DE BASE DE DATOS =====
class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(120), unique=True, nullable=False)
    telefono = db.Column(db.String(20))  # pedidos vía WhatsApp
    password_hash = db.Column(db.String(512), nullable=False)

    pedidos = db.relationship('Pedido', backref='usuario', lazy=True)

    def __repr__(self):
        return f'<Usuario {self.nombre}>'

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Pedido(db.Model):
    __tablename__ = 'pedidos'
    id = db.Column(db.Integer, primary_key=True)
    producto = db.Column(db.String(100), nullable=False)
    metodo_pago = db.Column(db.String(50))
    direccion = db.Column(db.String(200))
    estado = db.Column(db.String(50), default="pendiente")

    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)

    def __repr__(self):
        return f'<Pedido {self.producto} - Estado: {self.estado}>'

# ===== RUTAS DE LA WEB =====
@app.route('/')
def index():
    return render_template('index.html', name='Ziloy')

@app.route('/conocenos')
def conocenos():
    return render_template('conocenos.html')

@app.route('/tiendavirtual')
def tienda_virtual():
    return render_template('tiendavirtual.html')

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
            flash('Datos incorrectos o usuario no encontrado.', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Sesión cerrada correctamente", "info")
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', user_name=session.get('user_name'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        correo = request.form.get('correo', '').strip().lower()
        password = request.form.get('password', '').strip()
        telefono = request.form.get('telefono', '').strip() if 'telefono' in request.form else None

        # Validar campos
        if not nombre or not correo or not password:
            flash("Por favor completa todos los campos.", "error")
            return redirect(url_for('register'))

        # Verificar si el correo ya existe
        if Usuario.query.filter_by(correo=correo).first():
            flash("El correo ya está registrado.", "error")
            return redirect(url_for('register'))

        # Crear usuario
        password_hash = generate_password_hash(password)
        nuevo_usuario = Usuario(
            nombre=nombre,
            correo=correo,
            telefono=telefono,
            password_hash=password_hash
        )
        db.session.add(nuevo_usuario)
        db.session.commit()

        flash("Registro exitoso. Ya puedes iniciar sesión.", "success")
        return redirect(url_for('login'))

    return render_template('registro.html')

# ===== RUTA DE CHATBOT =====
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    user_message = data.get("message", "")
    
    if not user_message:
        return jsonify({"error": "El mensaje está vacío"}), 400

    respuesta = obtener_respuesta(user_message)
    return jsonify({"reply": respuesta})

# ===== RUTA DE PREDICCIÓN =====
@app.route("/prediccion", methods=["POST"])
def prediccion():
    data = request.get_json()
    mensaje = data.get("message", "")
    try:
        resultado = predecir_tiempo(mensaje)
        return jsonify({"reply": resultado})
    except Exception as e:
        return jsonify({"reply": f"Ocurrió un error en la predicción: {str(e)}"})

# ===== INICIAR SERVIDOR =====
if __name__ == '__main__':
    app.run(debug=True, port=5000)
