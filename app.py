from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import time

app = Flask(__name__)

# Configuración de CORS
CORS(app, resources={r"/*": {"origins": "*"}})

# --- BÚNKER DE SEGURIDAD (Caja Fuerte) ---
GOOGLE_SCRIPT_URL = os.environ.get("GOOGLE_SCRIPT_URL")
# Nuevas llaves secretas
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

@app.route('/')
def home():
    return "Bot de Axtelix: ¡Sincronizado y doble búnker activado (Google + Supabase)! 🛡️"

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

# --- RUTA 4: REGISTRAR VENTAS EN SUPABASE (¡NUEVO BLINDAJE!) ---
@app.route('/registrar-venta', methods=['POST'])
def registrar_venta():
    if not SUPABASE_URL or not SUPABASE_KEY:
        return jsonify({"error": "Configuración de Supabase faltante"}), 500
    try:
        datos_venta = request.json
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }
        
        # OJO AQUÍ: Estoy asumiendo que tu tabla en Supabase se llama "ventas"
        url_supabase = f"{SUPABASE_URL}/rest/v1/ventas" 
        
        respuesta = requests.post(url_supabase, json=datos_venta, headers=headers, timeout=10)
        
        if respuesta.status_code >= 400:
             return jsonify({"status": "error", "message": respuesta.text}), respuesta.status_code
             
        return jsonify({"status": "success", "mensaje": "Venta asegurada en Supabase"}), 200
        
    except Exception as e:
        print(f"❌ Error al registrar en Supabase: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# =========================================================
# --- RUTAS DE RESEÑAS (AXTELIX ENGINE) ---
# =========================================================

@app.route('/obtener-reviews', methods=['GET'])
def obtener_reviews():
    if not SUPABASE_URL or not SUPABASE_KEY:
        return jsonify({"error": "Configuración faltante"}), 500
    url = f"{SUPABASE_URL}/rest/v1/reviews?order=created_at.desc"
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        return jsonify(res.json()), res.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/guardar-review', methods=['POST'])
def guardar_review():
    url = f"{SUPABASE_URL}/rest/v1/reviews"
    headers = {
        "apikey": SUPABASE_KEY, 
        "Authorization": f"Bearer {SUPABASE_KEY}", 
        "Content-Type": "application/json", 
        "Prefer": "return=representation"
    }
    try:
        res = requests.post(url, headers=headers, json=request.json, timeout=10)
        return jsonify(res.json()), res.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/votar-review', methods=['POST'])
def votar_review():
    datos = request.json
    url = f"{SUPABASE_URL}/rest/v1/reviews?id=eq.{datos['id']}"
    headers = {
        "apikey": SUPABASE_KEY, 
        "Authorization": f"Bearer {SUPABASE_KEY}", 
        "Content-Type": "application/json"
    }
    try:
        res = requests.patch(url, headers=headers, json={datos['field']: datos['newValue']}, timeout=10)
        return jsonify({"status": "ok"}), res.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/borrar-review', methods=['POST'])
def borrar_review():
    datos = request.json
    url = f"{SUPABASE_URL}/rest/v1/reviews?id=eq.{datos['id']}"
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    try:
        res = requests.delete(url, headers=headers, timeout=10)
        return jsonify({"status": "ok"}), res.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =========================================================

if __name__ == '__main__':
    puerto = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=puerto)