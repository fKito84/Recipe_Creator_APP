from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# --- RUTAS DE NAVEGACIÓN ---

@app.route("/")
def index():
    # Aquí cargaremos los ingredientes de la base de datos más adelante
    ingredientes_mock = [] 
    return render_template("index.html", ingredientes=ingredientes_mock)

@app.route("/favorites")
def favorites():
    # Aquí cargaremos los favoritos de la base de datos
    favoritos_mock = []
    return render_template("favorites.html", favoritos=favoritos_mock)

@app.route("/recipe/<id>")
def recipe(id):
    # Esto es un dato falso (mock) para probar que la vista funciona
    receta_prueba = {
        "id": id,
        "nombre": "Pollo al horno con verduras",
        "emoji": "🍗",
        "tiempo": 45,
        "calorias": 450,
        "personas": 2,
        "dieta": "completa",
        "ingredientes": [
            {"nombre": "Pechuga de pollo", "cantidad": "300gr"},
            {"nombre": "Pimientos", "cantidad": "2 unid"}
        ],
        "pasos": [
            "Precalentar el horno a 180°C.",
            "Cortar el pollo y hornear por 45 minutos."
        ]
    }
    return render_template("recipe.html", receta=receta_prueba)

# --- RUTAS DE ACCIÓN (Los botones de tus formularios enviarán datos aquí) ---

@app.route("/add_ingredient", methods=["POST"])
def add_ingredient():
    nombre = request.form.get("nombre")
    cantidad = request.form.get("cantidad")
    unidad = request.form.get("unidad")
    print(f"Añadiendo: {cantidad} {unidad} de {nombre}")
    # Próximo paso: guardar en SQLite
    return redirect(url_for('index'))

@app.route("/generate_menu", methods=["POST"])
def generate_menu():
    dieta = request.form.get("dieta")
    comensales = request.form.get("personas")
    print(f"Generando menú {dieta} para {comensales} personas...")
    # Próximo paso: Conectar con IA de Gemini
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)