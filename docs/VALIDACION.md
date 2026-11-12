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

## Ajuste de contexto compartido

Las instrucciones de ChatGPT se trasladaron al archivo versionado `docs/INSTRUCCIONES_CHATGPT.md`. Se actualizaron las referencias, la definición y la regla de mantenimiento en AGENTS.md. Cambio documental; comprobados enlaces y contenido del ZIP, sin modificar lógica ni repetir pruebas de ejecución.
