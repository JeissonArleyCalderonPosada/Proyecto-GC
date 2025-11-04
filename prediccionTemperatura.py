import pandas as pd
import joblib
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestRegressor
import re

# ========================
# CARGAR Y ENTRENAR MODELO
# ========================
df = pd.read_excel("dataset_bebidas_enfriamiento.xlsx")

X = df[["Tipo de bebida", "Temperatura inicial (°C)", "Temperatura ambiente (°C)"]]
y = df["Tiempo estimado para alcanzar temperatura fría (min)"]

encoder = LabelEncoder()
X["Tipo de bebida"] = encoder.fit_transform(X["Tipo de bebida"])

modelo = RandomForestRegressor(n_estimators=200, random_state=42)
modelo.fit(X, y)

print("✅ Modelo de predicción cargado correctamente.")

# ========================
# FUNCIÓN DE PREDICCIÓN
# ========================
def predecir_tiempo(mensaje_usuario: str) -> str:
    """
    Recibe un mensaje como:
    'Tengo una cerveza a 30 grados y el ambiente está a 20'
    y devuelve el tiempo estimado de enfriamiento.
    """
    mensaje = mensaje_usuario.lower()

    # Detectar bebida
    bebidas = list(encoder.classes_)
    bebida = next((b for b in bebidas if b.lower() in mensaje), None)

    # Buscar números en el texto
    nums = re.findall(r"\d+", mensaje)
    temps = [int(n) for n in nums]

    if not bebida or len(temps) < 2:
        return "Por favor, dime la bebida, su temperatura inicial y la temperatura ambiente. Ejemplo: 'Una cerveza a 25 grados con ambiente a 18'."

    temp_inicial = temps[0]
    temp_ambiente = temps[1]

    # Preparar entrada para el modelo
    entrada = [[encoder.transform([bebida])[0], temp_inicial, temp_ambiente]]
    prediccion = modelo.predict(entrada)[0]

    return f"Tu {bebida} alcanzará temperatura fría en aproximadamente {prediccion:.1f} minutos."
