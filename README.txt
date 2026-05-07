1. De Figma a Flask (Las Vistas)
    Empezamos con los archivos que te generó Figma Make. Estaban hechos en React (un sistema
    complejo de JavaScript), lo cual era demasiado pesado para lo que pide tu práctica.
        Lo que hicimos: Tradujimos todo ese código a HTML puro manteniendo exactamente el mismo 
        diseño gracias a Tailwind CSS (para los estilos) y Lucide (para los iconos).
    Archivos creados (en la carpeta templates):
        index.html: La pantalla principal donde ves tu despensa y el formulario para generar menús.
        favorites.html: La pantalla donde se guardarán las recetas que marques con la estrella.
        recipe.html: El detalle paso a paso de cada receta generada.
2. El Motor de la App (Python y Módulos)

    Necesitábamos que esos diseños dejaran de ser una simple foto y empezaran a funcionar.

        Lo que hicimos: Creamos tu entorno de trabajo (.venv) e instalamos las herramientas 
        necesarias mediante la terminal.

        Módulos instalados:
            flask: El corazón de tu aplicación web. Es el que recibe las peticiones y muestra las pantallas HTML.
            google-generativeai: El módulo que usaremos en el próximo paso para conectar tu app 
            con el "cerebro" de Gemini.

        Archivo creado: app.py. Este es el director de orquesta que recibe los clics de los 
        botones web y ejecuta las acciones.

3. La Memoria (Base de Datos SQLite)

        Diseñamos cómo tu aplicación va a recordar la información, ajustándola a tus requisitos 
        exactos para que sea robusta.

            Lo que hicimos: Creamos el archivo database.py que genera automáticamente un 
            archivo database.db en tu ordenador.  

            structura de tablas:

                 Tabla                   Para qué sirve                     Campos clave 
        ----------------------------------------------------------------------------------------------------
            ingredientes_despensa      Guarda lo que tienes en casa.       Nombre, cantidad (con decimales), 
                                                                            y la medida exacta (gr, kg, ml, etc.).
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

   Querías que el profesor viera que la aplicación sabe distinguir entre diferentes personas 
   (por ejemplo, si entran desde dos móviles distintos), sin tener que programar un sistema de contraseñas pesado.     

       Lo que hicimos: Añadimos el campo pertenece_a a las tablas de la base de datos para guardar 
       la dirección IP del usuario. 

       El "Salvavidas" para Internet: Añadimos la herramienta ProxyFix en tu app.py. Esto garantiza que, 
       si subes la aplicación a un servidor de Internet (donde un "portero automático" oculta las IPs originales),
        tu aplicación siga siendo capaz de leer la IP real de cada móvil para mostrar a cada uno su propia despensa.


