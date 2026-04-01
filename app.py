from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import time
import google.generativeai as genai  # <-- LIBRERÍA DE IA

app = Flask(__name__)

# Configuración de CORS
CORS(app, resources={r"/*": {"origins": "*"}})

# --- BÚNKER DE SEGURIDAD (Variables de Entorno) ---
GOOGLE_SCRIPT_URL = os.environ.get("GOOGLE_SCRIPT_URL")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY") # <-- LLAVE DE GEMINI

# Inicializamos el Cerebro de la IA
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None

@app.route('/')
def home():
    return "Bot de Axtelix: ¡Sincronizado, doble búnker activado y Cerebro IA en línea! 🛡️🧠"


# =========================================================
# --- RUTAS DEL AGENTE IA Y WHATSAPP (NUEVO MOTOR) ---
# =========================================================

@app.route('/webhook-whatsapp', methods=['POST'])
def webhook_whatsapp():
    if not model:
        return jsonify({"error": "Falta GOOGLE_API_KEY en el servidor"}), 500
        
    try:
        datos = request.json
        mensaje_cliente = datos.get("mensaje", "")
        numero_cliente = datos.get("numero", "Desconocido")
        
        headers_supa = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        }

        # 1. Obtener inventario actual desde Supabase para que la IA lo lea
        url_productos = f"{SUPABASE_URL}/rest/v1/productos?select=*"
        res_prod = requests.get(url_productos, headers=headers_supa, timeout=10)
        inventario = res_prod.json() if res_prod.status_code == 200 else []

        # 2. El Prompt Maestro (El alma del vendedor)
        prompt = f"""
        Eres el vendedor estrella de Axtelix. Tienes un estilo pro, amable y mezclas un poquito de inglés.
        Aquí está tu inventario actual en tiempo real: {inventario}
        
        REGLAS ESTRICTAS:
        1. Si piden un perfume que ESTÁ en el inventario: dales el precio y convéncelos de comprar.
        2. Si piden un perfume que NO ESTÁ: diles que no lo tienes por ahora pero que lo anotarás para traerlo pronto.
           IMPORTANTE: Si no está, debes incluir EXACTAMENTE este texto oculto al final de tu respuesta: [FALTANTE: nombre_del_perfume]
        3. Si el cliente confirma que quiere comprar: responde normalmente y pon al final: [VENTA: nombre_del_perfume]
        4. Usa emojis (💎, ✨, 🚀).
        """
        
        # 3. Generamos la respuesta
        respuesta_ia = model.generate_content(prompt + "\n\nCliente dice: " + mensaje_cliente).text
        
        notificacion_interna = None # Variable para avisarle a Luis

        # 4. Lógica de "Lista de Deseados"
        if "[FALTANTE:" in respuesta_ia:
            try:
                item = respuesta_ia.split("[FALTANTE:")[1].split("]")[0].strip()
                url_deseados = f"{SUPABASE_URL}/rest/v1/deseados"
                requests.post(url_deseados, headers=headers_supa, json={
                    "nombre_perfume": item, 
                    "cliente_whatsapp": numero_cliente
                }, timeout=10)
                print(f"📝 Axtelix anotó un faltante: {item}")
                notificacion_interna = f"📝 ALERTA: Nos pidieron {item} y no hay stock. (Cliente: {numero_cliente})"
            except Exception as e:
                print("Error guardando faltante:", e)

        # 5. Sistema de Alertas (Notificación de Venta para Luis)
        if "[VENTA:" in respuesta_ia:
            producto_vendido = respuesta_ia.split("[VENTA:")[1].split("]")[0].strip()
            print(f"💰 ¡ALERTA LUIS! Posible venta cerrada de: {producto_vendido}")
            notificacion_interna = f"💰 ¡Posible VENTA CERRADA de {producto_vendido}! Escríbele a: {numero_cliente}"

        # 6. Limpiamos las etiquetas para que el cliente no vea los corchetes
        texto_final = respuesta_ia.split("[")[0].strip()
        
        # Retornamos la respuesta del bot Y la alerta (si existe) para el puente de JS
        return jsonify({
            "respuesta": texto_final,
            "notificar_luis": notificacion_interna
        }), 200

    except Exception as e:
        print(f"❌ Error en la IA: {e}")
        return jsonify({"error": str(e)}), 500


# =========================================================
# --- RUTAS DE GOOGLE SHEETS (SISTEMA ANTERIOR/HÍBRIDO) ---
# =========================================================

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
        print(f"Error al obtener inventario de Google: {e}")
        return jsonify([])

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

@app.route('/respaldo-preventa', methods=['POST'])
def respaldo_preventa():
    if not GOOGLE_SCRIPT_URL:
        return jsonify({"error": "Configuración faltante"}), 500
    try:
        datos_venta = request.json
        print(f"📦 Registro de preventa para: {datos_venta.get('nombre')}")
        respuesta = requests.post(GOOGLE_SCRIPT_URL, json=datos_venta, timeout=10)
        return jsonify({"status": "success", "message": "Datos asegurados en la nube"}), 200
    except Exception as e:
        print(f"❌ Error al respaldar venta: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# =========================================================
# --- RUTAS DE SUPABASE (EL NUEVO MOTOR PRINCIPAL) ---
# =========================================================

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
        url_supabase = f"{SUPABASE_URL}/rest/v1/pedidos" 
        respuesta = requests.post(url_supabase, json=datos_venta, headers=headers, timeout=10)
        if respuesta.status_code >= 400:
             print(f"Error de Supabase: {respuesta.text}")
             return jsonify({"status": "error", "message": respuesta.text}), respuesta.status_code
        return jsonify({"status": "success", "mensaje": "Venta asegurada en Supabase"}), 200
    except Exception as e:
        print(f"❌ Error al registrar en Supabase: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/obtener-productos', methods=['GET'])
def obtener_productos():
    if not SUPABASE_URL or not SUPABASE_KEY:
        return jsonify({"error": "Configuración de Supabase faltante"}), 500
    try:
        url = f"{SUPABASE_URL}/rest/v1/productos?select=*&order=id.asc"
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        respuesta = requests.get(url, headers=headers, timeout=10)
        if respuesta.status_code == 200:
            return jsonify(respuesta.json()), 200
        else:
            print(f"Error Supabase: {respuesta.text}")
            return jsonify({"error": "No se pudieron obtener los productos"}), respuesta.status_code
    except Exception as e:
        print(f"❌ Error en /obtener-productos: {e}")
        return jsonify({"error": str(e)}), 500


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
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json", "Prefer": "return=representation"}
    try:
        res = requests.post(url, headers=headers, json=request.json, timeout=10)
        return jsonify(res.json()), res.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/votar-review', methods=['POST'])
def votar_review():
    datos = request.json
    url = f"{SUPABASE_URL}/rest/v1/reviews?id=eq.{datos['id']}"
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
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
# --- INICIO DEL SERVIDOR ---
# =========================================================

if __name__ == '__main__':
    puerto = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=puerto)