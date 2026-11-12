# Decisiones

La [definición](DEFINICION.md) contiene el detalle acordado el 12 de noviembre de 2026. Este índice evita reinterpretar decisiones desde el prototipo antiguo.

| Tema | Decisión |
|---|---|
| Identidad | Token aleatorio fijo por cuadro preparado por el desarrollador, presentado como Bearer a la API y como contraseña de una cuenta técnica Firebase Auth del dispositivo; el SHA-256 deriva el ámbito. Sin registro del familiar ni segundo secreto que deba introducir. |
| Selecciones | Tres huecos, cada uno canción o emisora; sin playlists iniciales. |
| Controles | Tres pulsadores iluminados y rueda. Repetir el botón activo detiene; pulsación larga restablece Wi-Fi. |
| Encendido | Imagen decorativa y silencio, recordando volumen. |
| Audio | Streaming directo al ESP32, búfer y sin SD; canción termina y se detiene. |
| Web | Móvil primero, dinámica sin recargas y JavaScript modular; sin React. |
| Escucha web | Audio en el navegador; sin órdenes al cuadro ni volumen remoto. |
| Contenido | Búsqueda YouTube con elección de resultado; Radio Browser para emisoras. |
| Imagen | Decorativa independiente elegida en web; procesamiento servidor y sin original permanente. |
| Sustitución | Preparar antes de publicar; preservar el audio activo y limpiar cuando deje de utilizarse. |
| Tareas | Una importación por cuadro y estado recuperable al volver a la web. |
| Hosting | Web propia; backend Render/Docker; RTDB y Storage; no Firebase Hosting. |
| Portfolio | Repo público `cuadro-sonoro`, secretos excluidos, demo identificada sin servicios reales. |

Pendientes: integración física del token en QR/NFC, validación real de importación y reglas Firebase, firmware/hardware, cola/worker final, límites/calidades, imagen local sin red, limpieza con referencias activas, reanudación tras caída de audio y licencia. No añadir una autenticación al familiar.

## Decisión técnica — 12 de noviembre de 2026

El acceso de la API usa el token aleatorio fijo provisionado del cuadro en `Authorization: Bearer`. El backend compara su SHA-256 con `FRAME_TOKEN_HASHES` y nunca guarda el token original. Ese mismo hash deriva el ámbito de RTDB, SQLite local, tareas y nuevas rutas de Storage. Para el acceso directo, el desarrollador crea una cuenta técnica Firebase Auth con UID `frame-reader-{sha256}` y contraseña igual al Bearer. El cliente del dispositivo inicia sesión por Firebase Auth REST y guarda ID/refresh token en almacenamiento privado; los renueva sin Render. Reglas RTDB/Storage comparan UID autenticado con el cuadro y permiten únicamente lectura de slots y objetos privados de ese ámbito. El hash/ruta por sí solo no autoriza. No usar enlaces temporales firmados como sustituto. Validado solo con emuladores locales hasta la prueba descrita en VALIDACION.md; reglas reales e importación aún pendientes. No se migra automáticamente la colección antigua porque no se conoce a qué cuadro pertenecen sus datos.

En cada cambio de decisión registrar fecha, problema, decisión y efecto sobre código/documentación. El propietario puede modificar estas decisiones mediante instrucciones nuevas; actualizar la definición para que no quede una contradicción.
