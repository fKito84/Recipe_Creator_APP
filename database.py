import sqlite3

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.execute('PRAGMA foreign_keys = ON;') # Esencial para que las FK y el borrado funcionen
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    
    # 1. Tabla maestra: registro_ips
    conn.execute('''
        CREATE TABLE IF NOT EXISTS registro_ips (
            ip TEXT PRIMARY KEY,
            ultima_conexion TEXT NOT NULL
        )
    ''')

    # 2. Tabla: ingredientes_despensa
    conn.execute('''
        CREATE TABLE IF NOT EXISTS ingredientes_despensa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pertenece_a TEXT NOT NULL,
            nombre TEXT NOT NULL,
            cantidad REAL NOT NULL,
            medida TEXT NOT NULL CHECK(medida IN ('gr', 'unid', 'ml')), -- ¡Solo las medidas normalizadas!
            FOREIGN KEY (pertenece_a) REFERENCES registro_ips(ip) ON DELETE CASCADE
        )
    ''')
    
    # 3. Tabla: recetas (Solo se ha añadido 'cocinado')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS recetas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pertenece_a TEXT NOT NULL,
            nombre TEXT NOT NULL,
            dieta TEXT NOT NULL CHECK(dieta IN ('vegetariano', 'vegano', 'carnivoro', 'dieta completa')),
            personas INTEGER NOT NULL,
            fecha TEXT NOT NULL,
            favorito INTEGER NOT NULL CHECK(favorito IN (0, 1)) DEFAULT 0,
            cocinado INTEGER NOT NULL DEFAULT 0,
            descripcion TEXT NOT NULL,
            preparacion TEXT NOT NULL,
            FOREIGN KEY (pertenece_a) REFERENCES registro_ips(ip) ON DELETE CASCADE
        )
    ''')
    
    # 4. Tabla: detalle_receta (Una línea por ingrediente)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS detalle_receta (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            receta_id INTEGER NOT NULL,
            nombre TEXT NOT NULL,
            cantidad REAL NOT NULL,
            FOREIGN KEY (receta_id) REFERENCES recetas(id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    conn.close()