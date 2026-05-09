python -c "
contenido = '''---
title: \"RecetApp - Gestor de Despensa y Generador de Recetas con IA\"
subtitle: \"Documentación Técnica Completa del Proyecto\"
author: \"Francisco Muñoz Gonzalez\"
date: \"2026-05-09\"
version: \"1.0.0\"
abstract: |
  RecetApp es una aplicacion web full-stack desarrollada con Flask y SQLite 
  que utiliza inteligencia artificial (Google Gemini 2.5 Flash) para generar 
  recetas personalizadas basadas en los ingredientes disponibles en la despensa 
  del usuario. El sistema implementa un motor de inventario con normalizacion 
  de unidades, gestion multiusuario por IP sin necesidad de registro, y un 
  sistema de estados para el ciclo de vida de las recetas generadas.
toc: true
toc-depth: 3
numbersections: true
lang: es
---

\newpage

# Resumen Ejecutivo

## Vision General del Proyecto

RecetApp resuelve un problema cotidiano: \"Que puedo cocinar con lo que tengo en casa?\". La aplicacion permite a los usuarios gestionar una despensa virtual, generar recetas creativas mediante inteligencia artificial basadas exclusivamente en los ingredientes disponibles, y gestionar un libro de cocina personal con favoritos e historial de platos cocinados.

## Objetivos del Sistema

| Objetivo | Descripcion | Estado |
|----------|-------------|--------|
| Gestion de despensa | Anadir, eliminar y normalizar ingredientes con unidades | Completado |
| Generacion IA | Crear recetas personalizadas con Gemini 2.5 Flash | Completado |
| Control de inventario | Resta automatica de ingredientes al cocinar | Completado |
| Multiusuario | Diferenciacion de usuarios por direccion IP | Completado |
| Favoritos | Sistema de guardado de recetas preferidas | Completado |
| Historial | Registro permanente de recetas cocinadas | Completado |

## Tecnologias Utilizadas

| Capa | Tecnologia | Version | Justificacion |
|------|-----------|---------|---------------|
| Frontend | HTML5 + Tailwind CSS | CDN latest | Diseno responsive sin framework pesado |
| Iconos | Lucide Icons | CDN latest | Iconografia moderna y ligera |
| Backend | Python + Flask | 3.x | Framework minimalista y flexible |
| Base de Datos | SQLite | 3.x | Sin servidor, ideal para desarrollo |
| IA | Google Gemini 2.5 Flash | API v1 | Generacion rapida y economica |
| Middleware | Werkzeug ProxyFix | 3.x | Preparacion para entornos de produccion |

\newpage

# Arquitectura del Sistema

## Estructura del Proyecto

\`\`\`
Recipe_Creator_APP/
|
+-- app.py                 # Controlador principal (Flask + rutas + logica)
+-- database.py            # Esquema de BD y gestion de conexiones SQLite
+-- database.db            # Archivo de base de datos SQLite (generado)
+-- README.md              # Documentacion general y guia de instalacion
+-- .gitignore             # Archivos excluidos del control de versiones
|
+-- templates/             # Plantillas HTML (Jinja2)
|   +-- index.html         # Pantalla principal
|   +-- recipe.html        # Detalle de receta
|   +-- favorites.html     # Lista de favoritos
|
+-- static/                # Archivos estaticos
|   +-- (vacio - se usan CDNs)
|
+-- .venv/                 # Entorno virtual de Python
\`\`\`

## Flujo de Datos Principal

1. Usuario anade ingredientes (normalizacion automatica de unidades)
2. Usuario solicita menu (configura dieta, tipo, comensales)
3. Sistema ejecuta Barredora (limpia sugerencias anteriores no usadas)
4. Lee despensa actual y construye prompt para Gemini
5. IA genera recetas en formato JSON estructurado
6. Recetas se almacenan en BD (tablas recetas y detalle_receta)
7. Al cocinar: verifica stock, resta ingredientes, limpia ceros
8. Recetas cocinadas pasan a historial permanente (Mi Libro de Cocina)

\newpage

# Base de Datos

## Diagrama Entidad-Relacion

El modelo de datos tiene 4 tablas con integridad referencial:

- **registro_ips**: Tabla maestra (usuarios por IP)
- **ingredientes_despensa**: Inventario de cada usuario
- **recetas**: Recetas generadas con metadatos y estados
- **detalle_receta**: Ingredientes necesarios por receta

### Relaciones

- registro_ips (1) -> (N) ingredientes_despensa (ON DELETE CASCADE)
- registro_ips (1) -> (N) recetas (ON DELETE CASCADE)
- recetas (1) -> (N) detalle_receta (ON DELETE CASCADE)

## Diccionario de Datos

### Tabla: registro_ips

| Campo | Tipo | Restricciones | Descripcion |
|-------|------|--------------|-------------|
| ip | TEXT | PRIMARY KEY | Direccion IP del usuario |
| ultima_conexion | TEXT | NOT NULL | Fecha ultima visita (YYYY-MM-DD) |

### Tabla: ingredientes_despensa

| Campo | Tipo | Restricciones | Descripcion |
|-------|------|--------------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | ID unico |
| pertenece_a | TEXT | NOT NULL, FK | IP del propietario |
| nombre | TEXT | NOT NULL | Nombre normalizado (minusculas) |
| cantidad | REAL | NOT NULL | Cantidad almacenada |
| medida | TEXT | NOT NULL, CHECK (gr,ml,unid) | Unidad normalizada |

### Tabla: recetas

| Campo | Tipo | Restricciones | Descripcion |
|-------|------|--------------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | ID unico |
| pertenece_a | TEXT | NOT NULL, FK | IP del creador |
| nombre | TEXT | NOT NULL | Nombre del plato |
| dieta | TEXT | NOT NULL, CHECK (4 valores) | Tipo de dieta |
| personas | INTEGER | NOT NULL | Numero de comensales |
| fecha | TEXT | NOT NULL | Fecha de creacion |
| favorito | INTEGER | DEFAULT 0, CHECK (0,1) | Estado favorito |
| cocinado | INTEGER | DEFAULT 0 | Estado cocinado |
| descripcion | TEXT | NOT NULL | Descripcion generada por IA |
| preparacion | TEXT | NOT NULL | Pasos en JSON |

### Tabla: detalle_receta

| Campo | Tipo | Restricciones | Descripcion |
|-------|------|--------------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | ID unico |
| receta_id | INTEGER | NOT NULL, FK | Receta asociada |
| nombre | TEXT | NOT NULL | Nombre del ingrediente |
| cantidad | REAL | NOT NULL | Cantidad requerida |

## Script SQL de Creacion

\`\`\`sql
PRAGMA foreign_keys = ON;

CREATE TABLE registro_ips (
    ip TEXT PRIMARY KEY,
    ultima_conexion TEXT NOT NULL
);

CREATE TABLE ingredientes_despensa (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pertenece_a TEXT NOT NULL,
    nombre TEXT NOT NULL,
    cantidad REAL NOT NULL,
    medida TEXT NOT NULL CHECK(medida IN (\"gr\", \"unid\", \"ml\")),
    FOREIGN KEY (pertenece_a) REFERENCES registro_ips(ip) ON DELETE CASCADE
);

CREATE TABLE recetas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pertenece_a TEXT NOT NULL,
    nombre TEXT NOT NULL,
    dieta TEXT NOT NULL CHECK(dieta IN (\"vegetariano\", \"vegano\", \"carnivoro\", \"dieta completa\")),
    personas INTEGER NOT NULL,
    fecha TEXT NOT NULL,
    favorito INTEGER NOT NULL DEFAULT 0 CHECK(favorito IN (0, 1)),
    cocinado INTEGER NOT NULL DEFAULT 0,
    descripcion TEXT NOT NULL,
    preparacion TEXT NOT NULL,
    FOREIGN KEY (pertenece_a) REFERENCES registro_ips(ip) ON DELETE CASCADE
);

CREATE TABLE detalle_receta (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receta_id INTEGER NOT NULL,
    nombre TEXT NOT NULL,
    cantidad REAL NOT NULL,
    FOREIGN KEY (receta_id) REFERENCES recetas(id) ON DELETE CASCADE
);
\`\`\`

\newpage

# Flujos del Sistema

## Flujo 1: Anadir Ingrediente

**Ruta**: POST /add_ingredient

1. Recibe nombre, cantidad, unidad del formulario
2. Normaliza nombre (minusculas, sin espacios extra)
3. Normaliza unidades: kg->gr (x1000), l->ml (x1000)
4. Verifica si existe en despensa del usuario
5. Si existe: UPDATE sumando cantidad
6. Si no existe: INSERT nuevo registro
7. Redirige a index

## Flujo 2: Generar Menu con IA

**Ruta**: POST /generate_menu

1. Recibe dieta, tipo_receta, personas
2. Valida que la despensa no este vacia
3. Ejecuta Barredora (DELETE sugerencias efimeras)
4. Lee despensa actual del usuario
5. Construye prompt con:
   - Lista de ingredientes disponibles
   - Restricciones de dieta y comensales
   - Formato JSON estricto
   - Nombres identicos a la despensa (anti-alucinaciones)
6. Llama a Gemini 2.5 Flash
7. Limpia respuesta (quita etiquetas markdown)
8. Parsea JSON y guarda en BD

## Flujo 3: Cocinar Receta

**Ruta**: POST /cook_selection

1. Recibe IDs de recetas seleccionadas
2. Suma ingredientes necesarios de todas las recetas
3. Verifica stock contra despensa
4. Si falta algo: error SIN modificar BD
5. Si hay stock: resta ingredientes
6. Elimina ingredientes con cantidad <= 0
7. Marca recetas como cocinadas (cocinado=1)
8. Ejecuta Barredora final

## Flujo 4: Maquina de Estados de Recetas

| Estado | favorito | cocinado | Ubicacion UI | Persistencia |
|--------|----------|----------|--------------|--------------|
| Efimero | 0 | 0 | Sugerencias del Chef | Se auto-elimina |
| Guardado | 1 | 0 | Libro Cocina + Favoritos | Permanente |
| Cocinado | 0 | 1 | Libro de Cocina | Permanente |
| Completo | 1 | 1 | Libro Cocina + Favoritos | Permanente |

### Transiciones

- IA genera -> Efimero (0,0)
- Pulsar corazon -> Guardado (1,0)
- Pulsar cocinar -> Cocinado (0,1)
- Cocinar favorito -> Completo (1,1)
- No usar + Barredora -> Eliminado

## Flujo 5: La Barredora Inteligente

Sistema de limpieza automatica que evita basura digital.

Se ejecuta en dos momentos:
- Antes de generar nuevo menu
- Despues de cocinar recetas

Elimina solo:
\`\`\`sql
DELETE FROM recetas 
WHERE pertenece_a = ? 
AND favorito = 0 
AND cocinado = 0
\`\`\`

\newpage

# Implementacion Tecnica

## Sistema Multiusuario por IP

Usa request.remote_addr como identificador. ProxyFix para entornos con proxy inverso. Evita complejidad de autenticacion.

## Normalizacion de Unidades

Conversion en capa de aplicacion antes de insertar en BD. La BD solo acepta gr, ml, unid (CHECK constraint).

## Consolidacion de Stock

Si se anade ingrediente existente, se suma cantidad en lugar de duplicar.

## Prompt Engineering

Se fuerza a Gemini a usar nombres identicos a la despensa. Respuesta solo en JSON estricto. Nunca devuelve lista vacia.

## Codigo Clave

**Normalizacion (app.py):**
\`\`\`python
if unidad == \"kg\":
    cantidad = cantidad * 1000
    unidad = \"gr\"
elif unidad == \"l\":
    cantidad = cantidad * 1000
    unidad = \"ml\"
\`\`\`

**Consolidacion (app.py):**
\`\`\`python
existente = conn.execute(
    \"SELECT id, cantidad FROM ingredientes_despensa WHERE pertenece_a = ? AND nombre = ?\",
    (ip_usuario, nombre)
).fetchone()

if existente:
    nueva_cantidad = existente[\"cantidad\"] + cantidad
    conn.execute(\"UPDATE ingredientes_despensa SET cantidad = ? WHERE id = ?\",
                 (nueva_cantidad, existente[\"id\"]))
else:
    conn.execute(\"INSERT INTO ingredientes_despensa ...\")
\`\`\`

**Toggle favorito (app.py):**
\`\`\`python
conn.execute(\"UPDATE recetas SET favorito = 1 - favorito WHERE id = ?\", (id,))
\`\`\`

\newpage

# Interfaz de Usuario

## Pantallas

### index.html - Principal
- Header con logo y boton Favoritos
- Mi Despensa: formulario + lista ingredientes
- Configurar Menu: selectores + boton generar
- Sugerencias del Chef: recetas efimeras con checkboxes
- Mi Libro de Cocina: historial permanente

### recipe.html - Detalle
- Botones Cocinar y Favorito
- Badges: comensales, dieta
- Lista de ingredientes requeridos
- Pasos de preparacion numerados

### favorites.html - Favoritos
- Estado vacio con ilustracion
- Grid de tarjetas con acciones

## Iconos (Lucide)

| Icono | Uso |
|-------|-----|
| chef-hat | Logo |
| star | Favoritos |
| heart | Toggle favorito |
| flame | Cocinar |
| eye | Ver detalle |
| trash-2 | Eliminar |
| package | Despensa |
| book-open | Libro cocina |
| loader-2 | Carga |

\newpage

# Guia de Instalacion

## Requisitos

- Python 3.8+
- pip
- API Key de Google AI Studio

## Instalacion

\`\`\`bash
git clone https://github.com/fKito84/Recipe_Creator_APP.git
cd Recipe_Creator_APP
python -m venv .venv
.\\.venv\\Scripts\\activate
pip install flask google-generativeai werkzeug
python app.py
\`\`\`

Configurar API Key en app.py linea 14.
Acceder en http://127.0.0.1:5000

\newpage

# Historial de Desarrollo

## Commit f6cce9a - Version inicial
**Fecha**: Mayo 2026
Vistas HTML con Figma Make y Tailwind CSS. Prototipo visual.

## Commit 91e0fc1 - Funciones y BD
**Fecha**: 7 mayo 2026
Backend Flask, esquema SQLite, README. Primer andamiaje funcional.

## Commit b40ad4a - Version completa
**Fecha**: 9 mayo 2026

- Fix critico: IPs con INSERT OR IGNORE + UPDATE
- Motor inventario ERP: normalizacion y consolidacion
- Refactor BD: CHECK constraints
- Optimizacion Gemini: prompt engineering anti-alucinaciones
- Barredora inteligente
- UI/UX: separacion Sugerencias/Libro Cocina
- Loading spinner, botones volver a cocinar
- Documentacion completa y .gitignore

\newpage

# Analisis y Mejoras

## Fortalezas

1. Arquitectura limpia (3 capas)
2. Integridad de datos (FK, CHECK, CASCADE)
3. UX responsive con feedback visual
4. Preparacion produccion (ProxyFix)
5. Prompt engineering robusto

## Areas de Mejora

### Critica: API Key en codigo
Problema: Clave hardcodeada en app.py.
Solucion: Variables de entorno con python-dotenv.

### Alta: Unidades en detalle_receta
Problema: No se almacena unidad en ingredientes de receta.
Solucion: Anadir columna unidad o inferir de despensa.

### Media: Manejo errores IA
Problema: Errores de Gemini muestran mensaje generico.
Solucion: Diferenciar JSON invalido vs error de red.

\newpage

# Conclusiones

RecetApp demuestra integracion de:
- Frontend moderno con Tailwind CSS responsive
- Backend robusto con Flask y patron MVC
- Base de datos con integridad referencial completa
- IA con prompt engineering avanzado
- Gestion de estados con maquina de estados

Decisiones tecnicas (normalizacion, consolidacion, barredora, multiusuario por IP) muestran comprension de necesidades reales.

---

**Version**: 1.0.0
**Fecha**: 9 de mayo de 2026
**Autor**: Francisco Munoz Gonzalez
**Repositorio**: github.com/fKito84/Recipe_Creator_APP
'''

with open('documentacion_recetapp.md', 'w', encoding='utf-8') as f:
    f.write(contenido)

print('Archivo documentacion_recetapp.md creado correctamente')
"