from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.middleware.proxy_fix import ProxyFix
from database import get_db_connection, init_db
from datetime import datetime
import google.generativeai as genai
import json

app = Flask(__name__)
app.secret_key = "una_clave_secreta_super_segura"
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# --- CONFIGURACIÓN DE GEMINI ---
genai.configure(api_key="Aqui_tu_clave_ApiKey")
modelo = genai.GenerativeModel('gemini-2.5-flash')

init_db()

def asegurar_registro_ip(ip):
    conn = get_db_connection()
    hoy = datetime.now().strftime("%Y-%m-%d")
    # 1. Usamos IGNORE: Si la IP ya existe, no hace nada (y así no activa el borrado en cascada)
    conn.execute('INSERT OR IGNORE INTO registro_ips (ip, ultima_conexion) VALUES (?, ?)', (ip, hoy))
    # 2. Simplemente actualizamos la fecha de la última visita
    conn.execute('UPDATE registro_ips SET ultima_conexion = ? WHERE ip = ?', (hoy, ip))
    conn.commit()
    conn.close()

@app.route("/")
def index():
    ip_usuario = request.remote_addr
    asegurar_registro_ip(ip_usuario)
    
    conn = get_db_connection()
    
    # 1. Cargamos ingredientes
    ingredientes = conn.execute('SELECT * FROM ingredientes_despensa WHERE pertenece_a = ?', (ip_usuario,)).fetchall()
    
    # 2. SUGERENCIAS: Solo lo que NO es favorito Y NO ha sido cocinado
    sugerencias = conn.execute('''
        SELECT * FROM recetas 
        WHERE pertenece_a = ? AND favorito = 0 AND cocinado = 0 
        ORDER BY id DESC
    ''', (ip_usuario,)).fetchall()
    
    # 3. MI LIBRO (HISTORIAL): Lo que es favorito O ya se ha cocinado
    historial = conn.execute('''
        SELECT * FROM recetas 
        WHERE pertenece_a = ? AND (favorito = 1 OR cocinado = 1) 
        ORDER BY cocinado DESC, id DESC
    ''', (ip_usuario,)).fetchall()
    
    conn.close()

    mostrar_modal = False
    if ingredientes and not session.get('ya_preguntado'):
        mostrar_modal = True
        session['ya_preguntado'] = True
        
    return render_template("index.html", 
                           ingredientes=ingredientes, 
                           sugerencias=sugerencias, 
                           historial=historial, 
                           mostrar_modal=mostrar_modal)

@app.route("/add_ingredient", methods=["POST"])
def add_ingredient():
    ip_usuario = request.remote_addr
    asegurar_registro_ip(ip_usuario)
    
    # Lo pasamos a minúsculas y quitamos espacios extra para evitar duplicados ("Tomate" vs "tomate ")
    nombre = request.form.get("nombre").strip().lower() 
    cantidad = float(request.form.get("cantidad", 0))
    unidad = request.form.get("unidad")
    
    if nombre and cantidad > 0:
        # 1. NORMALIZACIÓN DE MEDIDAS (Convertimos a la unidad mínima)
        if unidad == 'kg':
            cantidad = cantidad * 1000
            unidad = 'gr'
        elif unidad == 'l':
            cantidad = cantidad * 1000
            unidad = 'ml'
            
        conn = get_db_connection()
        
        # 2. Comprobamos si el ingrediente ya existe en la despensa
        existente = conn.execute('SELECT id, cantidad FROM ingredientes_despensa WHERE pertenece_a = ? AND nombre = ?', (ip_usuario, nombre)).fetchone()
        
        if existente:
            # Si existe, sumamos la nueva cantidad a la que ya había
            nueva_cantidad = existente['cantidad'] + cantidad
            conn.execute('UPDATE ingredientes_despensa SET cantidad = ?, medida = ? WHERE id = ?', 
                         (nueva_cantidad, unidad, existente['id']))
        else:
            # Si no existe, creamos la fila nueva
            conn.execute('INSERT INTO ingredientes_despensa (pertenece_a, nombre, cantidad, medida) VALUES (?, ?, ?, ?)',
                         (ip_usuario, nombre, cantidad, unidad))
            
        conn.commit()
        conn.close()
        
    return redirect(url_for('index'))

