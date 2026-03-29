from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import time

app = Flask(__name__)

# Configuración de CORS
CORS(app, resources={r"/*": {"origins": "*"}})

# --- BÚNKER DE SEGURIDAD ---
# Ya no hay URL real aquí. Python la buscará en la configuración de Render.
GOOGLE_SCRIPT_URL = os.environ.get("GOOGLE_SCRIPT_URL")

@app.route('/')
def home():
    return "Bot de Axtelix: ¡Sincronizado y búnker activado! 🛡️"

# --- RUTA 1: OBTENER INVENTARIO ---
@app.route('/obtener-inventario', methods=['GET'])
def obtener_inventario():
    if not GOOGLE_SCRIPT_URL:
        return jsonify({"error": "Configuración faltante"}), 500
    try:
        url_final = f"{GOOGLE_SCRIPT_URL}?t={int(time.time())}"
        respuesta = requests.get(url_final, timeout=10)
        datos = respuesta.json()
        
        if isinstance(datos, dict) and "productos" in datos:
            return jsonify(datos["productos"])
        return jsonify(datos)
        
    except Exception as e:
        print(f"Error al obtener inventario: {e}")
        return jsonify([])

# --- RUTA 2: VALIDAR CUPONES ---
@app.route('/validar-cupon', methods=['POST'])
def validar_cupon():
    if not GOOGLE_SCRIPT_URL:
        return jsonify({"error": "Configuración faltante"}), 500
    try:
        datos_cliente = request.json
        respuesta = requests.post(GOOGLE_SCRIPT_URL, json=datos_cliente, timeout=10)
        return jsonify(respuesta.json())
        
    except Exception as e:
        print(f"Error en validación de cupón: {e}")
        return jsonify({"valido": False, "mensaje": "Servidor fuera de línea"})

# --- RUTA 3: RESPALDO DE VENTAS ---
@app.route('/respaldo-preventa', methods=['POST'])
def respaldo_preventa():
    if not GOOGLE_SCRIPT_URL:
        return jsonify({"error": "Configuración faltante"}), 500
    try:
        datos_venta = request.json
        print(f"📦 Registro de preventa para: {datos_venta.get('nombre')}")
        respuesta = requests.post(GOOGLE_SCRIPT_URL, json=datos_venta, timeout=10)
        
        return jsonify({
            "status": "success", 
            "message": "Datos asegurados en la nube"
        }), 200
        
    except Exception as e:
        print(f"❌ Error al respaldar venta: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    puerto = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=puerto)