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
| Hosting | Web estática servida por ESP32 en LAN; QR/NFC usa hostname único mDNS preferido. Móvil ejecuta la web y llama a API Render/Docker; RTDB/Storage en Firebase. No Firebase Hosting. |
| Portfolio | Repo público `cuadro-sonoro`, secretos excluidos, demo identificada sin servicios reales. |

Pendientes: validar Render, escucha humana, firmware/hardware, QR/NFC físicos, cola/worker final, límites/calidades, imagen local sin red, limpieza con referencias activas, reanudación tras caída de audio y licencia. La primera importación real y la reproducción en Chrome Headless están registradas en [VALIDACION.md](VALIDACION.md). Las reglas públicas reales se aplicaron manualmente y no se han modificado en la decisión sobre identificadores.

## Alojamiento de la web — 13 de noviembre de 2026

Carlos confirma que el ESP32 servirá los archivos estáticos de la web dentro de la Wi-Fi doméstica. El QR/NFC abrirá la página en el móvil usando un hostname local único, preferentemente mDNS, para no depender de la IP del router. El navegador del móvil seguirá llamando directamente a Render por HTTPS y usando Firebase según el flujo actual; el ESP32 no proxyfica las operaciones. `localhost` no se usa porque desde el móvil apunta al teléfono. Hay que validar mDNS en móviles/routers reales, prever alternativa si no resuelve y ajustar CORS para el origen local. Esta decisión reemplaza el alojamiento público de la web acordado previamente; hardware, firmware y servicio HTTP están pendientes.

## Decisión técnica — 12 de noviembre de 2026

Decisión nueva de Carlos (12 de noviembre de 2026): cualquier identificador válido de 1–128 caracteres ASCII puede crear/recuperar un cuadro sin aprovisionamiento. El identificador no es una credencial; el Bearer se conserva solo como transporte para seleccionar el ámbito. API y cliente Firebase calculan SHA-256 sobre sus bytes UTF-8 para usar `frames/{sha256}`, `frame_states` y `private/frames/{sha256}/...`, conservando las selecciones y medios existentes. No hay usuarios, Firebase Auth ni lista de identificadores autorizados. Cualquier persona que conozca o elija un identificador puede leer y cambiar ese ámbito mediante API. Las reglas públicas Firebase no cambian: RTDB deja leer `slots` y Storage objetos individuales por URL, y bloquean listados y escrituras públicas. Credenciales Admin quedan en backend/herramientas privadas.

En cada cambio de decisión registrar fecha, problema, decisión y efecto sobre código/documentación. El propietario puede modificar estas decisiones mediante instrucciones nuevas; actualizar la definición para que no quede una contradicción.
