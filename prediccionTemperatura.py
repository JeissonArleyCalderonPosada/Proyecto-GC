import pandas as pd
import joblib
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestRegressor
import re

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

print("✅ Modelo de predicción cargado correctamente.")

# ========================
# VARIABLES DE CONVERSACIÓN
# ========================
estado_conversacion = {
    "etapa": None,
    "bebida": None,
    "temp_inicial": None,
    "temp_ambiente": None
}

# ========================
# FUNCIÓN DE PREDICCIÓN
# ========================
def predecir_tiempo(mensaje_usuario: str) -> str:
    """
    Guía al usuario paso a paso para obtener la predicción.
    """
    global estado_conversacion
    mensaje = mensaje_usuario.lower().strip()

    # Si es el primer mensaje o no hay etapa activa, inicia directamente
    if not mensaje or estado_conversacion["etapa"] is None:
        estado_conversacion["etapa"] = "bebida"
        return "¿Qué tipo de bebida deseas analizar? (ejemplo: café, té, cerveza...)"

    # Reiniciar si el usuario quiere hacer otra predicción
    if "otra" in mensaje or "nuevo" in mensaje or "reiniciar" in mensaje:
        estado_conversacion = {
            "etapa": "bebida",
            "bebida": None,
            "temp_inicial": None,
            "temp_ambiente": None
        }
        return "Perfecto, Empecemos de nuevo. ¿Qué bebida deseas analizar?"

    # Etapa 1: bebida
    if estado_conversacion["etapa"] == "bebida":
        bebidas = list(encoder.classes_)
        bebida = next((b for b in bebidas if b.lower() in mensaje), None)

        if not bebida:
            return f"No reconozco esa bebida. Prueba con una de estas: {', '.join(bebidas)}."

        estado_conversacion["bebida"] = bebida
        estado_conversacion["etapa"] = "temp_inicial"
        return f"Perfecto. ¿Cuál es la temperatura inicial de tu {bebida}? (en °C)"

    # Etapa 2: temperatura inicial
    if estado_conversacion["etapa"] == "temp_inicial":
        nums = re.findall(r"\d+", mensaje)
        if not nums:
            return "Por favor, indícame un número para la temperatura inicial en °C."
        estado_conversacion["temp_inicial"] = int(nums[0])
        estado_conversacion["etapa"] = "temp_ambiente"
        return "Gracias. Ahora, podrias revisar la temperatura ambiente en tu celular e indicarmela (en °C)."

    # Etapa 3: temperatura ambiente → calcular predicción
    if estado_conversacion["etapa"] == "temp_ambiente":
        nums = re.findall(r"\d+", mensaje)
        if not nums:
            return "Por favor, indícame un número para la temperatura ambiente en °C."

        estado_conversacion["temp_ambiente"] = int(nums[0])
        estado_conversacion["etapa"] = "resultado"

        bebida = estado_conversacion["bebida"]
        temp_inicial = estado_conversacion["temp_inicial"]
        temp_ambiente = estado_conversacion["temp_ambiente"]

        entrada = [[encoder.transform([bebida])[0], temp_inicial, temp_ambiente]]
        prediccion = modelo.predict(entrada)[0]

        estado_conversacion["etapa"] = "fin"

        return (
            f"Tu {bebida} alcanzará temperatura fría en aproximadamente {prediccion:.1f} minutos.\n\n"
            "¿Quieres hacer otra predicción? (escribe 'otra' o 'nuevo' para reiniciar)"
        )

    # Si ya terminó
    if estado_conversacion["etapa"] == "fin":
        return "¿Quieres hacer otra predicción? Escribe 'otra' o 'nuevo' para comenzar de nuevo."

    return "No entendí eso. Intenta escribiendo 'otra' para comenzar de nuevo."
