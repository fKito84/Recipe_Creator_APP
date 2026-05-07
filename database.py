from flask import Flask, render_template, request, redirect, url_for
from werkzeug.middleware.proxy_fix import ProxyFix  # 1. Importamos la herramienta
from database import get_db_connection, init_db

app = Flask(__name__)

# 2. Le decimos a Flask que lea la IP real detrás del portero de Internet
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

init_db()

@app.route("/")
def index():
    # Ahora sí, atrapamos la IP real del móvil, incluso en Internet
    ip_usuario = request.remote_addr
    
    conn = get_db_connection()
    ingredientes = conn.execute(
        'SELECT * FROM ingredientes_despensa WHERE pertenece_a = ?', 
        (ip_usuario,)
    ).fetchall()
    conn.close()
    
    return render_template("index.html", ingredientes=ingredientes)

@app.route("/add_ingredient", methods=["POST"])
def add_ingredient():
    nombre = request.form.get("nombre")
    cantidad = request.form.get("cantidad")
    medida = request.form.get("unidad")
    ip_usuario = request.remote_addr 
    
    if nombre:
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO ingredientes_despensa (pertenece_a, nombre, cantidad, medida) 
            VALUES (?, ?, ?, ?)
        ''', (ip_usuario, nombre, cantidad, medida))
        conn.commit()
        conn.close()
        
    return redirect(url_for('index'))