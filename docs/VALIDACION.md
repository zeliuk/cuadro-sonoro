# Validación de esta entrega

> Las entradas fechadas siguientes son antecedentes de sus respectivas fases. Decisiones antiguas sobre alojamiento de la web, APIs y proveedores quedaron sustituidas por las actualizaciones más recientes y no son instrucciones vigentes. Para el estado actual, consultar primero [ESTADO.md](ESTADO.md), [DEFINICION.md](DEFINICION.md) y [DESPLIEGUE.md](DESPLIEGUE.md).

## Carga directa de Firebase en el simulador — 20 de noviembre de 2026

Se añadió `firmware/simulator/scripts/launch_firebase.py`: pide el identificador sin mostrarlo y lee una vez los tres registros desde RTDB. Para canciones descarga hasta 2 MiB por JPEG desde Storage. Para radios obtiene el favicon desde la URL HTTPS publicada, valida el host público y cada redirección y limita la respuesta a 2 MiB; el decodificador stb_image ajusta formatos rasterizados a un lienzo cuadrado y genera un icono local si falta/no puede decodificar el logo. El simulador pasa imagen, título y artista a la misma vista LVGL. Las teclas `1`, `2` y `3` activan/cambian/detienen la selección de cada hueco; los huecos vacíos no afectan a la selección activa. El QR usa el identificador consultado. La lectura no pasa por Render, no descarga audio y no modifica Firebase. `scripts/device_client.py` comparte el lector de selección con su comando anterior de descarga de medios.

Verificación: CMake compiló `cuadro-sonoro` en el MacBook Pro Intel usando la configuración existente `firmware/simulator/build-run`. La configuración pública local `firebase/device-config.json` existe, pero no se mostraron sus valores. No se ejecutó la nueva ruta con un identificador ni se consultó RTDB/Storage; quedan pendientes una canción con carátula publicada y su prueba visual. No se ejecutaron tests automáticos ni hubo acceso a Render, Firebase real o hardware en este cambio.

## Primera demo visual LVGL desktop — 20 de noviembre de 2026

Se añadió una app C++/LVGL 9.2.2/SDL2 de 480 × 480 en `firmware/simulator/`. La carátula JPEG local de 320 × 320 se ajusta a la pantalla sin deformarse; `View::showSong()` recibe por separado imagen, título y artista. Noto Sans/TinyTTF muestra las tildes. La franja oscura semitransparente contiene el título largo en dos líneas y el artista debajo. Las imágenes son recursos originales generados para esta prueba; Noto Sans está bajo SIL OFL 1.1, Nayuki QR bajo MIT y stb_image conserva su licencia en su cabecera.

`cmake --build firmware/simulator/build-run --target cuadro-sonoro --parallel 4` completó en macOS Intel `x86_64` con Apple Clang 17, CMake 4.4.5 instalado por pip y SDL2 2.32.10 compilado localmente bajo `/tmp` (no se instaló en el sistema). Homebrew no pudo construir CMake 4.5.1 en este host. El comando interno `--verify-flow /tmp/cuadro-sonoro` completó: reposo inicial; pulsación corta inicia canción; siguiente pulsación vuelve a reposo; tercera inicia de nuevo; mantener 1 durante 2 s muestra QR sin incrementar la acción corta; QR presente tras 19,5 s y expirado a 20,5 s; vuelve a canción. `SDL_RenderReadPixels` guardó capturas BMP inspeccionadas visualmente. También se abrió la ventana SDL interactiva y se capturó su contenido en reposo, canción y QR; confirmados el recorte, el título en dos líneas, las tildes y el retorno tras la expiración. No se escaneó el QR con cámara. No se probó en Apple Silicon/M2. No se usó nube, audio real, placa, red o Firebase.

## Corrección de arranque Homebrew en Apple Silicon — 20 de noviembre de 2026

El usuario reportó que `brew install cmake sdl2` falló con `/usr/local/opt/cmake not present or broken`. El prefijo `/usr/local` corresponde a Homebrew Intel/Rosetta; Apple Silicon usa `/opt/homebrew`. Se actualizó `firmware/README.md` para confirmar `uname -m` y `brew --prefix`, instalar con `/opt/homebrew/bin/brew` y usar prefijo explícito de SDL2 en CMake. Los nuevos comandos no se pudieron verificar en un Mac mini M2; se mantiene como pendiente ejecutar allí toda la secuencia.

## Selección documental de hardware del primer prototipo — 19 de noviembre de 2026

Se incorporó [HARDWARE.md](HARDWARE.md) como referencia única de materiales, esquema propuesto y comprobaciones de banco. Se seleccionaron la Waveshare ESP32-S3-Touch-LCD-4B (SKU 32052), AW9523B IO Expansion Board (SKU 22132), tres pulsadores RGB de ánodo común y 5 V, encoder DQLZV EC11, pomo, cableado, tiras de pines, termorretráctil y alimentación USB. Se enlazó desde la guía de firmware y el índice, manteniendo el croquis visual con una aclaración de que no es el esquema eléctrico. Definición, estado, arquitectura, plan e instrucciones ChatGPT distinguen la selección documental del montaje/validación pendientes.

Revisión documental: el esquema oficial de la 4B y la ficha técnica Awinic AW9523B se consultaron; la página de Waveshare para el módulo AW9523B devolvió HTTP 403 a la consulta automatizada, por lo que su pinout y posibles componentes integrados deben confirmarse directamente en la guía y módulo recibidos. Se dejó explícito que AW9523B arranca con sus puertos configurados como salidas según AD0/AD1, y se marcó la rama 5 V de los aros como pendiente de medición. No se conectó ni energizó hardware, no se ejecutó firmware, no se hicieron mediciones ni pruebas físicas; no se ejecutaron pruebas de software. El esquema es una propuesta documental, no una validación eléctrica.

## Definición documental de Wi-Fi y controles físicos — 16 de noviembre de 2026

Por instrucción de Carlos, se documentó la primera instalación offline: punto de acceso temporal identificable y protegido por contraseña propia, QR de conexión, portal cautivo con dirección local de respaldo aún por determinar, selección/actualización de redes y contraseña doméstica guardada únicamente en el ESP32. Se distinguió la conexión al router del acceso a Internet y se definió que las caídas de red no borran credenciales ni abren el asistente automáticamente. Tras configurar, el cuadro muestra el QR musical generado desde su identificador estable.

Se fijaron los gestos: botón 1 mantenido 2 segundos muestra el QR musical durante 20 segundos sin interrumpir audio; botones 2+3 mantenidos juntos 5 segundos permiten restablecer únicamente Wi-Fi con cuenta atrás cancelable. Se preservan identificador, selecciones, imagen y volumen. La rueda solo ajusta volumen. Se documentaron prioridad de la combinación, supresión de acciones cortas y ausencia de repetición al mantener.

Se actualizaron definición, decisiones, estado, plan, arquitectura, guía de firmware, README, AGENTS e instrucciones ChatGPT. Esta entrega es exclusivamente documental: no se implementó código, no se eligió hardware ni librería, no se instalaron dependencias, no hubo despliegues ni pruebas funcionales/servicios reales. Se ejecutó únicamente `git diff --check` y una revisión estática de referencias/contradicciones y enlaces relativos. Los tiempos, el comportamiento de red y la dirección del portal siguen pendientes de implementar y validar en hardware.

## Actualización documental de arquitectura — 16 de noviembre de 2026

Carlos decide alojar la web estática en `https://sonoro.zeliuk.xyz`; el ESP32 no la sirve. El QR/NFC habitual lleva `#token=<id-cuadro>`. El móvil necesita Internet, pero no la Wi-Fi del cuadro. El ESP32 tendrá un portal local separado para configurar/restablecer su Wi-Fi; la contraseña queda en el dispositivo. Hosting y backend no intervienen en la reproducción normal: el dispositivo leerá configuración/medios de Firebase y reproducirá desde Storage o los streams. Se actualizaron definición, arquitectura, estado, plan, despliegue, configuración, instrucciones ChatGPT y guías asociadas. Además, se añadió `scripts/generate_public_qr.py`, separado del generador Bonjour de desarrollo. Genera `https://sonoro.zeliuk.xyz/#token=<id>` y evita imprimir IDs asignados. Se reemplazaron los dos PNG anteriores ignorados por Git por QR con IDs ficticios que apuntan al dominio público; no corresponden a cuadros reales. Carlos comunica manualmente que el backend funciona en Render con RapidAPI; esto se registra como reporte del propietario y no como comprobación de Codex ni de hardware. El origen CORS requerido es `https://sonoro.zeliuk.xyz` mediante `ALLOWED_ORIGINS`, sin barra final; no se afirma que esté configurado en Render.

Comprobaciones realizadas por Codex en esta fase: revisión de instrucciones, estado de Git y documentación; contraste de URL API versionada y variables CORS con `web/index.html`, `backend/main.py` y `backend/.env.example`; ejecución del generador público para producir dos QR ficticios; revisión de referencias documentales. Se ejecutó `git diff --check` y revisión estática de enlaces relativos/coherencia. No se ejecutaron pruebas funcionales, pruebas Bonjour, navegador o Docker ni llamadas a Render, RapidAPI, YouTube o Firebase; no se consumió cuota ni se cambió configuración remota. El despliegue del hosting, HTTPS, CORS efectivo desde el dominio y recorrido completo quedan pendientes. Hardware y firmware no están validados.



## Sustitución de Apify por RapidAPI — 16 de noviembre de 2026

