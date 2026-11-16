# Decisiones

La [definición](DEFINICION.md) contiene el detalle acordado el 12 de noviembre de 2026. Este índice evita reinterpretar decisiones desde el prototipo antiguo.

| Tema | Decisión |
|---|---|
| Identidad | El identificador se fija en el enlace y selecciona su ámbito por Bearer; no autentica ni requiere alta. API y cliente directo derivan SHA-256. No hay Firebase Auth ni lista de cuadros. Por decisión expresa de Carlos, Firebase permite leer selecciones/medios por URL conocida sin sesión. |
| Selecciones | Tres huecos, cada uno canción o emisora; sin playlists iniciales. |
| Controles | Tres pulsadores iluminados y rueda. Pulsación corta activa/detiene huecos; botón 1 mantenido 2 s muestra el QR musical durante 20 s; botones 2+3 juntos mantenidos 5 s restablecen solo Wi-Fi tras una cuenta atrás cancelable. La rueda solo ajusta volumen. Los gestos largos/combinados suprimen la acción corta y no se repiten al mantener. |
| Encendido | Imagen decorativa y silencio, recordando volumen. |
| Audio | Streaming directo al ESP32, búfer y sin SD; canción termina y se detiene. |
| Web | Móvil primero, dinámica sin recargas y JavaScript modular; sin React. |
| Escucha web | Audio en el navegador; sin órdenes al cuadro ni volumen remoto. |
| Contenido | Búsqueda YouTube con elección de resultado; Radio Browser para emisoras. |
| Imagen | Decorativa independiente elegida en web; procesamiento servidor y sin original permanente. |
| Sustitución | Preparar antes de publicar; preservar el audio activo y limpiar cuando deje de utilizarse. |
| Tareas | Una importación por cuadro y estado recuperable al volver a la web. |
| Hosting e importador | Web pública en `https://sonoro.zeliuk.xyz`; API en `https://cuadro-sonoro.onrender.com`; RTDB/Storage en Firebase. yt-dlp busca y RapidAPI prepara el audio elegido. No Firebase Hosting ni web alojada en ESP32. |
| Portfolio | Repo público `cuadro-sonoro`, secretos excluidos, demo identificada sin servicios reales. |

Pendientes: verificación independiente y detallada del servicio Render/RapidAPI y del recorrido desde la web pública, escucha humana, firmware/hardware, QR/NFC físicos, operación de cola bajo el requisito de una instancia/worker, límites/calidades, imagen local sin red, limpieza con referencias activas, reanudación tras caída de audio y licencia. Carlos comunica que el backend funciona en Render con RapidAPI; no se aportan aquí logs, métricas ni resultados de recuperación/cancelación. La importación anterior con yt-dlp en Render falló con HTTP 429/403; es antecedente y no bloqueo vigente de descarga mediante RapidAPI. Sigue [PRUEBA_RAPIDAPI.md](PRUEBA_RAPIDAPI.md). La primera importación real y reproducción en Chrome Headless están registradas en [VALIDACION.md](VALIDACION.md).

## Alojamiento de la web — 16 de noviembre de 2026

Carlos decide alojar los estáticos de `web/` en `https://sonoro.zeliuk.xyz`. QR/NFC habituales abrirán ese origen con `#token=<id-cuadro>`. El móvil requiere Internet, pero no la misma Wi-Fi que el cuadro. El ESP32 no aloja la web musical y conserva un portal local separado para configurar/restablecer Wi-Fi. La API permanece en `https://cuadro-sonoro.onrender.com`; `ALLOWED_ORIGINS` permite documentar el origen exacto `https://sonoro.zeliuk.xyz` (sin barra final). El valor no se afirma aplicado en Render. Hosting y backend no intervienen en la reproducción normal: el ESP32 leerá configuración/medios de Firebase y reproducirá audio desde Storage o streams. No se necesita servidor doméstico ni Raspberry Pi por cuadro. Se conservan servidor Bonjour y pruebas locales solo como herramientas de desarrollo. La dirección y flujo están decididos; despliegue, HTTPS, CORS integrado y hardware siguen sin verificación.

## Decisión técnica — 12 de noviembre de 2026

Decisión nueva de Carlos (12 de noviembre de 2026): cualquier identificador válido de 1–128 caracteres ASCII puede crear/recuperar un cuadro sin aprovisionamiento. El identificador no es una credencial; el Bearer se conserva solo como transporte para seleccionar el ámbito. API y cliente Firebase calculan SHA-256 sobre sus bytes UTF-8 para usar `frames/{sha256}`, `frame_states` y `private/frames/{sha256}/...`, conservando las selecciones y medios existentes. No hay usuarios, Firebase Auth ni lista de identificadores autorizados. Cualquier persona que conozca o elija un identificador puede leer y cambiar ese ámbito mediante API. Las reglas públicas Firebase no cambian: RTDB deja leer `slots` y Storage objetos individuales por URL, y bloquean listados y escrituras públicas. Credenciales Admin quedan en backend/herramientas privadas.

En cada cambio de decisión registrar fecha, problema, decisión y efecto sobre código/documentación. El propietario puede modificar estas decisiones mediante instrucciones nuevas; actualizar la definición para que no quede una contradicción.


## Búsqueda yt-dlp y descarga RapidAPI — 16 de noviembre de 2026

Carlos solicita mantener la búsqueda yt-dlp y sustituir Apify por RapidAPI YouTube MP3 para descargar el resultado elegido. Efecto: `POST /search` consulta `ytsearch5`; `POST /imports` recibe el ID seleccionado y RapidAPI devuelve el enlace MP3. La clave RapidAPI queda solo en backend. El frontend ya no expone selector de proveedor y apunta a `https://cuadro-sonoro.onrender.com`; la web se sirve por separado. El secreto RapidAPI y CORS deben configurarse independientemente en Render. No se ha llamado al endpoint ni validado la cuota/descarga real.

## Estado comunicado del backend en Render — 16 de noviembre de 2026

Carlos confirma que el backend funciona en Render con RapidAPI. Se registra como validación manual comunicada por el propietario; esta fase documental no hizo llamadas a Render, RapidAPI, YouTube o Firebase ni recibió métricas o logs para verificar detalles de importación, recuperación, cancelación o estabilidad. El firmware no existe. Los fallos históricos HTTP 429/403 pertenecen a descargas anteriores con yt-dlp y no deben describirse como bloqueo vigente de RapidAPI.

## Primera instalación Wi-Fi y controles — 16 de noviembre de 2026

Por instrucción de Carlos, la primera instalación usa un punto de acceso temporal identificable y protegido por contraseña propia del dispositivo; el QR conecta el móvil a esa red y el asistente local opera sin Internet ni servicios cloud. La contraseña doméstica queda solo en el ESP32. Una caída de Internet no se confunde con credenciales incorrectas ni abre el asistente. El dispositivo muestra después el QR musical generado desde su ID estable. Restablecer Wi-Fi requiere mantener 2+3 juntos 5 s; se cancela al soltar cualquiera y conserva ID, selecciones, imagen y volumen. El botón 1 muestra el QR tras 2 s de pulsación y lo mantiene visible 20 s. Son tiempos acordados, pendientes de validación física. Efecto: definición, arquitectura, estado, plan, guías de firmware y reglas compartidas actualizadas; sin implementación de firmware.
