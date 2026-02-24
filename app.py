from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import time  # <--- Añadido para romper el caché

app = Flask(__name__)
# Ajuste de CORS para permitir la conexión desde tu tienda en GitHub Pages
CORS(app, resources={r"/*": {"origins": "*"}})

# 1. TU NUEVA URL DE GOOGLE APPS SCRIPT (Actualizada)
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwN-y6WGRGDy-LxHU9ix_tqNwrtc781lTEXt-KTDDr8_IFC9l6S2osWaEM5emHDul3R/exec"

@app.route('/')
def home():
    return "Bot de Axtelix: ¡Estoy vivo y trabajando! 🚀"

@app.route('/obtener-inventario', methods=['GET'])
def obtener_inventario():
    try:
        # Añadimos un número único (timestamp) al final de la URL 
        # Esto obliga a Google a darnos los datos frescos del Excel
        url_final = f"{GOOGLE_SCRIPT_URL}?t={int(time.time())}"
        
        # Pedimos los datos a Google Sheets
        respuesta = requests.get(url_final, timeout=10)
        datos = respuesta.json()
        
        # Si Google nos manda la lista dentro de una llave llamada "productos", la extraemos
        if isinstance(datos, dict) and "productos" in datos:
            return jsonify(datos["productos"])
        return jsonify(datos)
        
    except Exception as e:
        print(f"Error: {e}")
        # Si falla, mandamos una lista vacía para que el HTML use su 'RESPALDO'
        return jsonify([])

@app.route('/validar-cupon', methods=['POST'])
def validar_cupon():
    try:
        datos_cliente = request.json
        # Le enviamos el código del cupón a Google para que lo cheque
        respuesta = requests.post(GOOGLE_SCRIPT_URL, json=datos_cliente, timeout=10)
        return jsonify(respuesta.json())
        
    except Exception as e:
        print(f"Error en cupones: {e}")
        return jsonify({"valido": False, "mensaje": "Servidor ocupado, intenta en 30 segundos"})

if __name__ == '__main__':
    # Render usa el puerto que él quiera, por eso usamos os.environ.get
    puerto = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=puerto)