from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    """Recibe mensajes de WhatsApp y responde automáticamente"""
    mensaje_usuario = request.form.get("Body", "").lower()
    respuesta = MessagingResponse()
    mensaje = respuesta.message()

    # === Lógica básica del chatbot ===
    if "hola" in mensaje_usuario:
        mensaje.body("👋 ¡Hola! Soy el asistente de Ziloy. ¿Quieres hacer una compra?")
    elif "comprar" in mensaje_usuario:
        mensaje.body("Perfecto 😄. ¿Qué producto deseas comprar?")
    elif "gracias" in mensaje_usuario:
        mensaje.body("¡Con gusto! 😊 Si deseas más ayuda, solo escríbeme de nuevo.")
    else:
        mensaje.body("No entendí muy bien 😅. Escribe 'hola' para comenzar o 'comprar' para iniciar tu pedido.")

    return str(respuesta)

if __name__ == "__main__":
    app.run(debug=True, port=5001)
