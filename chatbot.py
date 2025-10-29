from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os
import logging

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
CORS(app)

openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    logging.warning("OPENAI_API_KEY no encontrada. ")

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

if __name__ == "__main__":
    app.run(debug=True, port=5001)