Por instrucción de Carlos, se eliminó la integración Apify y su selector de frontend. `/search` mantiene la búsqueda yt-dlp; `/imports` usa el endpoint HTTP RapidAPI YouTube MP3 con `RAPIDAPI_KEY` configurada solo en backend. Se añadieron validación HTTPS de enlaces, descarga acotada, conservación de la selección previa y documentación de instalación/operación. El MCP de Codex no se usa como runtime de la aplicación.

No se ejecutaron tests, comprobaciones de sintaxis, Docker ni pruebas del navegador. No se llamó a RapidAPI, YouTube, Firebase ni Render; no se consumió cuota. La respuesta y enlace de descarga RapidAPI, permisos/cuota del plan y funcionamiento Raspberry Pi siguen pendientes de prueba real. El código se preparó tomando como contrato `GET /dl?id=<video_id>` y respuesta JSON con `status="ok"` y `link`, descritos en el material público de la API; confirmar el contrato y los límites del plan antes de importar.

### Primer intento real reportado — enlace MP3 no disponible (antecedente)

Carlos reporta desde Render `HTTP 404` al descargar el enlace devuelto, con el host `alpha.123tokyo.xyz`. Esto indica que la API devolvió un enlace, pero el servidor de medios no encontró el archivo; el `User-Agent` ya se había cambiado antes de este intento. No se registra el enlace completo porque puede incluir datos temporales. El fallo apunta al enlace/servidor de medios del proveedor, no a la configuración de `RAPIDAPI_KEY`. No repetir conversiones hasta confirmar con el proveedor si el host o el enlace están operativos: cada solicitud de conversión puede consumir cuota. No se había validado una importación completa en la fecha de ese reporte. Esta nota es histórica; Carlos comunica después que el backend funciona en Render con RapidAPI, sin detalles de importación incluidos aquí.

