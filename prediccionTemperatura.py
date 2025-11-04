from flask import Flask, request, jsonify
import pandas as pd
import joblib
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestRegressor

app = Flask(__name__)

# ========================
# CARGAR Y ENTRENAR MODELO
# ========================
df = pd.read_excel("DatasetBebidasEnfriamiento.xlsx")

X = df[["Tipo de bebida", "Temperatura inicial (°C)", "Temperatura ambiente (°C)"]]
y = df["Tiempo estimado para alcanzar temperatura fría (min)"]

encoder = LabelEncoder()
X["Tipo de bebida"] = encoder.fit_transform(X["Tipo de bebida"])

modelo = RandomForestRegressor(n_estimators=200, random_state=42)
modelo.fit(X, y)

print("✅ Modelo cargado y listo para predecir.")

# ========================
# ENDPOINT /chat
# ========================
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    mensaje = data.get("message", "").lower()

    # Detectar datos dentro del mensaje (simplificado)
    bebidas = list(encoder.classes_)
    bebida = next((b for b in bebidas if b.lower() in mensaje), None)
    
    # Buscar valores numéricos en el texto
    import re
    nums = re.findall(r"\d+", mensaje)
    temps = [int(n) for n in nums]

    if not bebida or len(temps) < 2:
        return jsonify({"reply": "Por favor, dime la bebida, su temperatura inicial y la temperatura ambiente."})

    temp_inicial = temps[0]
    temp_ambiente = temps[1]

    # Preparar entrada para el modelo
    entrada = [[encoder.transform([bebida])[0], temp_inicial, temp_ambiente]]
    prediccion = modelo.predict(entrada)[0]

    respuesta = f"Tu {bebida} dejará de estar caliente en aproximadamente {prediccion:.1f} minutos."
    return jsonify({"reply": respuesta})

# ========================
# EJECUTAR SERVIDOR
# ========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)