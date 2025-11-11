from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from prediccionTemperatura import predecir_tiempo
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import openai
import os
import logging
from flask import session
from functools import wraps
from preguntasFrecuentes import obtener_respuesta
from dotenv import load_dotenv
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask_mail import Message, Mail

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
CORS(app)
app.secret_key = "clave_super_segura"

#Configuracion de la base de datos
load_dotenv()  # carga las variables del archivo .env

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Configuración de correo con las variables del entorno
app.config['MAIL_SERVER'] = os.getenv("SMTP_HOST")
app.config['MAIL_PORT'] = int(os.getenv("SMTP_PORT", 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv("ADMIN_SMTP_USER")
app.config['MAIL_PASSWORD'] = os.getenv("ADMIN_SMTP_PASS")
app.config['MAIL_DEFAULT_SENDER'] = os.getenv("ADMIN_EMAIL")

mail = Mail(app)

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
    is_admin = db.Column(db.Boolean, default=False)

    pedidos = db.relationship('Pedido', backref='cliente', lazy=True)

    def __repr__(self):
        return f'<Usuario {self.nombre}>'

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Pedido(db.Model):
    __tablename__ = 'pedidos'
    id = db.Column(db.Integer, primary_key=True)
    nombre_cliente = db.Column(db.String(100))
    telefono = db.Column(db.String(20))
    color = db.Column(db.String(50), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_total = db.Column(db.Float, nullable=False)
    metodo_pago = db.Column(db.String(50))
    direccion = db.Column(db.String(200))
    estado = db.Column(db.String(50), default="pendiente")

    # Relación con usuarios
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)

    def __repr__(self):
        return f'<Pedido Usuario:{self.usuario_id} - Estado:{self.estado}>'

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
            session['is_admin'] = usuario.is_admin
            flash('Inicio de sesión exitoso', 'success')

            if usuario.is_admin:
                return redirect(url_for('admin_dashboard'))  # Panel admin 
            else:
                return redirect(url_for('index'))        # Usuario normal

        else:
            flash('Datos incorrectos o usuario no encontrado.', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Sesión cerrada correctamente", "info")
    return redirect(url_for('login'))

@app.route('/admin')
def admin_home():
    if not session.get('is_admin'):
        flash("Acceso denegado. No tienes permisos de administrador.", "error")
        return redirect(url_for('login'))

    pedidos = Pedido.query.order_by(Pedido.id.desc()).all()
    return render_template('admin_dashboard.html', pedidos=pedidos)

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


def enviar_confirmacion_whatsapp(telefono, nombre_cliente):
    """Envía un mensaje de confirmación al cliente vía WhatsApp usando Twilio."""
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    whatsapp_from = os.getenv("TWILIO_WHATSAPP_FROM")

    if not (account_sid and auth_token and whatsapp_from):
        logging.error("Faltan credenciales de Twilio en el .env")
        return

    client = Client(account_sid, auth_token)
    mensaje = f"✅ Hola {nombre_cliente}, tu pedido ha sido confirmado y está en camino."
    try:
        client.messages.create(
            body=mensaje,
            from_=whatsapp_from,
            to=f"whatsapp:{telefono}"
        )
        logging.info(f"Mensaje WhatsApp enviado a {telefono}")
    except Exception as e:
        logging.error(f"Error al enviar mensaje WhatsApp: {e}")

@app.route('/confirmar/<int:pedido_id>')
def confirmar_pedido(pedido_id):
    if not session.get('is_admin'):
        flash("No tienes permisos para confirmar pedidos.", "error")
        return redirect(url_for('dashboard'))

    pedido = Pedido.query.get(pedido_id)
    if pedido:
        pedido.estado = "confirmado"
        db.session.commit()
        flash(f"Pedido #{pedido.id} confirmado exitosamente.", "success")

        # Enviar mensaje de WhatsApp
        enviar_confirmacion_whatsapp(pedido.telefono, pedido.nombre_cliente)
    else:
        flash("Pedido no encontrado.", "error")

    return redirect(url_for('admin_dashboard'))

def enviar_correo_admin(asunto, cuerpo):
    """Envía un correo a la dueña del negocio notificando un nuevo pedido."""
    remitente = os.getenv("EMAIL_USER")
    destinatario = os.getenv("EMAIL_ADMIN")  # correo de la administradora
    password = os.getenv("EMAIL_PASS")

    if not (remitente and destinatario and password):
        logging.error("Faltan credenciales de correo en el .env")
        return

    msg = MIMEMultipart()
    msg["From"] = remitente
    msg["To"] = destinatario
    msg["Subject"] = asunto
    msg.attach(MIMEText(cuerpo, "plain", "utf-8"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(remitente, password)
            server.send_message(msg)
            logging.info("Correo enviado exitosamente a la dueña.")
    except Exception as e:
        logging.error(f"Error al enviar correo: {e}")

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
    
# ===== RUTA CHATBOT WHATSAPP =====
@app.route("/whatsapp", methods=["POST"])
def whatsapp_bot():
    from flask import request
    mensaje_usuario = request.form.get('Body', '').strip().lower()
    numero_usuario = request.form.get('From', '').replace('whatsapp:', '')

    resp = MessagingResponse()
    msg = resp.message()

    # Buscar usuario en base de datos (aquí puedes asociarlo luego por número)
    usuario = Usuario.query.filter_by(correo='cliente@ejemplo.com').first()
    if not usuario:
        msg.body("⚠️ No estás registrado en Ziloy. Por favor regístrate primero en la web para poder hacer pedidos.")
        return str(resp)

    pedido = Pedido.query.filter_by(telefono=numero_usuario, estado="pendiente").first()

    # Mensaje inicial
    if "hola" in mensaje_usuario:
        msg.body(f"👋 ¡Hola {usuario.nombre}! Soy el asistente virtual de *Ziloy* 👜.\n\nCada bolsa tiene un valor de *18 dólares*.\n\n¿Deseas el color *negro* o *rosado*?")
    
    # Nuevo pedido si no existe
    elif not pedido:
        nuevo_pedido = Pedido(
            nombre_cliente=usuario.nombre,
            telefono=numero_usuario,
            usuario_id=usuario.id
        )
        db.session.add(nuevo_pedido)
        db.session.commit()
        msg.body("Empecemos 🛍️ ¿Qué color prefieres para tu bolsa térmica? (Negro o Rosado)")

    # Escoger color
    elif pedido and not pedido.color:
        if mensaje_usuario in ["negro", "rosado"]:
            pedido.color = mensaje_usuario.title()
            db.session.commit()
            msg.body("Perfecto 🎨 ¿Cuántas unidades deseas?")
        else:
            msg.body("Solo tenemos disponibles en *Negro* o *Rosado*. Por favor elige uno de esos colores.")

    # Escoger cantidad
    elif pedido and pedido.color and not pedido.cantidad:
        try:
            cantidad = int(mensaje_usuario)
            pedido.cantidad = cantidad
            pedido.precio_total = cantidad * 18
            db.session.commit()
            msg.body("¿Cuál será tu método de pago? (Transferencia o Efectivo)")
        except ValueError:
            msg.body("Por favor ingresa un número válido para la cantidad.")

    # Escoger método de pago
    elif pedido and not pedido.metodo_pago:
        if "transferencia" in mensaje_usuario:
            pedido.metodo_pago = "Transferencia"
            db.session.commit()
            msg.body(
                "Perfecto, realiza la consignación a esta cuenta:\n\n"
                "*Banco Pichincha*\n"
                "Cuenta de ahorro transaccional\n"
                "Número: *2204633778*\n"
                "A nombre de: *Ángela Magali Camacho Yaguana*\n\n"
                "Cuando completes el pago, envíame tu *dirección de entrega*. 🚚"
            )
        elif "efectivo" in mensaje_usuario:
            pedido.metodo_pago = "Efectivo"
            db.session.commit()
            msg.body(
                "Perfecto. Puedes pagar el total en efectivo.\n\n"
                "Por favor, envíame tu *dirección de entrega* o especifica si deseas recoger de forma *presencial*."
            )
        else:
            msg.body("Métodos aceptados: *Transferencia* o *Efectivo*. Por favor selecciona uno de ellos.")

    # Dirección (domicilio o presencial)
    elif pedido and not pedido.direccion:
        if "presencial" in mensaje_usuario:
            pedido.direccion = "Presencial - Afuera de la Universidad Nacional de Loja, Av. Pío Jaramillo Alvarado y Reinaldo Espinosa​ Loja, Ecuador"
            pedido.precio_total += 0  # Sin envío
            db.session.commit()
            msg.body(
                "Perfecto, puedes recoger tu pedido en:\n"
                "*Afuera de la Universidad Nacional de Loja*\n"
                "Av. Pío Jaramillo Alvarado y Reinaldo Espinosa, Loja, Ecuador.\n\n"
                "¡Gracias! Tu pedido ha sido registrado y está pendiente de confirmación."
            )

        elif "ecuador" in mensaje_usuario or "domicilio" in mensaje_usuario:
            pedido.direccion = "Domicilio en Ecuador (pendiente de confirmar ubicación exacta)"
            pedido.precio_total += 6  # envío adicional por Servientrega
            db.session.commit()
            msg.body(
                "🚚 Perfecto, realizaremos el envío por *Servientrega* (+6 USD de envío).\n"
                "Por favor confirma la provincia y dirección exacta dentro de Ecuador."
            )

        else:
            msg.body("❌ Por ahora solo realizamos envíos dentro del *territorio nacional de Ecuador*. Si estás en otro país, aún no contamos con cobertura internacional.")

    # Cierre del pedido
    elif pedido and pedido.direccion:
        msg.body("✅ Gracias, tu pedido ya fue registrado completamente. En breve recibirás confirmación por WhatsApp y correo electrónico.")

        # Enviar correo a admin con el pedido
        cuerpo = f"""
        Nuevo pedido recibido:

        Cliente: {pedido.nombre_cliente}
        Teléfono: {pedido.telefono}
        Color: {pedido.color}
        Cantidad: {pedido.cantidad}
        Precio total (USD): {pedido.precio_total}
        Método de pago: {pedido.metodo_pago}
        Dirección: {pedido.direccion}
        """
        enviar_correo_admin("Nuevo pedido recibido en Ziloy", cuerpo)

    else:
        msg.body("No logré entenderte 😅. Por favor empieza diciendo *Hola* para hacer un nuevo pedido.")

    return str(resp)

@app.route('/admin')
def admin_dashboard():
    if not session.get('is_admin'):
        flash("Acceso restringido. Solo la administradora puede ver esto.", "danger")
        return redirect(url_for('index'))

    pedidos = Pedido.query.order_by(Pedido.id.desc()).all()
    return render_template('admin_dashboard.html', pedidos=pedidos)

def enviar_correo_nuevo_pedido(pedido):
    try:
        msg = Message(
            subject="Nuevo pedido recibido - Ziloy",
            recipients=[os.getenv("ADMIN_EMAIL")],
            body=f"""
¡Hola!

Se ha recibido un nuevo pedido en Ziloy.

Detalles del pedido:
- Cliente: {pedido.cliente.nombre}
- Teléfono: {pedido.cliente.telefono}
- Color: {pedido.color}
- Cantidad: {pedido.cantidad}
- Método de pago: {pedido.metodo_pago}
- Dirección: {pedido.direccion}
- Estado: {pedido.estado}

📍 Ingresa al panel de administración para revisarlo.
"""
        )
        mail.send(msg)
        print("Correo enviado al admin correctamente.")
    except Exception as e:
        print("Error al enviar el correo:", e)

# ===== RUTAS DE ACCIÓN ADMIN =====
@app.route('/rechazar/<int:pedido_id>')
def rechazar_pedido(pedido_id):
    if not session.get('is_admin'):
        flash("No tienes permisos para realizar esta acción.", "error")
        return redirect(url_for('login'))

    pedido = Pedido.query.get(pedido_id)
    if pedido:
        pedido.estado = "rechazado"
        db.session.commit()
        flash(f"Pedido #{pedido.id} rechazado.", "warning")

        # Avisar por WhatsApp al cliente
        try:
            client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
            client.messages.create(
                body=f"❌ Hola {pedido.nombre_cliente}, tu pedido ha sido rechazado. Revisa los datos de la transferencia e inténtalo nuevamente.",
                from_=os.getenv("TWILIO_WHATSAPP_FROM"),
                to=f"whatsapp:{pedido.telefono}"
            )
        except Exception as e:
            logging.error(f"Error al avisar rechazo vía WhatsApp: {e}")
    else:
        flash("Pedido no encontrado.", "error")

    return redirect(url_for('admin_dashboard'))


@app.route('/entregar/<int:pedido_id>')
def entregar_pedido(pedido_id):
    if not session.get('is_admin'):
        flash("No tienes permisos para marcar entregas.", "error")
        return redirect(url_for('login'))

    pedido = Pedido.query.get(pedido_id)
    if pedido:
        pedido.estado = "entregado"
        db.session.commit()
        flash(f"Pedido #{pedido.id} marcado como entregado.", "success")

        # Notificar al cliente por WhatsApp
        try:
            client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
            client.messages.create(
                body=f"¡Hola {pedido.nombre_cliente}! Tu pedido ha sido *entregado exitosamente*. 🎉 Gracias por confiar en Ziloy 👜",
                from_=os.getenv("TWILIO_WHATSAPP_FROM"),
                to=f"whatsapp:{pedido.telefono}"
            )
        except Exception as e:
            logging.error(f"Error al avisar entrega vía WhatsApp: {e}")
    else:
        flash("Pedido no encontrado.", "error")

    return redirect(url_for('admin_dashboard'))
# ===== INICIAR SERVIDOR =====
if __name__ == '__main__':
    app.run(debug=True, port=5000)
