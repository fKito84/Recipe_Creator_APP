
# RecetApp - Gestor de Despensa y Generador de Recetas con IA

1. De Figma a Flask (Las Vistas)
Empezamos con los archivos generados por Figma Make. Estaban hechos en React (un ecosistema complejo de JavaScript), lo cual era demasiado pesado para el alcance de esta práctica. 
    Lo que hicimos: Tradujimos todo ese código a HTML puro manteniendo exactamente el mismo diseño gracias a Tailwind CSS (para los estilos rápidos) y Lucide (para los iconos).
Archivos creados (en la carpeta templates):
    - index.html: La pantalla principal dividida en dos grandes bloques dinámicos: "Sugerencias del Chef" (temporales) y "Mi Libro de Cocina" (historial).
    - favorites.html: La pantalla dedicada exclusivamente a las recetas que marques con el icono del corazón.
    - recipe.html: El detalle paso a paso de cada receta generada, con botones de acción rápida para cocinar o guardar.

2. El Motor de la App (Python y Módulos)
Necesitábamos que los diseños dejaran de ser estáticos y empezaran a procesar lógica real.
    Lo que hicimos: Creamos un entorno virtual (.venv) e instalamos las herramientas necesarias.
Módulos principales instalados:
    - flask: El framework de nuestra aplicación web. Recibe peticiones, enlaza rutas y renderiza las pantallas HTML.
    - google-generativeai: El módulo que conecta el backend con el modelo LLM de Google Gemini.
Archivo maestro: app.py. Es el controlador principal que maneja el inventario, procesa formularios y orquesta las llamadas a la IA.

3. La Memoria (Base de Datos Relacional SQLite)
Diseñamos una estructura robusta para almacenar inventario e historial, aplicando reglas estrictas de integridad. Archivo: database.py.

    - Tabla: ingredientes_despensa   
      Para qué sirve: Guarda el stock actual del usuario.
      Campos clave: Nombre, cantidad, y un CHECK restrictivo de medida ('gr', 'ml', 'unid') para forzar la normalización de datos.
      
    - Tabla: recetas              
      Para qué sirve: Almacena las sugerencias de la IA y el historial personal.
      Campos clave: Dieta, personas, preparación (guardada en JSON), favorito (0/1) y el estado cocinado (0/1).
      
    - Tabla: detalle_receta         
      Para qué sirve: Desglosa los ingredientes que exige cada receta.
      Campos clave: Nombre del ingrediente y cantidad. Vinculada a 'recetas' mediante borrado en cascada. El cruce con la despensa se hace a través del campo "nombre" para evitar desajustes con IDs volátiles de inventario.

         structura de tablas:

                 Tabla                   Para qué sirve                     Campos clave 
        ----------------------------------------------------------------------------------------------------
            ingredientes_despensa      Guarda lo que tienes en casa.       Nombre, cantidad (con decimales), 
                                                                            y la medida exacta (gr, unid, ml).
        ---------------------------------------------------------------------------------------------------
              recetas              Guarda la lista de ingredientes        Está enlazada a la tabla recetas. 
                                    que usa una receta concreta.          Si borras la receta, sus    
                                                                          ingredientes se borran automáticamente 
                                                                          (Borrado en cascada).
        ---------------------------------------------------------------------------------------------------

            detalle_receta         Guarda la lista de ingredientes        Está enlazada a la tabla recetas. 
                                    que usa una receta concreta.          Si borras la receta, sus ingredientes 
                                                                          se borran automáticamente (Borrado en cascada).
            

4. El Toque Profesional (Multiusuario por IP)
La aplicación sabe distinguir entre diferentes personas (simulando usuarios en modo desarrollo) sin necesitar un sistema de login complejo.
    Lo que hicimos: Añadimos el campo pertenece_a a todas las tablas para vincular cada ingrediente y receta a la dirección IP.
    El "Salvavidas" para servidores: Implementamos la herramienta ProxyFix en app.py, garantizando que si se despliega en producción, la app lea la IP real del cliente y no la del proxy del servidor.

5. Inteligencia Artificial (Conexión con Gemini 2.5 Flash)
La aplicación no busca recetas preexistentes, las "inventa" en tiempo real basándose en restricciones estrictas.
    Prompt Engineering: Se fuerza a la IA a respetar la dieta, los comensales y el número exacto de platos (ej: 9 platos para un menú completo). 
    Anti-Alucinaciones: La IA está obligada a devolver un esquema JSON estricto y a utilizar los nombres de los ingredientes de forma idéntica a como están escritos en la base de datos de la despensa.

6. Motor de Inventario y Normalización de Datos
Para que la resta de ingredientes funcione matemáticamente, implementamos lógica de ERP en el controlador.
    - Normalización: Si el usuario introduce "1 kg" o "1 l", Python lo multiplica por 1000 y lo inserta en la BD como "gr" o "ml". La base de datos nunca ve kilos ni litros.
    - Consolidación: Si se añade un ingrediente que ya existe, no se duplica la fila, sino que se suman las cantidades automáticamente.
    - Resta Segura: Al "Cocinar", el sistema suma las cantidades exigidas por la receta, verifica que el stock sea mayor o igual, y procede a la resta, eliminando de la base de datos aquellos ingredientes que lleguen a 0.

7. Ciclo de Vida de las Recetas ("Barredora" y Libro de Cocina)
Controlamos que la base de datos no acumule basura digital generada por la IA.
    - La Barredora Inteligente: Antes de generar un nuevo menú o al terminar de cocinar un plato, se ejecuta un DELETE que limpia automáticamente todas las sugerencias anteriores que no fueron cocinadas ni guardadas en favoritos (favorito=0 AND cocinado=0).

8. Resumen de Funcionalidades Completas
    - Añadir ingredientes con conversión automática de unidades.
    - Eliminar ingredientes manualmente o vaciar la despensa entera.
    - Generar menús personalizados (Desayuno, Comida, Cena o Completos) basados en el stock y preferencias dietéticas.
    - Sistema de validación de stock antes de cocinar.
    - Descuento automático de ingredientes tras cocinar un plato.
    - Guardado de recetas en Favoritos (corazón).
    - Historial permanente de recetas cocinadas (check verde).
    - Visualización de pasos de preparación y cantidades requeridas por plato.

9. Cómo lanzar la aplicación en Modo Desarrollo

    Paso 1: Clonar el repositorio y abrir la terminal en la carpeta del proyecto.
    Paso 2: Activar el entorno virtual.
            - En Windows: .\.venv\Scripts\activate
            - En Mac/Linux: source .venv/bin/activate
    Paso 3: Instalar las dependencias necesarias.
            > pip install flask google-generativeai werkzeug
    Paso 4: Configurar la API Key.
            - Abrir app.py y sustituir el valor "TU_API_KEY_AQUI" en genai.configure() por una clave válida de Google AI Studio.
    Paso 5: Ejecutar el servidor.
            > python app.py
    Paso 6: Abrir el navegador y acceder a: http://127.0.0.1:5000