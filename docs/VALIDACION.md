# Validación de esta entrega

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
| Firebase Hosting | Retirado de `firebase.json`; web prevista en servidor propio. |
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
| Enlace directo en Chrome Headless | Se abrió `http://127.0.0.1:5173/#token=mi-cuadro-prueba` sin tocar ajustes. La API local se conectó desde el valor base de `web/index.html`; aparecieron tres huecos vacíos, el fragmento se limpió, el ID quedó en `sessionStorage`, la demo siguió oculta y la consola no mostró errores. |

### Sin conexión manual en la web — 12 de noviembre de 2026

Se retiraron el engranaje y el diálogo que pedían elegir modo, URL de API o identificador. Para cuadros reales, el enlace es el único dato que recibe el usuario; el navegador utiliza la URL base publicada en `meta[name="sonoro-api-base"]` (`http://127.0.0.1:8000` en la copia local). La demo sigue disponible como modo explícito con el botón «Probar demostración» cuando no hay un cuadro activo. `node --check web/app.js`, `git diff --check` y `GET /health` pasaron. Los contenedores API y web responden en `127.0.0.1:8000` y `127.0.0.1:5173`. No se repitió Chrome en esta edición: no hay un ejecutable Chrome/Chromium en el PATH de este entorno; la reproducción anterior queda registrada arriba como validación previa.

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