Un reporte comunitario específico de `youtube-mp36` describe el mismo patrón 403/404 desde servidores cloud y atribuye el bloqueo a una verificación de usuario en el servidor del archivo; propone añadir el username RapidAPI al `User-Agent` y `X-RUN` con MD5 del username ([referencia](https://billy85276.hashnode.dev/rapidapi)). Se añadió soporte obligatorio para `RAPIDAPI_USERNAME` en el backend. Este workaround no está documentado en la página pública del proveedor ni validado todavía con una conversión real. Configurar el username en local y Render y hacer un único intento solo si se acepta el posible consumo de cuota.

### Reproducción de un MP3 RapidAPI — sonido blanco

Carlos reportó ruido blanco, pero aclaró que el sonido pertenece al inicio de «Chandelier» de Sia. No hay un fallo de audio confirmado. Una captura de la respuesta RapidAPI mostró que `filesize` puede diferir de los bytes descargados; por eso se deja como dato informativo y ya no bloquea la tarea. Se conservan la comprobación del `Content-Length` real y la comparación de duración. No se repitió la conversión ni se probó el cambio.

## Endpoint de web en Render y entorno local — 16 de noviembre de 2026

Se cambió el meta `sonoro-api-base` versionado para que el sitio estático llame a `https://cuadro-sonoro.onrender.com`; el frontend sigue separado y no se aloja desde ese servicio. Se adaptó el `.env` local ignorado por Git: se retiraron variables `APIFY_*` y se guardó `RAPIDAPI_KEY` desde el elemento existente del llavero macOS sin imprimirla. Las variables Firebase locales se conservaron. `render.prototype.yaml` ahora documenta las variables de clave RapidAPI y CORS.

No se modificó el entorno de Render ni se desplegó. Para que el servicio remoto importe, hay que configurar allí `RAPIDAPI_KEY` como secreto y permitir el origen real de la web en `ALLOWED_ORIGINS` o `ALLOWED_ORIGIN_REGEX`; el `.env` local no configura Render. No se probaron peticiones remotas.

## Proveedor inicial yt-dlp — 16 de noviembre de 2026

Tras el reporte de una solicitud que pedía `APIFY_TOKEN` sin querer usar Apify, la interfaz pasa a seleccionar yt-dlp inicialmente. Apify sigue disponible en el selector. La API conserva su valor predeterminado Apify para clientes antiguos que no envíen `provider`; la interfaz actual envía el valor elegido. No se ejecutaron pruebas ni se reinició/reconstruyó el backend en esta edición.

## API local predeterminada en la web — 16 de noviembre de 2026

Por decisión de Carlos, `web/index.html` ahora usa `http://127.0.0.1:8000` como `sonoro-api-base`, en lugar de Render. Se actualizaron README y guías de web, API, pruebas y configuración. Desde el móvil, `127.0.0.1` señala al propio teléfono; para Raspberry Pi/LAN debe configurarse la dirección alcanzable de la API en el HTML servido. La guía Render requiere cambiar temporalmente el meta en una copia local.

No se ejecutaron pruebas ni comprobaciones automáticas en esta edición. No se llamó a Render, YouTube o Firebase.

## Selector de proveedor y descarga local yt-dlp — 16 de noviembre de 2026

Se preparó un selector por importación en la web para conservar Apify y permitir yt-dlp en la máquina que ejecuta la API. El proveedor se incluye en la tarea para mantenerlo al recuperar/reintentar; ambas opciones pasan por la validación de MP3/duración, portada, Storage y publicación existentes. yt-dlp convierte a MP3 con FFmpeg y usa el runtime JavaScript instalado en el host. Se actualizaron el contrato de `/imports`, OpenAPI generado por FastAPI, guía de API, instrucciones locales, definición, estado, configuración y README.

Esta edición no se ha ejecutado ni probado todavía. No se ejecutaron tests, comprobaciones de sintaxis, build Docker ni pruebas de navegador; no hubo solicitudes a YouTube, Apify, Render o Firebase. La compatibilidad de yt-dlp en macOS/Raspberry Pi, el progreso/cancelación durante descargas y la publicación real siguen pendientes. Próximo paso: configurar una API local y Firebase de prueba, seleccionar un resultado autorizado y verificar primero `provider=yt_dlp`, preservación ante fallo y reintento; después contrastar que `provider=apify` conserva su flujo.

## Búsqueda yt-dlp y descarga Apify — 16 de noviembre de 2026

Se restauró la búsqueda plana inicial con yt-dlp (`ytsearch5`) y se mantuvo Apify únicamente en la importación del MP3 seleccionado por ID. `/search` no requiere `APIFY_TOKEN` ni crea runs de Actors. Se añadió yt-dlp/yt-dlp-ejs a dependencias y Deno a la imagen Docker; se retiraron las variables de configuración exclusivas de la antigua búsqueda Apify del ejemplo y del `.env` local sin mostrar sus valores. Se actualizaron API/OpenAPI, definición, estado, configuración y procedimiento de descarga.

Verificaciones: `pytest backend/tests scripts/tests -q` (**65 passed**); `python -m compileall -q backend scripts`; `node --check web/app.js`; `git diff --check`; `docker compose config --quiet`. La construcción de la imagen no pudo comprobarse porque el daemon Docker no está activo. La búsqueda fue verificada con mocks; no se llamó a YouTube, Apify, Render ni Firebase. La búsqueda desde Render y la descarga real siguen pendientes.

Durante la construcción remota, el instalador de Deno descargado con `curl` terminó con código 56. Se sustituyó por la copia del binario desde la imagen oficial `denoland/deno:bin-2.9.8` en una etapa multi-stage. La nueva construcción todavía debe confirmarse en Render.


## Endpoint API predeterminado local — 16 de noviembre de 2026

Por decisión de Carlos, `web/index.html` deja de apuntar a Render y usa `http://127.0.0.1:8000`, la API Docker local del Mac. Render se descarta para importaciones de YouTube por los HTTP 429/403 documentados. El worker Docker local y Render podían compartir la cola en Firebase RTDB cuando ambos tenían acceso al mismo proyecto; el worker local podía consumir tareas enviadas a Render. No se debe ejecutar esa configuración compartida como solución de alojamiento para el producto.

Se actualizaron definición, estado, decisiones, arquitectura, configuración, guías operativas e instrucciones del proyecto ChatGPT. La URL loopback se limita al navegador del mismo Mac; no sirve desde un móvil ni desde el ESP32. Elegir una API accesible desde la LAN queda pendiente.

Verificaciones de esta edición: `node --check web/app.js` y `git diff --check`. No se ejecutaron tests ni pruebas de API/Docker; el daemon Docker no estaba disponible al revisar el estado. No se hicieron llamadas a Render/YouTube/Firebase ni pruebas en móvil.

## Decisión de alojamiento web sustituida — 13 de noviembre de 2026

Decisión histórica, sustituida el 16 de noviembre de 2026: entonces se propuso que el ESP32 sirviera la web en la red doméstica mediante hostname mDNS. La decisión vigente aloja la web en `https://sonoro.zeliuk.xyz`; el ESP32 no aloja la web musical. El firmware y hardware nunca se implementaron en esa fase.

Fecha: 12 de noviembre de 2026. Entorno de comprobación: Linux, Python 3.12.14 y un entorno virtual limpio. El usuario continuará en macOS; no se ha ejecutado la instalación en su Mac.

| Comprobación | Resultado |
|---|---|
| Instalar `backend/requirements-dev.txt` | Correcto en entorno virtual limpio; incluye dependencias de ejecución. |
| Tests de backend y control de repositorio | 10 superados, con proveedores simulados y datos temporales. |
| Arranque y parada Uvicorn con `.env` local | Correctos, sin configurar Firebase. |
| HTTP local | 17 comprobaciones: health, autorización, estado, documentación, metadatos de radio sintética, vaciado y errores esperados. |
| Catálogo API frente a OpenAPI real | Coinciden las ocho operaciones; exportación en `openapi.prototype.json`. |
| `node --check web/app.js` | Correcto. |
| Diseño conservado | HTML, CSS y JS idénticos al ZIP original recuperado. |
| Firebase Hosting | Retirado de `firebase.json`. La intención histórica de servir la web desde el ESP32 fue sustituida el 16 de noviembre de 2026 por el hosting HTTPS público de Carlos. |
| Enlaces internos de documentación | Comprobados. |
| Control básico de publicación | 56 archivos preparados sin hallazgos de sus patrones; no es una auditoría del historial. |

La radio sintética utiliza `example.org` y solo verifica el contrato y los registros, no reproduce una emisora real. La búsqueda se probó únicamente con entrada inválida para verificar 422. La importación se probó sin Storage para verificar 503; la ejecución completa se cubre solo con mocks existentes.

El conjunto de dependencias resuelto produce un aviso de deprecación de Starlette/TestClient sobre HTTPX. Las pruebas pasan; fijar y revisar compatibilidad de dependencias al preparar la base reproducible de despliegue.

## Revisión local en macOS — 12 de noviembre de 2026

Se preparó `.venv` con `uv` y CPython 3.12.15, instalando `backend/requirements-dev.txt`. La revisión se ejecutó sin variables ni credenciales de Firebase; `backend/.env` fue generado localmente y no se mostró ni versionó.

| Comprobación | Resultado |
|---|---|
| `env -u FIREBASE_DATABASE_URL -u FIREBASE_STORAGE_BUCKET -u FIREBASE_SERVICE_ACCOUNT_JSON -u GOOGLE_APPLICATION_CREDENTIALS .venv/bin/python -m pytest backend/tests scripts/tests -q` | 10 pasaron. Aviso de deprecación de Starlette/TestClient con HTTPX. |
| `.venv/bin/python -m compileall -q backend scripts` | Correcto. |
| `node --check web/app.js` | Correcto. |
| `python scripts/check_project.py` | Python 3.12 y dependencias disponibles; FFmpeg, ffprobe y Deno ausentes; Docker y Node disponibles. |
| Demo en `127.0.0.1:5173` | HTML, JS y CSS respondieron 200. No se hizo comprobación interactiva en un navegador. |
| API local en `127.0.0.1:8000` | Health 200; `/state` 401 sin token y 200 con token local; estación sintética 200, media 200, vaciado 200 y media 404; importación sin Storage 503. Procesos detenidos al terminar. |

La radio era una URL sintética `example.org`; no se descargó contenido. No se validaron Firebase, YouTube, Render, Docker Compose ni hardware. FFmpeg y Deno faltan, por lo que no se puede ejecutar aquí una importación real. La navegación manual y la validación móvil siguen pendientes.

La guía de endpoints se contrastó con las ocho rutas implementadas y sus respuestas locales. Estas comprobaciones son la revisión de fase 0, anterior al cambio de fase 1 que se registra a continuación.

## Checkpoints de diagnóstico para importaciones — 13 de noviembre de 2026

Se añadieron mensajes `import_checkpoint` al worker para marcar búsqueda y validación de metadatos, descarga, conversión, preparación de portada, subida a Firebase, publicación y limpieza. El fallo registra etapa, clase de excepción y detalle redactado; se sustituyen URLs, identificadores del cuadro/tarea y rutas temporales. La guía del backend y el catálogo API indican cómo localizar estos mensajes en la terminal local o en **Logs** de Render.

No se ejecutó la suite de pruebas para esta revisión. El código de checkpoints sí se desplegó en Render; los nuevos logs se documentan en las dos pruebas siguientes.

## Prueba local con yt-dlp prerelease — 13 de noviembre de 2026

Para comprobar si había una corrección posterior al estable, la imagen Docker instaló `yt-dlp 2026.11.4.232659.dev0` y mantuvo `yt-dlp-ejs 0.8.0` con Deno 2.9.8. La consulta de metadatos de la misma selección que fallaba en Render terminó correctamente dentro de esa imagen (`duration` presente). No se descargó audio, no se subieron archivos ni se accedió a Firebase. El contenedor Compose habitual no se recreó; solo se construyó la imagen y se ejecutó un contenedor efímero sin dependencias.

El resultado local indica que el prerelease puede corregir la extracción desde esta red, pero no desde Render. La versión prerelease fue una prueba y no queda aprobada como versión definitiva.

## Prueba de yt-dlp prerelease en Render — 13 de noviembre de 2026

Tras desplegar el prerelease, el intento volvió a fallar en `source_lookup`: yt-dlp registró HTTP 429 al pedir la página y varios HTTP 403 al consultar la API del reproductor. Los logs confirman que cargó `nightly@2026.11.04.232659`, EJS 0.8.0 y Deno 2.9.8. El POST de importación fue aceptado, pero no se alcanzó la descarga, conversión ni subida de medios; la limpieza terminó correctamente.

La comparación local/Render demuestra que actualizar yt-dlp no basta: local obtuvo los metadatos con esa misma prerelease y Render recibió límites/prohibiciones de YouTube. Esto apunta a una restricción o limitación de solicitudes desde la red/IP de salida de Render; el log no establece su causa administrativa exacta. Se retiró la instalación automática de prereleases del Dockerfile y se conserva la versión estable indicada por `requirements.txt`.

## Límites de la evidencia

- Docker y Deno no estaban disponibles en este entorno: no se ha construido la imagen ni ejecutado Compose.
- No se ha accedido a servicios Firebase reales ni descargado contenido de YouTube en esta comprobación.
- No se ha desplegado en Render, Firebase ni el servidor de Carlos.
- En esta revisión de fase 0 todavía no se había implementado aislamiento por cuadro. Radio Browser, imagen decorativa y firmware siguen pendientes.
- No se ha hecho una nueva revisión visual en navegador; se conservan los archivos visuales originales sin cambios. La validación móvil del producto final corresponde a su fase.

Las guías de Docker, Firebase CLI y despliegue son recetas para ejecutar/validar en el entorno correspondiente, no pruebas de despliegue realizadas. Actualizar este documento con cada hito real y registrar errores de forma redactada.

## Primer cambio de fase 1 — 12 de noviembre de 2026

Se implementó el contrato Bearer por cuadro: el backend usa SHA-256 para derivar el ámbito de RTDB/SQLite, tareas y rutas nuevas de Storage; no guarda el token original ni migra los registros del prototipo global. La web conserva su estructura visual y ahora identifica la credencial como token del cuadro. Su incorporación automática a QR/NFC todavía no existe.

| Comprobación | Resultado |
|---|---|
| Tests backend/scripts con variables Firebase retiradas | 13 pasaron, incluidos identificadores previos y separación entre cuadros, límite de una tarea activa por cuadro, aislamiento de SQLite heredado; la allowlist usada entonces fue retirada en la actualización descrita al final de este documento. Un aviso de deprecación de Starlette/TestClient con HTTPX. |
| `compileall` y `node --check web/app.js` | Correctos. |
| Web estática tras cambiar la etiqueta del token | HTML, JS y CSS respondieron 200. No se hizo revisión visual móvil; CSS y estructura no cambiaron. |
| API local y Bearer | En esa revisión, la versión anterior aceptaba solo los identificadores entonces configurados y rechazaba otros. La política actual permite cualquier identificador que cumpla el formato documentado en la actualización final. |
| Importación sin Storage | 503 esperado, sin crear tarea. |
| OpenAPI exportado | Ocho rutas y esquemas actualizados en `openapi.prototype.json`; los endpoints privados documentan seguridad y errores principales. |

Estas pruebas usan SQLite temporal y URLs sintéticas. No prueban Firebase RTDB/Storage reales, descargas de YouTube, Docker, Render, acceso ESP32 ni enlaces QR/NFC. No se validó visualmente el cambio de texto en distintos tamaños de pantalla; no se modificaron CSS ni estructura.

## Enlace de acceso por cuadro — 12 de noviembre de 2026

La web acepta `https://dominio/#token=<identificador>`. El valor se recoge en el navegador, se conserva en `sessionStorage` de la pestaña y se quita de la barra sin navegar de nuevo. Las operaciones lo transportan mediante `Authorization: Bearer`. Cambiar de enlace aborta solicitudes del contexto anterior y vacía el estado visible. Identificador ausente queda bloqueado; la demo continúa siendo una elección explícita. El límite de 32 caracteres mencionado en estas comprobaciones históricas fue retirado después.

| Comprobación | Resultado |
|---|---|
| `node --check web/app.js` | Correcto. |
| Tests locales backend/scripts, Firebase env retiradas | 13 pasaron; un aviso conocido de deprecación Starlette/TestClient con HTTPX. |
| `python -m compileall -q backend scripts` | Correcto. |
| Navegador Chrome headless, web estática y FastAPI local con SQLite temporal | Bloqueo inicial sin identificador; guardar URL sin identificador no abrió demo; fragmento eliminado sin navegación; la petición `/state` incluyó Bearer; recarga conservó acceso; el cambio entre dos IDs aisló el estado; la demo permaneció explícita. La prueba de rechazo a IDs no registrados correspondía a una política anterior, sustituida por la decisión documentada al final. |
| Interfaz móvil a 390 × 844 CSS px | `innerWidth` 390 y `scrollWidth` 390, sin desbordamiento horizontal. No se probó en un móvil físico. |

Los dos cuadros y el token rechazado eran datos ficticios en una base SQLite temporal. No se usaron credenciales ni servicios Firebase reales. El endpoint local se permitió mediante CORS solo para el origen temporal de la prueba. La prueba no valida QR impreso, NFC, hosting ni una integración real con Firebase/Render. No se comprobó visualmente en un dispositivo físico.

## Reproducir los checks

Desde la raíz, con `.venv` activado:

```bash
env -u FIREBASE_DATABASE_URL -u FIREBASE_STORAGE_BUCKET -u FIREBASE_SERVICE_ACCOUNT_JSON -u GOOGLE_APPLICATION_CREDENTIALS python -m pytest backend/tests scripts/tests -q
python -m compileall -q backend scripts
node --check web/app.js
```

El recorrido HTTP manual está en [PRUEBA_API.md](PRUEBA_API.md). El esquema se puede actualizar desde una API local arrancada con `curl -sS http://127.0.0.1:8000/openapi.json -o docs/openapi.prototype.json`, revisando el diff junto a `API.md` antes de commit.

## Lectura pública por URL conocida — 12 de noviembre de 2026

Carlos decidió que la configuración publicada y los medios sean legibles sin sesión si se conocen sus URLs. El identificador sigue siendo Bearer de la API y SHA-256 separa registros/rutas, pero no se considera autorización de lectura Firebase. RTDB limita el GET público a `frames/{sha256}/slots`; raíz, listado de cuadros, `jobs` y escrituras quedan denegados. Storage permite GET de objeto bajo `private/frames/{sha256}/`, sin sesión ni URL firmada temporal; listar y escribir siguen denegados. Los cambios e importaciones pasan por API usando el identificador solo para seleccionar ámbito; no hay autenticación de usuario.

Desde la raíz, en macOS con `.venv`, Node 22 y Java 17, se ejecutó Firebase CLI 14.22.0 vía `npx`:

```bash
npx --yes firebase-tools@14.22.0 emulators:exec --only database,storage --project demo-sonoro-device --log-verbosity=QUIET 'source .venv/bin/activate && python scripts/test_device_access.py'
```

Resultado `PASS`: lectura directa RTDB/Storage sin sesión; configuración y medios separados en dos identificadores; rechazo de listado raíz, `jobs`, listados Storage y escrituras públicas; el cliente descargó ambos medios con la API detenida. Datos aleatorios/temporales en emuladores `demo-*`; no se usaron credenciales reales.

También pasó `env -u FIREBASE_DATABASE_URL -u FIREBASE_STORAGE_BUCKET -u FIREBASE_SERVICE_ACCOUNT_JSON -u GOOGLE_APPLICATION_CREDENTIALS .venv/bin/python -m pytest backend/tests scripts/tests -q`: 16 tests, con el aviso conocido de deprecación Starlette/TestClient con HTTPX. `compileall`, `node --check web/app.js` y `git diff --check` pasaron. Tests de API y transacción simulada confirman que un primer GET autorizado crea estado y los siguientes reutilizan el registro; `/media` forma URLs Storage directas.

No se desplegaron reglas, no se modificó Firebase real, no se activó facturación ni se ejecutó una importación real. Los emuladores verifican las reglas locales, no su publicación ni la disponibilidad de medios cargados en un proyecto real. El firmware no existe; la validación de audio en hardware queda pendiente.

Referencias oficiales consultadas: [GET RTDB por REST y reglas públicas](https://firebase.google.com/docs/database/rest/retrieve-data), [métodos get/list de Security Rules Storage](https://firebase.google.com/docs/storage/security/core-syntax) y [autenticación requerida solo cuando la regla la exige](https://firebase.google.com/docs/reference/rest/database). Comandos completos y URLs ficticias están en [firebase/README.md](../firebase/README.md).

## Conexión local al proyecto Firebase real — 12 de noviembre de 2026

Se actualizó el `backend/.env` ignorado por Git sin reemplazar el resto de sus variables. Se configuró Application Default Credentials mediante un archivo de cuenta de servicio; `FIREBASE_SERVICE_ACCOUNT_JSON` quedó vacío. El JSON local existe, es válido y su `project_id` coincide con el proyecto esperado. No se imprimió ni copió al repositorio. `firebase/device-config.json` también se completó con la URL RTDB y el bucket públicos, y su forma coincide con la que consume `scripts/device_client.py`.

| Comprobación contra servicios reales | Resultado |
|---|---|
| FastAPI `/state` con autorización temporal generada solo en memoria, usando el Admin SDK del archivo local | RTDB respondió con estado vacío; el registro temporal se eliminó y se confirmó su ausencia. No se consultaron ni modificaron selecciones existentes. |
| Primeras consultas de metadatos y subida temporal a Storage | Respondieron con HTTP 404. No se concluyó que faltara configurar el producto y no se creó ningún recurso. |
| Comprobación repetida de configuración, metadatos, subida, descarga y eliminación | Correcta: el proceso cargó el bucket previsto; el JSON de credencial y el proyecto de Admin coinciden. La lectura de metadatos y el ciclo de objeto temporal pasaron; después de borrar se confirmó que el objeto ya no existe. No se cambió el bucket, reglas ni facturación. |
| Reglas públicas y cliente de dispositivo | Pendiente: no se desplegaron reglas; la lectura directa sin sesión no se probó contra el proyecto real. |

La primera respuesta 404 no se reproduce en la comprobación repetida; no se atribuye una causa sin evidencia. Los emuladores verificaron anteriormente lectura pública, rechazo de listados/escrituras y separación entre cuadros. Eso no sustituye la validación de reglas contra Firebase real. En esa fase se había configurado una lista de IDs para las operaciones de API; la decisión actual elimina ese requisito y permite que cualquier identificador válido cree o recupere su ámbito.

La prueba real utilizó un registro aleatorio temporal fuera de selecciones y verificó su limpieza. No se ejecutaron importaciones de YouTube, no se tocaron reglas ni otros recursos Firebase y no se incluyeron rutas personales o credenciales en esta documentación.

## Preparación y validación de reglas del cuadro de prueba — 12 de noviembre de 2026

Se reutilizó el identificador existente, sin imprimirlo, en `secrets/frame-test-token.txt` (ignorado por Git). En esa etapa se configuró su hash como alta previa; esa configuración ya no se usa y se eliminó. Antes de llamar a la API se confirmó que RTDB no tenía cuadros ni tareas previas.

| Comprobación | Resultado |
|---|---|
| Reglas locales con emuladores Database y Storage | `PASS`: leer `frames/{sha256}/slots` y descargar objetos individuales; listar `/frames`, leer `jobs`, listar Storage y escribir públicamente fueron rechazados. El cliente descargó medios separados de dos cuadros. Emuladores detenidos al terminar. |
| API local contra RTDB real | `GET /state` con el identificador previamente configurado: 200 y estado vacío. Entonces, un ID sin alta respondía 401. El cambio actual elimina esa restricción; no se requiere alta para leer o crear estado. |
| Despliegue real de reglas | Firebase CLI no pudo publicarlas por problemas de autenticación/permisos. Carlos aplicó manualmente las reglas locales de RTDB y Storage en Firebase Console. La comprobación de abajo confirma el comportamiento efectivo de las reglas aplicadas. |
| Configuración pública directa desde ordenador contra Firebase real | Correcta: el cliente leyó `slots` y descargó el archivo de Storage en un proceso separado sin credenciales ni sesión; la API local estaba detenida. |

Desde la raíz del repositorio, el comando completo intentado para desplegar solo estos dos servicios fue:

```bash
npx --yes firebase-tools@14.22.0 deploy --only database,storage --project cuadro-sonoro --non-interactive
```

Este es el comando CLI que se intentó desde la raíz, aunque el propietario aplicó después las reglas manualmente. No se seleccionaron Firestore, Hosting, Auth ni Functions. El CLI falló antes de publicar: primero por credenciales OAuth caducadas y luego, usando ADC aislado, por falta de permisos como `serviceusage.services.get`, `firebase.projects.get`, `firebasedatabase.instances.update`, `firebaserules.rulesets.create`, `firebaserules.releases.create` y `firebaserules.releases.update`. No hubo despliegue por CLI. La referencia oficial explica que `--only` limita los servicios y que el despliegue reemplaza las reglas existentes de cada servicio seleccionado: [Firebase CLI](https://firebase.google.com/docs/cli#deploy-specific-firebase-services).

Tras la aplicación manual, se volvió a preparar solo el cuadro de prueba con un registro `slots`, una tarea interna ficticia y un objeto mínimo bajo el prefijo de ese cuadro. Con la API detenida, un proceso independiente sin variables de cuenta ni cabeceras de sesión leyó la configuración, descargó el archivo exacto mediante `scripts/device_client.py` y comprobó los rechazos:

| Petición pública | Resultado real |
|---|---|
| RTDB `frames/{sha256}/slots.json` | 200, configuración de prueba leída. |
| Descarga de un objeto individual de Storage | 200, bytes coincidentes con el fixture. |
| RTDB `/frames.json`, `frames/{sha256}/jobs.json` y escritura de prueba | 401. |
| Listado y escritura de prueba en Storage | 403. |

El contenido de audio era solo un fixture de bytes, no un MP3 reproducible. El estado del cuadro y los objetos bajo el prefijo temporal se eliminaron; la comprobación administrativa final confirmó que el registro no existe y el prefijo está vacío. Un intento de borrado del objeto de escritura denegada respondió 404 porque no se llegó a crear; se confirmó después que no quedó ningún archivo.

La API se probó desde la raíz con:

```bash
source .venv/bin/activate
python -m uvicorn backend.main:app --env-file backend/.env --host 127.0.0.1 --port 8000 --workers 1
```

La credencial permite al Admin SDK usar RTDB y Storage, pero no da a Firebase CLI los permisos de publicación necesarios. El identificador de prueba permanece en `secrets/frame-test-token.txt`, ignorado por Git. Para abrirlo localmente sin imprimir el enlace, sigue el procedimiento de portapapeles descrito en [PRUEBA_API.md](PRUEBA_API.md). En esta validación histórica no se hicieron importaciones de YouTube ni se dejaron registros u objetos remotos de prueba; la prueba de descarga no validaba un MP3 ni la reproducción en navegador.

## Ajuste de contexto compartido

Las instrucciones de ChatGPT se trasladaron al archivo versionado `docs/INSTRUCCIONES_CHATGPT.md`. Se actualizaron las referencias, la definición y la regla de mantenimiento en AGENTS.md. Cambio documental; comprobados enlaces y contenido del ZIP, sin modificar lógica ni repetir pruebas de ejecución.

## Primera importación real y reproducción web — 12 de noviembre de 2026

Trabajo ejecutado desde la raíz `cuadro-sonoro/` en macOS. El árbol partió limpio en `8252c0a`. Docker Desktop estaba activo: Docker 28.0.4 y Docker Compose 2.34.0-desktop.1. No se usaron Firebase CLI, emuladores, proveedores simulados ni Render en esta fase; tampoco se desplegaron reglas ni se cambió facturación.

### Imagen y credencial

Se comprobó la configuración y construyó la API:

```bash
docker --version
docker compose version
docker compose config --quiet
docker compose build api
docker compose run --rm --no-deps api sh -lc 'ffmpeg -version | head -n 1; ffprobe -version | head -n 1; deno --version; yt-dlp --version; test -r "$GOOGLE_APPLICATION_CREDENTIALS" && echo credencial_montada_legible'
```

Resultado dentro del contenedor: FFmpeg 7.1.5, ffprobe 7.1.5, Deno 2.9.8 y yt-dlp 2026.10.26. La credencial se mantuvo en la ruta nativa existente de macOS en `backend/.env`; se creó su copia privada `secrets/firebase.json` con permisos locales restringidos. `compose.yaml` monta `secrets/` de solo lectura y establece únicamente dentro del servicio `GOOGLE_APPLICATION_CREDENTIALS=/run/secrets/firebase.json`. No se imprimió ni versionó el JSON. La alternativa `FIREBASE_SERVICE_ACCOUNT_JSON` permaneció vacía.

### API, búsqueda e importación

Los puertos 8000 y 5173 estaban libres; no había procesos locales previos en escucha. Desde la raíz:

```bash
docker compose up -d
docker compose ps
curl -fsS http://127.0.0.1:8000/health
```

La API y la web quedaron arriba en `127.0.0.1:8000` y `127.0.0.1:5173`. `/health` devolvió `ok=true`, `storage_configured=true` y `durable_state=true`; esas banderas por sí solas no prueban permisos. Se leyó primero `/state` con el token privado del cuadro: HTTP 200, cero selecciones y cero tareas previas.

La búsqueda real `Kevin MacLeod` + `Carefree` devolvió cinco resultados. Se eligió expresamente el tercer resultado, «Carefree» (canal Kevin MacLeod, 206 s; identificador de YouTube `qapK8Gx6ZTo`), no el primer candidato. El POST real a `/imports` para el hueco 0 respondió 202. El estado persistido informó `downloading`, `processing`, `uploading` con contadores reales de subida (7, 31, 55, 79) y finalmente `ready`, 100, `estimated=false`. Los contadores corresponden a bytes de la subida reanudable, no a una estimación global. La selección previa estaba vacía y solo se publicó tras completar audio e imagen. No hay logs de progreso inventado.

### Firebase y archivos publicados

Se consultó el `slots` público de RTDB sin sesión y se comparó con el estado autenticado de la API: `id`, `audio_key` e `image_key` de `slot-0` coincidieron. `/media/0` devolvió 200. Los GET directos de Storage se hicieron sin cabecera de autorización:

| Objeto | Resultado | Verificación |
|---|---|---|
| Audio | HTTP 200, `audio/mpeg`, 3.283.244 bytes | ffprobe: MP3, 48 kHz, estéreo, 205,176 s. |
| Imagen | HTTP 200, `image/jpeg`, 12.027 bytes | Pillow decodificó JPEG correctamente. |

En la validación inicial los medios permanecieron bajo la selección publicada para que Carlos los escuchara; se eliminaron después al retirar ese favorito. No se copiaron URLs de Storage ni el identificador del cuadro a esta documentación.

### Reproductor web

En la versión anterior de la interfaz, la web local se abrió en Chrome Headless 157 y se configuró desde el diálogo de conexión con el endpoint local antes de entrar mediante el token de prueba en el fragmento. Ese diálogo se retiró después: la reproducción técnica previamente observada sigue siendo evidencia de ese commit de UI, no una nueva prueba del flujo actual sin popup. Se activó el botón de prueba del hueco 0. El elemento de audio alcanzó `readyState=4`, detectó 205,14 s, quedó reproduciendo con `currentTime=1,12 s`, mostró el reproductor y no registró error multimedia ni error de consola. El avance se observó después del clic, sin usar autoplay al arrancar la página. Esto demuestra decodificación y avance en el navegador; **no demuestra que una persona haya oído el sonido**. Hardware y altavoz no existen todavía.

Durante la primera pasada apareció un 404 de `/favicon.ico`; `web/index.html` ahora declara un icono de datos vacío para que la consola local no reporte esa petición fallida. Repetida la reproducción tras ese ajuste: consola y multimedia sin errores. El ajuste no cambia la estética.

### Revisión posterior y acceso local de Carlos

Para revisar estado sin imprimir el token, desde la raíz se puede ejecutar:

```bash
source .venv/bin/activate
python - <<'PY'
from pathlib import Path
import requests

token = Path('secrets/frame-test-token.txt').read_text(encoding='utf-8').strip()
headers = {'Authorization': 'Bearer ' + token}
state = requests.get('http://127.0.0.1:8000/state', headers=headers, timeout=30).json()
slot = state['slots']['slot-0']
job = state['jobs'][slot['id']]
print('selección:', slot['title'], '—', slot['artist'])
print('tarea:', job['status'], 'duración:', slot['duration'], 's')
PY
```

En el entorno donde se ejecutó esta fase, `docker compose up -d` sigue dejando API y web disponibles. Para abrirlo desde el mismo Mac sin publicar el identificador: visitar `http://127.0.0.1:5173`, guardar `http://127.0.0.1:8000` como «Servicio real» sin token y luego copiar el enlace mediante la receta `pbcopy` de [PRUEBA_API.md](PRUEBA_API.md). Pegar el contenido del portapapeles en la barra local del navegador; el fragmento se consume y se elimina. Pulsa el control «Probar en el móvil». No compartas el enlace, capturas con él ni las URLs directas de Storage.

### Límites y próximos pasos

- Comprobado con servicios reales: búsqueda/descarga de YouTube, Docker, RTDB, Storage, publicación y lectura sin sesión según las reglas existentes, además del reproductor Chrome Headless.
- No probado con servicios reales de alojamiento: Render, continuidad al cerrar/reiniciar procesos y rendimiento desde su red. El worker sigue dentro de un único proceso y no ofrece garantía de recuperación fiable.
- No probado con persona: escucha audible subjetiva. No probado con hardware: firmware, ESP32, streaming al dispositivo, botones, pantalla o altavoz.
- No se provocó un fallo de importación sobre la selección real ni se borraron medios. La limpieza de reemplazos/huérfanos sigue sin implementar; borrar el hueco por API no es limpieza de Storage.
- En la fase de importación se conservó el hueco 0 para escucha. Después, a petición de Carlos, ese favorito se retiró junto con audio e imagen en Storage. Compose queda arriba en este Mac.

### Checks finales del repositorio

Desde la raíz, con `.venv` activado y retirando explícitamente el entorno Firebase de los tests aislados:

```bash
env -u FIREBASE_DATABASE_URL -u FIREBASE_STORAGE_BUCKET -u FIREBASE_SERVICE_ACCOUNT_JSON -u GOOGLE_APPLICATION_CREDENTIALS .venv/bin/python -m pytest backend/tests scripts/tests -q
.venv/bin/python -m compileall -q backend scripts
node --check web/app.js
docker compose config --quiet
git diff --check
```

Resultado: 16 tests pasaron; `compileall`, comprobación JS, Compose y diff pasaron. Pytest conserva un aviso conocido de deprecación de Starlette/TestClient con HTTPX. `scripts/check_public_repo.py --staged` no se ejecutó porque no se preparó ningún commit ni se añadieron cambios al índice. El JSON privado, `.env` y token permanecen ignorados por Git.

## Identificador sin alta previa — 12 de noviembre de 2026

Se aplicó la nueva intención de Carlos: el valor de `#token` es un identificador, no una credencial. No hay usuarios, Firebase Auth ni lista de IDs permitidos. Se conserva `Authorization: Bearer` para transportar el identificador sin reescribir las llamadas; cualquier cliente que lo conozca puede operar en ese ámbito mediante API. Se validan de 1 a 128 caracteres ASCII: letra o número inicial, seguidos de letras, números, guion o guion bajo. API y lector directo importan una sola función que calcula SHA-256 de los bytes UTF-8; las rutas Firebase existentes no cambian.

Desde la raíz se reconstruyeron y arrancaron únicamente los servicios locales:

```bash
docker compose config --quiet
docker compose up --build -d
docker compose ps
curl -fsS http://127.0.0.1:8000/health
```

Antes de la primera llamada, la consulta administrativa de RTDB confirmó que `mi-cuadro-prueba` y `otro-cuadro-prueba` no tenían registros. No se imprimió el identificador antiguo ni ninguna ruta/hash real.

| Comprobación | Resultado |
|---|---|
| API aislada con SQLite temporal | `mi-cuadro-prueba` pasó de ausente a `GET /state` 200 con `slots`/`jobs` vacíos; una segunda llamada recuperó el mismo estado. Un registro sintético se recuperó después por el mismo ID; el segundo ID obtuvo un estado aparte. Se retiró solo el registro sintético creado durante la prueba y el primer ID volvió a quedar vacío. |
| Firebase real | La API creó ambos IDs cortos sin alta previa. El cliente directo leyó el slot de prueba bajo el mismo SHA-256; después de retirar el registro sintético, la lectura pública quedó vacía. En aquella comprobación el identificador existente seguía devolviendo «Carefree» y sus referencias `audio_key`/`image_key`; se retiraron después en la validación de limpieza definitiva. |
| Enlace directo en Chrome Headless | Se abrió `http://127.0.0.1:5173/#token=mi-cuadro-prueba` sin tocar ajustes. La descripción histórica atribuía la respuesta a API local, pero el HTML versionado apunta a Render; por ello no se conserva esa atribución como verificada. Se observaron tres huecos vacíos, limpieza del fragmento, ID en `sessionStorage`, demo oculta y consola sin errores. |

### Sin conexión manual en la web — 12 de noviembre de 2026

Se retiraron el engranaje y el diálogo que pedían elegir modo, URL de API o identificador. Para cuadros reales, el enlace es el único dato que recibe el usuario; el navegador utiliza `https://cuadro-sonoro.onrender.com` desde `meta[name="sonoro-api-base"]`. La demo sigue disponible como modo explícito con el botón «Probar demostración» cuando no hay un cuadro activo. `node --check web/app.js`, `git diff --check` y `GET /health` pasaron. Los contenedores API y web responden en `127.0.0.1:8000` y `127.0.0.1:5173`. No se repitió Chrome en esta edición: no hay un ejecutable Chrome/Chromium en el PATH de este entorno; la reproducción anterior queda registrada arriba como validación previa.

### Eliminación definitiva de medios sin referencias — 12 de noviembre de 2026

Se actualizó el `DELETE /slots/{slot}`: retira la selección, detiene el reproductor local si está usando esa canción y elimina de Storage los objetos del cuadro que no sigan referenciados por otro hueco ni correspondan a una importación activa. El arranque de API limpia huérfanos; sustituciones por importación o emisora y fallos/cancelaciones de importación también ejecutan limpieza. Un fallo de Storage informa `cleanup_pending` y se vuelve a intentar en otro borrado o reinicio. Las reglas Firebase no cambiaron; el backend usa su Admin SDK.

Validación automatizada: `env -u FIREBASE_DATABASE_URL -u FIREBASE_STORAGE_BUCKET -u FIREBASE_SERVICE_ACCOUNT_JSON -u GOOGLE_APPLICATION_CREDENTIALS .venv/bin/python -m pytest backend/tests scripts/tests -q` dio **29 passed** con un aviso de deprecación de Starlette/TestClient y HTTPX; compileall, `node --check web/app.js` y `git diff --check` pasaron. La prueba usa un Storage falso para comprobar que se preservan objetos referenciados y cargas activas y se borra un huérfano.

En Firebase real, antes de borrar, inspeccioné conteos sin imprimir identificadores ni nombres: había un cuadro con una canción y dos referencias de medios. El enlace privado almacenado para la importación correspondía a esa única selección. Desde la raíz del repositorio ejecuté el borrado dirigido sin imprimir el identificador ni las URLs:

```bash
python3 - <<'PY'
import json
from pathlib import Path
from urllib.request import Request, urlopen

frame_id = Path('secrets/frame-test-token.txt').read_text(encoding='utf-8').strip()
headers = {'Authorization': 'Bearer ' + frame_id}
base = 'http://127.0.0.1:8000'
with urlopen(Request(base + '/state', headers=headers), timeout=20) as response:
    state = json.loads(response.read())
assert len(state['slots']) == 1
slot_key = next(iter(state['slots']))
slot = int(slot_key.removeprefix('slot-'))
with urlopen(Request(base + f'/slots/{slot}', headers=headers, method='DELETE'), timeout=20) as response:
    result = json.loads(response.read())
assert result['cleanup_pending'] is False
assert result['deleted_objects'] == 2
PY
```

Resultado real: selección retirada, `deleted_objects=2`, `cleanup_pending=false`; los GET anónimos a las dos URLs de Storage obtenidas antes del borrado devolvieron 404 y `/state` quedó sin selección. El identificador ficticio `mi-cuadro-prueba` se conservó intacto. Las reglas de Firebase no cambiaron y no se desplegó ningún servicio externo.

Compose sigue activo: `api` en `127.0.0.1:8000` y `web` en `127.0.0.1:5173`. Para abrir el cuadro de prueba vacío usa [http://127.0.0.1:5173/#token=mi-cuadro-prueba](http://127.0.0.1:5173/#token=mi-cuadro-prueba). No se modificaron ni redesplegaron reglas Firebase; no se desplegó Render ni se tocó facturación. No se validaron móviles físicos, hardware, firmware ni escucha humana.

### Play/stop en la portada — 12 de noviembre de 2026

Se quitó el panel de reproductor que aparecía debajo de las tarjetas. Ahora el control de play queda superpuesto a la portada y cambia a stop durante la reproducción; se detiene al pulsarlo, al terminar el audio, al cambiar/eliminar la selección o al salir de la página. `node --check web/app.js` y `git diff --check` pasaron y el servidor estático local entrega el HTML/JS actualizado. No se hizo validación visual interactiva en esta edición: no hay Chrome/Chromium en el PATH y el cuadro Firebase quedó vacío tras eliminar su selección. La prueba anterior de reproducción real en Chrome sigue documentada arriba.


## Búsqueda e integración de emisoras — 12 de noviembre de 2026

Se añadió `POST /stations/search` como proxy acotado a Radio Browser: nombre obligatorio, país opcional, máximo 12 resultados, timeout de 12 segundos, filtro del proveedor para emisoras marcadas caídas y filtrado local de URL HTTPS. La web permite elegir un resultado, guarda URL resuelta, UUID y metadatos disponibles, y mantiene la entrada manual. La búsqueda no solicita el audio ni verifica que el stream siga activo; la compatibilidad real requiere escucha en navegador y validación posterior en ESP32.

Comprobación aislada ejecutada: `env -u FIREBASE_DATABASE_URL -u FIREBASE_STORAGE_BUCKET -u FIREBASE_SERVICE_ACCOUNT_JSON -u GOOGLE_APPLICATION_CREDENTIALS .venv/bin/python -m pytest backend/tests scripts/tests -q` dio **30 passed**; Radio Browser se simuló y se comprobaron parámetros, User-Agent y filtrado de URL insegura. `compileall`, `node --check web/app.js` y `git diff --check` pasaron. La consulta de solo lectura al proveedor y la función de la API devolvieron resultados reales para «Radio Nacional» en España; todos los cinco resultados expuestos por la API tenían URL HTTPS. No se abrió ningún stream ni se hizo prueba visual/móvil o escucha de una emisora.


## Logo de emisora en portada — 12 de noviembre de 2026

La tarjeta de emisora muestra centrado el `favicon` HTTPS recibido de Radio Browser. Si no hay URL válida o la imagen falla al cargar, se retira el logo y queda la tarjeta con el nombre. La canción mantiene su imagen actual. Comprobaciones: 30 tests backend/scripts, `compileall`, `node --check web/app.js` y `git diff --check` correctos. No se pudo hacer revisión visual en navegador/móvil porque no hay Chromium disponible en el entorno.

## Recuperación durable de importaciones — 12 de noviembre de 2026

El worker guarda reclamación y generación de ejecución en el estado. Cancelar o vaciar el hueco marca la tarea terminal de forma durable. Las actualizaciones de progreso exigen la ejecución vigente; el hueco y `ready` se escriben en la misma transacción. Cada reintento de recuperación vuelve a descargar y convertir desde el principio, hasta dos recuperaciones; después comunica que hay que cancelar y crear una importación nueva. Las subidas usan rutas por ejecución para que una solicitud antigua no pueda pisar los objetos de un reintento. Un apagado ordenado reencola sin cancelar. La limpieza conserva objetos publicados y tareas activas, y reintenta restos al inicio, al terminar trabajos y cada cinco minutos.

SQLite usa transacciones `BEGIN IMMEDIATE`, WAL y timeout de bloqueo. Compose lo monta en el volumen `sonoro-state`; recrear API conserva el archivo, mientras `down -v` lo elimina. Se añadió `compose.recovery.yaml` con nombre de proyecto y volumen separados, sin `.env`, secretos ni Firebase.

| Comprobación | Resultado |
|---|---|
| Tests backend/scripts en contenedor Python 3.12, Firebase env retiradas | 40 pasaron; un aviso conocido de Starlette/TestClient con HTTPX. Incluye reinicios sintéticos en descarga/preparación/subida, cancelación persistente, vaciado de hueco, subida tardía, límite de recuperación, rollback de publicación, recuperación en lifespan y lectura desde un proceso separado. |
| `python -m compileall -q backend scripts` | Correcto en contenedor; `PYTHONPYCACHEPREFIX=/tmp/sonoro-pycache` evitó escribir en el montaje de scripts de solo lectura. |
| `node --check web/app.js` | Correcto; JS/UI no cambiaron. |
| `docker compose config --quiet` y build de API | Correctos. |
| `docker compose -f compose.recovery.yaml config --quiet` | Correcto. |
| Recorrido Docker aislado | Sembró estado sintético `uploading`, mató API, ejecutó recuperación en otro contenedor y leyó `queued` con `recoveries: 1` desde el mismo volumen; luego eliminó el volumen aislado. No llamó Firebase ni YouTube. |
| `git diff --check` | Correcto. |

El anfitrión solo tenía Python 3.9 sin pytest; la suite se ejecutó dentro de la imagen Docker Python 3.12 e instaló Git y dependencias de desarrollo en un contenedor temporal. No se hicieron pruebas funcionales contra Firebase, YouTube, Render, ni se aceptaron importaciones reales. Para restaurar el API Compose habitual tras la prueba aislada se recreó su contenedor con el `.env` local existente; al arrancar, el ciclo de vida ejecutó la limpieza normal de huérfanos configurada para ese entorno. No se consultaron ni imprimieron sus datos, por lo que no se registra aquí el resultado de esa limpieza. Tampoco se probaron escucha, hardware ni garantías de almacenamiento/proceso en Render. El Compose habitual quedó levantado.

## Entorno de prueba web local desde Mac — 13 de noviembre de 2026

Se añadió `scripts/serve_local_preview.py`: con un comando genera el QR ficticio y, en macOS, sirve exclusivamente `web/` desde Python HTTP en puerto 80 y publica el nombre/servicio con Bonjour mediante `/usr/bin/dns-sd -P`. Sufijo estable, interfaz o IP y puerto se pueden configurar. La terminación con Ctrl+C detiene únicamente esos dos hijos. `scripts/generate_local_qr.py` crea QR PNG local con `qrcode[pil]` y valores ficticios por defecto; `artifacts/local-preview/` y `.venv-qr/` quedan ignorados.

La API lee opcionalmente `ALLOWED_ORIGIN_REGEX` y pasa su valor (o `None`) a `CORSMiddleware.allow_origin_regex`, conservando `ALLOWED_ORIGINS`, métodos y cabeceras previos. Se documentó la variable para Render, la prueba por IP/puerto y el recorrido desde móvil. `web/index.html` ya tenía `meta[name="sonoro-api-base"]` en `https://cuadro-sonoro.onrender.com`; se mantuvo y se corrigieron guías que indicaban por error el backend local.

| Verificación | Resultado |
|---|---|
| Suite aislada backend/scripts, sin entorno Firebase heredado | 44 pasaron, incluido CORS: dos hostnames admitidos, preflight Authorization/Content-Type, origen externo y sufijo engañoso rechazados, exactos conservados, y comportamiento previo sin regex. Aviso conocido de deprecación Starlette/TestClient con HTTPX. |
| `python -m compileall -q backend scripts` con `.venv` | Correcto. |
| `node --check web/app.js` | Correcto. |
| Servidor/anuncio real en macOS, puerto 80 | `dns-sd -P` registró servicio y hostname; `dns-sd -G v4 cuadro-sonoro-dev001.local` resolvió a la IP LAN. GET por IP local y por hostname resolvieron HTTP 200 y el HTML servido contenía la base de Render. |
| QR local | Instalado `qrcode[pil]` en `.venv-qr`; PNG de prueba generado y reconocido como PNG 410×410. Archivo ignorado por Git. |
| Ctrl+C/limpieza | Terminal mostró salida ordenada del servidor; el lanzador termina Bonjour y HTTP. |
| Prueba física móvil/Render/hardware | Pendiente. No se modificó ni desplegó Render; no se hicieron llamadas de importación, cambios Firebase ni pruebas de hardware. |

Siguiente paso que correspondía al experimento local de esa fecha; queda como antecedente, no como procedimiento de producción. La guía de herramientas Bonjour se conserva en [PRUEBA_WEB_LOCAL.md](PRUEBA_WEB_LOCAL.md). La arquitectura vigente requiere CORS para `https://sonoro.zeliuk.xyz`; publicación, HTTPS y CORS efectivos siguen pendientes de verificación.
# Integración Apify simulada — 16 de noviembre de 2026

Implementación local de búsqueda con `streamers/youtube-scraper` y descarga con `lurkapi/youtube-to-mp3-audio-downloader`. Se revisaron las páginas actuales de esquemas de entrada/salida y la API de runs de Apify. Las pruebas ejecutadas usan mocks y SQLite temporal: cubren búsqueda con resultados/vacía/fallo y configuración ausente; normalización/filtros; importación y conservación del contenido anterior; resultado individual fallido con run exitoso; duración no permitida, transferencia excesiva, formato incorrecto; run ID durable tras recuperación; seguimiento reencolado sin duplicar el Actor; creación ambigua sin repetir POST; cancelación remota con reintento, carrera de cancelación/creación y protección ante publicación tardía; límite global/frecuencia; CORS preflight para Authorization desde ambos orígenes localhost; diagnóstico redactado del resultado individual fallido del Actor. No se usaron credenciales ni servicios reales y no se desplegó ni generó consumo.

Comprobaciones locales previas: `python -m pytest backend/tests scripts/tests -q` (63 passed), `python -m compileall -q backend scripts`, `node --check web/app.js`, `git diff --check`; `docker compose config --quiet` pasó. La construcción de imagen se inició, pero el comando no entregó progreso ni finalizó dentro de la ventana de observación; no se declara Docker build validado. Registro histórico del flujo Apify, ya retirado. No constituye instrucción para el proveedor vigente.

### Descarga autenticada de medios Apify

La captura del run mostró `Success` y un `audioFileUrl` bajo `api.apify.com/v2/key-value-stores/...`; ese registro privado requiere autorización. `open_media` ahora adjunta `APIFY_TOKEN` como cabecera Bearer únicamente para el host exacto `api.apify.com`, eliminando cabeceras de autorización recibidas para no reenviarlas a otros hosts. Una prueba simulada comprueba ambos casos y que el token original no se modifica.

El catálogo de Apify marcaba como obsoleto `lurkapi/youtube-video-downloader`, por lo que no se recomienda configurarlo. Se añadió en local un adaptador optativo para `johnvc/youtube-download-api`: traduce la entrada/salida de su esquema publicado y conserva los límites locales. El 16 de noviembre el propietario ejecutó ese Actor en Apify Console con un vídeo público; un run devolvió `YOUTUBE_BLOCKED` tras seis rutas, con 0 archivos y `$0.000020` total; otro entregó 1 archivo MP3 de 2.7 MB tras cinco intentos, 4 minutos de audio y `$0.000064` total. Un run posterior, iniciado desde el backend con límite remoto de 240 s, fue abortado por timeout después de cuatro rutas bloqueadas; no completó la recuperación. El límite remoto predeterminado del código y la plantilla pasa a 600 s; una variable explícita de Render prevalece y debe actualizarse allí. Añadida prueba del timeout predeterminado y del override. Suite aislada: **66 passed**; `compileall`, `node --check web/app.js` y `git diff --check` correctos. No se ha validado una importación completa a Firebase desde Render.

## Maqueta interactiva del objeto — 16 de noviembre de 2026

Se añadió una página aislada en `web/maqueta/` que presenta el objeto a partir de la imagen facilitada, acepta un identificador de cuadro y consulta `GET /state` y `GET /media/{slot}` usando la API configurada en el HTML. Los pulsadores seleccionan un hueco y reproducen el audio en el navegador. El botón 1 mantenido durante 2 s muestra en la pantalla un QR real del enlace del cuadro durante 20 s sin detener el audio; el generador local está distribuido con licencia MIT. La portada se superpone a la pantalla de la referencia. El control de volumen afecta al audio del navegador, y el restablecimiento Wi-Fi solo simula el gesto. No se envían órdenes al dispositivo ni escrituras al backend.

Comprobaciones: `node --check web/maqueta/maqueta.js`, `node --check web/maqueta/qrcode.mjs`, `node --check web/app.js` y `git diff --check` correctos. El generador creó SVG QR de 33×33 y 53×53 módulos para IDs de 11 y 128 caracteres. El servidor estático local respondió HTTP 200 y entregó HTML, CSS, JavaScript y WebP completos en el puerto 5174; el puerto 5173 ya estaba ocupado. La imagen de referencia se convirtió de PNG de 2,0 MB a WebP de 91,6 kB. El halo base del segundo pulsador se atenúa mediante CSS para separar el estado inactivo del activo; pendiente revisión visual en navegador/móvil. No se llamó a la API, Firebase, servicios remotos o hardware. La prueba integrada requiere una API disponible, CORS para el origen de la página y Firebase configurado en el backend si se quieren leer datos reales de RTDB/Storage. No se incluyen credenciales Firebase en frontend.

## Ajuste de interacción de la maqueta — 17 de noviembre de 2026

Los tres pulsadores del objeto activan la pista y la escucha local. El QR ahora ocupa el área de pantalla del cuadro, se genera con el ID indicado y tiene cuenta atrás de 20 s; el audio conserva el estado durante el QR. El botón central recibe una capa CSS para bajar su brillo cuando está inactivo. Se comprobaron sintaxis JS y carga HTTP local; sigue pendiente validar reproducción desde API/Firebase y revisión visual en navegador móvil.

## Retirada del panel lateral — 17 de noviembre de 2026

Se quitó de la maqueta el panel de estado/lista/volumen señalado por el usuario. El audio se activa desde los pulsadores del objeto y el volumen desde la rueda interactiva. El identificador se recibe desde la URL y no aparece un formulario selector.

Comprobaciones: `node --check web/maqueta/maqueta.js`, recuento de referencias DOM sin IDs faltantes y GET HTTP 200 para HTML, CSS, JS, módulo QR e imagen WebP en el servidor estático local. No se comprobó visualmente en navegador/móvil ni se accedió a Firebase.

## Token por URL en la maqueta — 17 de noviembre de 2026

Se eliminó el formulario selector del ID. La maqueta carga el token desde `#token=` o `?token=`, lo valida, lo guarda en `sessionStorage` y limpia el fragmento, siguiendo el acceso habitual del producto. Sin token, muestra una instrucción para abrir la URL correcta.

Comprobaciones: `node --check` para `maqueta.js` y `qrcode.mjs`; HTML, CSS, JS y módulo QR respondieron HTTP 200 en local; no hay IDs DOM referenciados que falten ni elementos del formulario token. `git diff --check` correcto.

## Imagen de botones con tono igual — 17 de noviembre de 2026

Se sustituyó la imagen de referencia por la versión facilitada con los tres anillos ámbar iguales, optimizada a WebP de 74 kB. Se quitó el ajuste CSS exclusivo del botón 2; los tres conservan la misma base y el estado activo usa el mismo halo programado. No se verificó visualmente en navegador/móvil.

Comprobaciones: sintaxis de `maqueta.js` y `qrcode.mjs`, `git diff --check` y carga HTTP 200 de la página, CSS e imagen WebP en servidor local. La imagen nueva ocupa 76.172 bytes.

## Escala del objeto según la ventana — 17 de noviembre de 2026

El ancho de la imagen se calcula con `90vw` y un máximo de `90vh` (o `90dvh` donde está disponible), por lo que usa el 90 % de la dimensión menor tanto en portrait como en landscape. La sección ocupa el ancho de la ventana independientemente del ancho del encabezado. La regla CSS se comprobó estáticamente; pendiente revisar el encuadre final en un navegador móvil.

## QR persistente e identidad de la maqueta — 17 de noviembre de 2026

La pantalla mantiene el QR del ID cuando una respuesta correcta de `/state` confirma que los tres huecos están vacíos. En cuanto existe al menos una selección, vuelve a la portada decorativa o al contenido que corresponda. Mantener el pulsador 1 sigue mostrando el QR durante 20 s. Se alinearon color de fondo, paleta, logotipo y dimensiones del encabezado con los estilos de `web/`; no se cambió `web/index.html`, `web/style.css` ni `web/app.js`.

Comprobaciones: `node --check` para `maqueta.js`, `qrcode.mjs` y `web/app.js`; `git diff --check`; referencias de IDs DOM; carga HTTP local de HTML, CSS, JS, módulo QR e imagen. No se abrió un navegador para verificar visualmente la disposición y no se consultaron API, Firebase ni hardware. La comprobación del QR persistente al recibir estados vacíos/publicados queda pendiente en una sesión integrada.

## Inicio de audio desde Firebase en producción — 17 de noviembre de 2026

Para diagnosticar la falta de música se consultó el sitio publicado y el backend configurado por la maqueta. La página y sus recursos devolvieron HTTP 200. La API devolvió `/health`, `/state` y `/media/{slot}` con HTTP 200 para el ID indicado por el usuario; CORS permitió `https://sonoro.zeliuk.xyz` y el preflight de `Authorization`. Las URLs de Storage respondieron con contenido de audio e imagen; el enlace de emisora respondió como audio AAC. No se imprimieron títulos, identificadores internos ni URLs de medios.

La maqueta ahora resuelve anticipadamente los datos de `/media/{slot}` al cargar el estado, para reducir la espera tras el toque y conservar el gesto del usuario para iniciar audio. `node --check web/maqueta/maqueta.js`, `node --check web/maqueta/qrcode.mjs` y `git diff --check` pasaron. No se automatizó la reproducción audible en navegador. Esta corrección requiere publicar `web/maqueta/maqueta.js`; no se desplegó ningún servicio.

## Error de carga del token en hosting — 17 de noviembre de 2026

La página pública, `maqueta.js`, `maqueta.css` y los datos de la API estaban disponibles. La API devolvió el estado y las URLs de medios; CORS permitió el origen y Storage respondió al solicitar audio. La diferencia encontrada fue que Nginx servía `qrcode.mjs` sin `Content-Type`; los navegadores bloquean ese módulo por MIME estricto, impidiendo que el script principal se ejecute y procese `#token`.

Se renombró el módulo a `qrcode.js` y se versionaron las URLs de módulo en HTML/JS para invalidar posibles cachés largas. La maqueta local pasó sintaxis JavaScript y `git diff --check`. Falta publicar el nuevo contenido y confirmar en navegador de producción que desaparece el fragmento y carga el estado; no se desplegó el hosting.
## Sondeo adaptativo de estado — 17 de noviembre de 2026

La web principal dejó de consultar `/state` cada 1,5 s de forma permanente: sondea cada 2,5 s mientras detecta una tarea activa y cada 120 s cuando está en reposo. Pausa el temporizador con la pestaña oculta y consulta al volver; tras aceptar una canción reanuda el sondeo de progreso. La maqueta de solo lectura consulta cada 60 s y pausa en segundo plano. Esto reduce llamadas, aunque las consultas visibles en reposo siguen pudiendo mantener despierto el servicio gratuito de Render.

Comprobaciones: `node --check web/app.js`, `node --check web/maqueta/maqueta.js` y `git diff --check`. No se ejecutaron pruebas automatizadas ni se consultaron Render, API, Firebase o hardware. Los intervalos se han comprobado en el código, no mediante una medición de red en navegador.

## Vista de cuadro para tablet — 17 de noviembre de 2026

Se creó `web/tablet/` para servir una vista inmersiva del cuadro. La implementación comparte la lógica `maqueta.js` y el generador QR. Dibuja un fondo cálido y una pantalla centrada; no presenta el marco de la fotografía. Las imágenes individuales del pulsador y del mando de volumen facilitadas por el usuario se convirtieron a WebP con transparencia. La solicitud de pantalla completa se vincula a una pulsación directa sobre el fondo para respetar el requisito de gesto del navegador.

No se ejecutaron comprobaciones de sintaxis ni se abrió la página en un navegador durante esta fase. Quedan pendientes la comprobación visual en tablet portrait/landscape, el modo fullscreen según navegador, la carga desde API/Firebase y la publicación de `/tablet/`. No se consultaron servicios remotos ni hardware.

El ajuste posterior igualó grosor, halo y estados inactivo/activo con las reglas de `/maqueta`. Se dejó quieta la imagen del mando de volumen y se conectó el giro de su indicador al valor local. Este ajuste visual no se ha revisado en navegador.

El anillo superpuesto se redujo para alinearlo con el aro de luz del pulsador individual (aproximadamente 64 % del ancho de su imagen). Pendiente comprobar el encaje visual en navegador; no se ejecutaron pruebas.

Se aumentó ligeramente el tamaño adaptable de los tres pulsadores. La revisión de encaje en tablet sigue pendiente.

Se cambiaron pulsadores y rueda a tamaños porcentuales de la fila de controles, en lugar de límites en píxeles o unidades de ventana. Se ajustaron al 22 % y 24 % y se amplió la fila. Pendiente revisar su proporción en formatos de tablet distintos.

Se quitó el temporizador de consulta de `/maqueta` y `/tablet`: hacen una lectura inicial y solicitan estado de nuevo ante pulsaciones cortas. Las URLs de medios se conservan en memoria por selección para mantener el inicio del audio desde el toque. No se ejecutaron pruebas ni mediciones de red; queda pendiente comprobar la cadencia real en navegador.

## Check backend de GitHub Actions — 17 de noviembre de 2026

El log aportado por Carlos mostraba dos fallos: `test_late_upload_completion_cannot_publish_after_cancel` y `test_progress_pipeline_only_commits_after_upload`. Ambas pruebas usaban respuestas HTTP simuladas con `audio.example`; al añadir la validación DNS contra destinos no públicos, el importador rechazaba el hostname de prueba antes de alcanzar la cancelación/publicación que esas pruebas cubren.

Las dos pruebas aíslan ahora la resolución DNS mediante un mock del validador. Se añadieron pruebas del validador que simulan una IP pública y direcciones loopback/privadas, sin consultar DNS real. Esta validación local no usa RapidAPI, Firebase ni hardware. Verificación local en Python 3.12.15, con las variables Firebase heredadas retiradas: `49 passed, 1 warning` en `backend/tests` y `scripts/tests`; `compileall` y `git diff --check` también pasaron. La advertencia es la deprecación de Starlette/httpx indicada por FastAPI. No se ha vuelto a ejecutar GitHub Actions; la ejecución local usa los mismos pasos de backend.
## Referencias visuales del objeto — 17 de noviembre de 2026

Se incorporaron en `docs/imagenes/` dos ilustraciones WebP optimizadas: una representación exterior orientativa del resultado y una vista conceptual del montaje interno. Se enlazaron desde la definición y la guía de firmware, indicando que la segunda no es un esquema de conexiones comprobado. Las fuentes PNG proporcionadas se convirtieron localmente; no se validó ningún componente ni cableado físico.

Comprobación: las dos imágenes se abren y se convirtieron desde los adjuntos locales. No se ejecutaron pruebas de software ni se revisó un montaje real.
