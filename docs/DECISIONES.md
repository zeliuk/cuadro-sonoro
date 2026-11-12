# Decisiones

La [definición](DEFINICION.md) contiene el detalle acordado el 12 de noviembre de 2026. Este índice evita reinterpretar decisiones desde el prototipo antiguo.

| Tema | Decisión |
|---|---|
| Identidad | Identificador aleatorio fijo por cuadro preparado por el desarrollador. La API conserva Bearer + `FRAME_TOKEN_HASHES`; SHA-256 deriva el ámbito. Por decisión expresa de Carlos, Firebase permite leer selecciones/medios por URL conocida sin sesión. No hay Firebase Auth ni contraseña técnica. |
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

Pendientes: integración física del token en QR/NFC, primera importación y escucha en Firebase real, firmware/hardware, cola/worker final, límites/calidades, imagen local sin red, limpieza con referencias activas, reanudación tras caída de audio y licencia. Las reglas públicas reales se aplicaron manualmente y se verificaron en esta fase.

## Decisión técnica — 12 de noviembre de 2026

El identificador aleatorio fijo sigue siendo Bearer para la API; el backend compara SHA-256 con `FRAME_TOKEN_HASHES` y deriva ámbitos de RTDB, SQLite, tareas y rutas Storage. Decisión nueva: Carlos acepta expresamente que quien conozca la URL pueda leer la configuración musical publicada y los medios, sin Firebase Auth ni renovación de sesión. Las reglas limitan RTDB a `frames/{sha256}/slots` y Storage a GET de objetos individuales bajo `private/frames/{sha256}/`; listados, tareas y escrituras permanecen denegados. SHA-256 separa rutas, no autoriza el GET público. API Bearer sigue exigiéndose para cambios e importaciones. Credenciales Admin quedan en backend/herramientas privadas. Prueba local con emuladores; reglas reales e importación aún pendientes. No se migra automáticamente la colección antigua porque no se conoce a qué cuadro pertenecen sus datos.

En cada cambio de decisión registrar fecha, problema, decisión y efecto sobre código/documentación. El propietario puede modificar estas decisiones mediante instrucciones nuevas; actualizar la definición para que no quede una contradicción.
