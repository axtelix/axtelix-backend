from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import time

app = Flask(__name__)

# Configuración de CORS: Permite que tu tienda en GitHub Pages se comunique con Render
CORS(app, resources={r"/*": {"origins": "*"}})

# URL de tu Google Apps Script (Sincronizada con tu Inventario, Cupones y Ventas)
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwN-y6WGRGDy-LxHU9ix_tqNwrtc781lTEXt-KTDDr8_IFC9l6S2osWaEM5emHDul3R/exec"

@app.route('/')
def home():
    return "Bot de Axtelix: ¡Sincronizado y listo para vender! 🚀"

# --- RUTA 1: OBTENER INVENTARIO ACTUALIZADO ---
@app.route('/obtener-inventario', methods=['GET'])
def obtener_inventario():
    try:
        # Añadimos un timestamp para romper el caché de Google y tener datos frescos
        url_final = f"{GOOGLE_SCRIPT_URL}?t={int(time.time())}"
        respuesta = requests.get(url_final, timeout=10)
        datos = respuesta.json()
        
        # Si los datos vienen dentro de una llave 'productos', los extraemos, si no, mandamos la lista
        if isinstance(datos, dict) and "productos" in datos:
            return jsonify(datos["productos"])
        return jsonify(datos)
        
    except Exception as e:
        print(f"Error al obtener inventario: {e}")
        return jsonify([])

# --- RUTA 2: VALIDAR CUPONES DE DESCUENTO ---
@app.route('/validar-cupon', methods=['POST'])
def validar_cupon():
    try:
        datos_cliente = request.json
        # Enviamos el código a Google para verificar si existe y tiene stock
        respuesta = requests.post(GOOGLE_SCRIPT_URL, json=datos_cliente, timeout=10)
        return jsonify(respuesta.json())
        
    except Exception as e:
        print(f"Error en validación de cupón: {e}")
        return jsonify({"valido": False, "mensaje": "Servidor de cupones fuera de línea"})

# --- RUTA 3: RESPALDO AUTOMÁTICO DE VENTAS (PREVENTA) ---
@app.route('/respaldo-preventa', methods=['POST'])
def respaldo_preventa():
    """
    Recibe los datos del cliente (nombre, dirección, total) en cuanto da clic en 'Continuar'.
    Esto asegura la información en tu Google Sheets aunque no manden el WhatsApp.
    """
    try:
        datos_venta = request.json
        print(f"📦 Intento de compra registrado para: {datos_venta.get('nombre')}")
        
        # Reenviamos el JSON a Google Apps Script para que lo anote en 'VENTAS_LOG'
        respuesta = requests.post(GOOGLE_SCRIPT_URL, json=datos_venta, timeout=10)
        
        return jsonify({
            "status": "success", 
            "message": "Datos de preventa guardados en la nube"
        }), 200
        
    except Exception as e:
        print(f"❌ Error al respaldar venta: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # Render usa variables de entorno para el puerto, esto es obligatorio para que funcione en la nube
    puerto = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=puerto)