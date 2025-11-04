from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from prediccionTemperatura import predecir_tiempo
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import openai
import os
import logging

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
CORS(app)
app.secret_key = "clave_super_segura"

# Configuración de la base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = (
    "mssql+pyodbc://DESKTOP-PTOBCHL\\SQLEXPRESS/ml_project_aulaespejo?"
    "driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Configuración de OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    logging.warning("OPENAI_API_KEY no encontrada.")

# ===== MODELO DE USUARIO =====
class Usuario(db.Model):
    __tablename__ = 'Usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(512), nullable=False)

    def __repr__(self):
        return f'<Usuario {self.nombre}>'

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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
            flash('Datos incorrectos', 'error')
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
        password = request.form.get('password', '')

        if not nombre or not correo or not password:
            flash("Por favor completa todos los campos.", "error")
            return redirect(url_for('register'))

        if Usuario.query.filter_by(correo=correo).first():
            flash("El correo ya está registrado.", "error")
            return redirect(url_for('register'))

        password_hash = generate_password_hash(password)
        nuevo_usuario = Usuario(nombre=nombre, correo=correo, password_hash=password_hash)
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

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Eres ZiloyBot, asistente amable y profesional de la marca Ziloy."},
                {"role": "user", "content": user_message}
            ],
            max_tokens=500,
            temperature=0.6
        )
        bot_reply = response.choices[0].message.content.strip()
        return jsonify({"reply": bot_reply})
    except Exception as e:
        logging.exception("Error llamando a OpenAI")
        return jsonify({"error": "Error en servidor del chatbot"}), 500
    

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
