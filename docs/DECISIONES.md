# Decisiones

La [definición](DEFINICION.md) contiene el detalle acordado el 12 de noviembre de 2026. Este índice evita reinterpretar decisiones desde el prototipo antiguo.

| Tema | Decisión |
|---|---|
| Identidad | El identificador se fija en el enlace y selecciona su ámbito por Bearer; no autentica ni requiere alta. API y cliente directo derivan SHA-256. No hay Firebase Auth ni lista de cuadros. Por decisión expresa de Carlos, Firebase permite leer selecciones/medios por URL conocida sin sesión. |
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
| Hosting e importador | La web estática de prueba apunta a `https://cuadro-sonoro.onrender.com`; búsqueda y descarga usan Actors Apify desde backend. Esta integración es experimental y queda pendiente de validación real. RTDB/Storage siguen en Firebase. No Firebase Hosting. |
| Portfolio | Repo público `cuadro-sonoro`, secretos excluidos, demo identificada sin servicios reales. |

Pendientes: prueba real Apify/Render, escucha humana, firmware/hardware, QR/NFC físicos, operación de cola bajo el requisito de una instancia/worker, límites/calidades, imagen local sin red, limpieza con referencias activas, reanudación tras caída de audio y licencia. La importación previa con yt-dlp en Render falló con HTTP 429/403; esta limitación histórica no valida ni invalida por sí sola Apify. Sigue [PRUEBA_APIFY_RENDER.md](PRUEBA_APIFY_RENDER.md). La primera importación real y reproducción en Chrome Headless están registradas en [VALIDACION.md](VALIDACION.md).

## Alojamiento de la web — 13 de noviembre de 2026

Carlos confirma que el ESP32 servirá los archivos estáticos de la web dentro de la Wi-Fi doméstica. El QR/NFC abrirá la página en el móvil usando un hostname local único, preferentemente mDNS, para no depender de la IP del router. El 16 de noviembre se autorizó preparar una prueba de Apify desde Render; la URL de web apunta a ese backend para la prueba. La implementación no se ha desplegado ni validado en servicios reales. Hardware, firmware y acceso desde hostname doméstico siguen pendientes.

## Decisión técnica — 12 de noviembre de 2026

Decisión nueva de Carlos (12 de noviembre de 2026): cualquier identificador válido de 1–128 caracteres ASCII puede crear/recuperar un cuadro sin aprovisionamiento. El identificador no es una credencial; el Bearer se conserva solo como transporte para seleccionar el ámbito. API y cliente Firebase calculan SHA-256 sobre sus bytes UTF-8 para usar `frames/{sha256}`, `frame_states` y `private/frames/{sha256}/...`, conservando las selecciones y medios existentes. No hay usuarios, Firebase Auth ni lista de identificadores autorizados. Cualquier persona que conozca o elija un identificador puede leer y cambiar ese ámbito mediante API. Las reglas públicas Firebase no cambian: RTDB deja leer `slots` y Storage objetos individuales por URL, y bloquean listados y escrituras públicas. Credenciales Admin quedan en backend/herramientas privadas.

En cada cambio de decisión registrar fecha, problema, decisión y efecto sobre código/documentación. El propietario puede modificar estas decisiones mediante instrucciones nuevas; actualizar la definición para que no quede una contradicción.