@app.route("/delete_ingredient/<int:id>", methods=["POST"])
def delete_ingredient(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM ingredientes_despensa WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route("/clear_pantry", methods=["POST"])
def clear_pantry():
    ip_usuario = request.remote_addr
    conn = get_db_connection()
    conn.execute('DELETE FROM ingredientes_despensa WHERE pertenece_a = ?', (ip_usuario,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route("/generate_menu", methods=["POST"])
def generate_menu():
    ip_usuario = request.remote_addr
    dieta = request.form.get("dieta")
    tipo_solicitado = request.form.get("tipo_receta")
    personas = request.form.get("personas")
    
    conn = get_db_connection()
    ing_db = conn.execute('SELECT nombre, cantidad, medida FROM ingredientes_despensa WHERE pertenece_a = ?', (ip_usuario,)).fetchall()
    
    # 1. Validación de seguridad: Si no hay ingredientes, no llamamos a la IA
    if not ing_db:
        flash("Tu despensa está vacía. Añade ingredientes primero.", "error")
        conn.close()
        return redirect(url_for('index'))

    # 2. LA BARREDORA INTELIGENTE: Limpiamos las sugerencias anteriores que NO se usaron (ni favoritos ni cocinados)
    try:
        conn.execute('DELETE FROM recetas WHERE pertenece_a = ? AND favorito = 0 AND cocinado = 0', (ip_usuario,))
        conn.commit()
    except Exception as e:
        print(f"Error en la barredora: {e}")

    # 3. Preparamos la lista de ingredientes para enviársela al Chef IA
    contexto_despensa = ", ".join([f"{i['cantidad']} {i['medida']} de {i['nombre']}" for i in ing_db])

    instrucciones = f"""
    Eres un chef experto. Ingredientes en la despensa: {contexto_despensa}.
    Reglas estrictas:
    - Dieta: {dieta}. Para {personas} personas.
    - El usuario ha pedido: '{tipo_solicitado}'.
    - Si pidió 'menu_completo', genera EXACTAMENTE 9 recetas (3 de desayuno, 3 de comida, 3 de cena). 
    - Si pidió 'desayuno', 'comida' o 'cena', genera EXACTAMENTE 3 recetas de ese tipo específico.
    - El 'nombre' del plato debe indicar el tipo siempre al principio, ej: '[DESAYUNO] Tortilla de patatas'.
    - En 'ingredientes_usados', el 'nombre' DEBE SER IDÉNTICO a como aparece en la despensa proporcionada.
    - Usa los ingredientes de la despensa. Si hay pocos, haz recetas simples, pero NUNCA devuelvas una lista vacía.
    
    Responde ÚNICAMENTE en este formato JSON exacto, sin texto adicional:
    [
      {{
        "nombre": "Nombre del plato",
        "descripcion": "Descripción apetitosa",
        "ingredientes_usados": [ {{"nombre": "Nombre exacto despensa", "cantidad": 200}} ],
        "pasos": ["Paso 1", "Paso 2"]
      }}
    ]
    """

    try:
        print(f"Llamando a Gemini para generar: {tipo_solicitado}...")
        res = modelo.generate_content(instrucciones)
        
        # Limpiamos posibles etiquetas de markdown del texto de la IA
        texto_limpio = res.text.replace("```json", "").replace("```", "").strip()
        
        # CHIVATO DE TERMINAL: Veremos exactamente qué ha escrito Gemini
        print("\n--- RESPUESTA DE GEMINI ---")
        print(texto_limpio)
        print("---------------------------\n")

        data = json.loads(texto_limpio)
        
        # Comprobamos si la IA ha devuelto algo
        if not data or len(data) == 0:
            flash("El Chef IA no pudo crear recetas con esos ingredientes. ¡Prueba a añadir más variedad!", "error")
        else:
            hoy = datetime.now().strftime("%Y-%m-%d")
            
            for r in data:
                # Extraemos los campos con .get por seguridad si la IA omite alguno
                nombre_receta = r.get('nombre', 'Nueva Receta')
                desc_receta = r.get('descripcion', 'Receta generada por IA')
                ingredientes_usados = r.get('ingredientes_usados', [])
                pasos_receta = r.get('pasos', [])

                # Insertamos la receta principal
                cursor = conn.execute('''
                    INSERT INTO recetas (pertenece_a, nombre, dieta, personas, fecha, favorito, cocinado, descripcion, preparacion)
                    VALUES (?, ?, ?, ?, ?, 0, 0, ?, ?)
                ''', (ip_usuario, nombre_receta, dieta, personas, hoy, desc_receta, json.dumps(pasos_receta)))
                
                receta_id = cursor.lastrowid
                
                # Insertamos el detalle de cada ingrediente usado en esa receta
                for ing in ingredientes_usados:
                    conn.execute('''
                        INSERT INTO detalle_receta (receta_id, nombre, cantidad) 
                        VALUES (?, ?, ?)
                    ''', (receta_id, ing['nombre'], float(ing['cantidad'])))
            
            conn.commit()
            flash(f"¡{len(data)} sugerencias generadas con éxito!", "success")
        
    except Exception as e:
        print("\n========== ERROR DETALLADO EN GENERACIÓN ==========")
        print(f"Tipo de error: {type(e).__name__}")
        print(f"Mensaje: {e}")
        print("===================================================\n")
        flash("Hubo un problema técnico al crear las recetas. Revisa la terminal.", "error")

    conn.close()
    return redirect(url_for('index'))
@app.route("/cook_selection", methods=["POST"])
def cook_selection():
    ids_seleccionados = request.form.getlist("recetas_seleccionadas")
    if not ids_seleccionados:
        flash("Selecciona qué platos vas a cocinar.", "error")
        return redirect(url_for('index'))

    ip_usuario = request.remote_addr
    conn = get_db_connection()
    
    # 1. Sumamos ingredientes necesarios
    necesidades = {}
    for r_id in ids_seleccionados:
        detalles = conn.execute('SELECT nombre, cantidad FROM detalle_receta WHERE receta_id = ?', (r_id,)).fetchall()
        for d in detalles:
            necesidades[d['nombre']] = necesidades.get(d['nombre'], 0) + d['cantidad']

    # 2. Comprobamos stock
    faltan = []
    for nombre, cant_req in necesidades.items():
        stock = conn.execute('SELECT cantidad FROM ingredientes_despensa WHERE pertenece_a = ? AND nombre = ?', (ip_usuario, nombre)).fetchone()
        if not stock or stock['cantidad'] < cant_req:
            faltan.append(nombre)

    if faltan:
        flash(f"No hay ingredientes suficientes: {', '.join(faltan)}", "error")
        conn.close()
        return redirect(request.referrer or url_for('index'))

    # 3. RESTAMOS Y LIMPIAMOS
    for nombre, cant_req in necesidades.items():
        conn.execute('UPDATE ingredientes_despensa SET cantidad = cantidad - ? WHERE pertenece_a = ? AND nombre = ?', (cant_req, ip_usuario, nombre))
    
    conn.execute('DELETE FROM ingredientes_despensa WHERE cantidad <= 0')

    # Marcamos como cocinadas
    for r_id in ids_seleccionados:
        conn.execute('UPDATE recetas SET cocinado = 1 WHERE id = ?', (r_id,))
    
    # LA REGLA DE ORO: Limpiamos el resto de sugerencias que no se han cocinado ni son favoritas
    conn.execute('''
        DELETE FROM recetas 
        WHERE pertenece_a = ? AND favorito = 0 AND cocinado = 0
    ''', (ip_usuario,))
    
    conn.commit()
    conn.close()
    flash("¡Buen provecho! Despensa actualizada y sugerencias limpiadas.", "success")
    return redirect(url_for('index'))

@app.route("/recipe/<int:id>")
def recipe(id):
    conn = get_db_connection()
    receta_db = conn.execute('SELECT * FROM recetas WHERE id = ?', (id,)).fetchone()
    if not receta_db:
        return "No existe", 404
        
    ingredientes_receta = conn.execute('SELECT * FROM detalle_receta WHERE receta_id = ?', (id,)).fetchall()
    pasos = json.loads(receta_db['preparacion'])
    
    receta = {
        **dict(receta_db),
        "pasos": pasos,
        "ingredientes": ingredientes_receta
    }
    conn.close()
    return render_template("recipe.html", receta=receta)

@app.route("/toggle_favorite/<int:id>", methods=["POST"])
def toggle_favorite(id):
    conn = get_db_connection()
    conn.execute('UPDATE recetas SET favorito = 1 - favorito WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(request.referrer or url_for('index'))

@app.route("/delete_recipe/<int:id>", methods=["POST"])
def delete_recipe(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM recetas WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route("/favorites")
def favorites():
    ip_usuario = request.remote_addr
    conn = get_db_connection()
    favoritos = conn.execute('SELECT * FROM recetas WHERE pertenece_a = ? AND favorito = 1', (ip_usuario,)).fetchall()
    conn.close()
    return render_template("favorites.html", favoritos=favoritos)

if __name__ == "__main__":
    app.run(debug=True)