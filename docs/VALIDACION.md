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
| Tests backend/scripts con variables Firebase retiradas | 13 pasaron, incluidos tokens provisionados, rechazo de token no autorizado, separación entre cuadros, límite de una tarea activa por cuadro, rechazo del token local con configuración Firebase y no migración de SQLite heredado. Un aviso de deprecación de Starlette/TestClient con HTTPX. |
| `compileall` y `node --check web/app.js` | Correctos. |
| Web estática tras cambiar la etiqueta del token | HTML, JS y CSS respondieron 200. No se hizo revisión visual móvil; CSS y estructura no cambiaron. |
| API local y Bearer | El token local autorizado accedió; tokens ausentes, cortos o no provisionados: 401. Las pruebas con dos tokens provisionados verificaron separación de estado y medios. |
| Importación sin Storage | 503 esperado, sin crear tarea. |
| OpenAPI exportado | Ocho rutas y esquemas actualizados en `openapi.prototype.json`; los endpoints privados documentan seguridad y errores principales. |

Estas pruebas usan SQLite temporal y URLs sintéticas. No prueban Firebase RTDB/Storage reales, descargas de YouTube, Docker, Render, acceso ESP32 ni enlaces QR/NFC. No se validó visualmente el cambio de texto en distintos tamaños de pantalla; no se modificaron CSS ni estructura.

## Enlace de acceso por cuadro — 12 de noviembre de 2026

La web acepta `https://dominio/#token=<token_urlsafe>`. El token se recoge en el navegador, se conserva en `sessionStorage` de la pestaña y se quita de la barra sin navegar de nuevo. Las operaciones usan `Authorization: Bearer`; el backend mantiene su allowlist `FRAME_TOKEN_HASHES`. Cambiar de enlace aborta solicitudes del contexto anterior y vacía el estado visible. Token ausente queda bloqueado; 401 limpia la sesión y no abre la demo. La demo continúa siendo una elección explícita.

| Comprobación | Resultado |
|---|---|
| `node --check web/app.js` | Correcto. |
| Tests locales backend/scripts, Firebase env retiradas | 13 pasaron; un aviso conocido de deprecación Starlette/TestClient con HTTPX. |
| `python -m compileall -q backend scripts` | Correcto. |
| Navegador Chrome headless, web estática y FastAPI local con SQLite temporal | Bloqueo inicial sin token; guardar URL sin token no abrió demo; fragmento eliminado sin navegación; la petición `/state` incluyó Bearer; recarga de pestaña conservó acceso; cambio entre dos tokens provisionados mostró solo el estado del segundo; token largo no provisionado recibió 401, limpió el token/estado y no abrió demo; selección explícita de demo y retorno mediante enlace funcionaron. |
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

Carlos decidió que la configuración publicada y los medios sean legibles sin sesión si se conocen sus URLs. El identificador sigue siendo Bearer de la API y SHA-256 separa registros/rutas, pero no se considera autorización de lectura Firebase. RTDB limita el GET público a `frames/{sha256}/slots`; raíz, listado de cuadros, `jobs` y escrituras quedan denegados. Storage permite GET de objeto bajo `private/frames/{sha256}/`, sin sesión ni URL firmada temporal; listar y escribir siguen denegados. Cambios e importaciones siguen pasando por API con `FRAME_TOKEN_HASHES`.

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

La primera respuesta 404 no se reproduce en la comprobación repetida; no se atribuye una causa sin evidencia. Los emuladores verificaron anteriormente lectura pública, rechazo de listados/escrituras y separación entre cuadros. Eso no sustituye la validación de reglas contra Firebase real. En el `.env` anterior no existía `FRAME_TOKEN_HASHES`; se conservaron las variables e identificadores que sí estaban, sin añadir un token de cuadro. Por tanto, el backend accede a RTDB y Storage, pero la API local no autoriza operaciones de cuadro hasta provisionar el hash.

La prueba real utilizó un registro aleatorio temporal fuera de selecciones y verificó su limpieza. No se ejecutaron importaciones de YouTube, no se tocaron reglas ni otros recursos Firebase y no se incluyeron rutas personales o credenciales en esta documentación.

## Preparación y validación de reglas del cuadro de prueba — 12 de noviembre de 2026

Se reutilizó el identificador local aleatorio que ya existía, sin imprimirlo. Se guardó una copia recuperable en `secrets/frame-test-token.txt` (ignorada por Git) y se añadió únicamente su SHA-256 a `FRAME_TOKEN_HASHES`, conservando los valores previos. Antes de llamar a la API se confirmó que RTDB no tenía cuadros ni tareas previas.

| Comprobación | Resultado |
|---|---|
| Reglas locales con emuladores Database y Storage | `PASS`: leer `frames/{sha256}/slots` y descargar objetos individuales; listar `/frames`, leer `jobs`, listar Storage y escribir públicamente fueron rechazados. El cliente descargó medios separados de dos cuadros. Emuladores detenidos al terminar. |
| API local contra RTDB real | `GET /state` con el identificador provisionado: 200 y estado vacío. Identificador aleatorio no autorizado: 401, sin crear registro. El estado temporal de prueba se eliminó y se verificó su ausencia. |
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

La credencial permite al Admin SDK usar RTDB y Storage, pero no da a Firebase CLI los permisos de publicación necesarios. Para revisar el cuadro de prueba localmente, el valor está en `secrets/frame-test-token.txt`; no se copia al informe ni a documentación compartida. Para generar el enlace en la terminal local, desde la raíz:

```bash
python3 - <<'PY'
from pathlib import Path
token = Path('secrets/frame-test-token.txt').read_text(encoding='utf-8').strip()
print('https://<dominio-de-la-web>/#token=' + token)
PY
```

No activar trazas de shell ni copiar la salida a logs o informes. El archivo privado se conserva para continuar la fase. No se hicieron importaciones de YouTube ni se dejaron registros u objetos remotos de prueba. La prueba de descarga no valida un MP3 real ni la reproducción en navegador.

## Ajuste de contexto compartido

Las instrucciones de ChatGPT se trasladaron al archivo versionado `docs/INSTRUCCIONES_CHATGPT.md`. Se actualizaron las referencias, la definición y la regla de mantenimiento en AGENTS.md. Cambio documental; comprobados enlaces y contenido del ZIP, sin modificar lógica ni repetir pruebas de ejecución.
