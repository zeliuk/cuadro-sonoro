# Configuración por entorno

El modo demo no necesita backend ni nube. Para la API local, desde la raíz ejecuta `python3 scripts/setup_local.py`: crea `backend/.env` a partir de la plantilla con SQLite y Firebase vacíos. No genera identificadores ni sobrescribe un archivo existente.

## Identificador del cuadro

No hay registro de usuarios, credencial, lista de cuadros ni paso de aprovisionamiento. Cualquier identificador válido abre o crea su espacio de datos. La web lo recibe como `#token=<identificador>`, lo conserva en `sessionStorage` de la pestaña y lo envía como `Authorization: Bearer <identificador>` por compatibilidad. Bearer es aquí un transporte y no prueba identidad ni permiso.

El formato aceptado es de 1 a 128 caracteres ASCII: el primero debe ser letra o número; los siguientes pueden ser letras, números, guion o guion bajo. Por ejemplo, `mi-cuadro-prueba`. API y cliente directo calculan `SHA-256(UTF-8(identificador))` para conservar la ruta `frames/{sha256}` y el prefijo de Storage `private/frames/{sha256}`. El hash separa cuadros; no oculta ni protege el identificador. No hay endpoint para listar cuadros.

| Variable actual | Función | Ubicación |
|---|---|---|
| `ALLOWED_ORIGINS` | Lista separada por comas de orígenes exactos permitidos por CORS. | `backend/.env`. No autentica usuarios. |
| `ALLOWED_ORIGIN_REGEX` | Regex opcional de origen CORS; vacío/ausente conserva solo la lista exacta. | `backend/.env`. Para hostname local ver abajo. |
| `FIREBASE_DATABASE_URL` | URL exacta de RTDB. Vacía: SQLite local. | `backend/.env`. |
| `FIREBASE_STORAGE_BUCKET` | Nombre del bucket sin `gs://`. Vacía: importación no disponible. | `backend/.env`. |
| `GOOGLE_APPLICATION_CREDENTIALS` | Ruta al JSON privado de cuenta de servicio. | Nativo: absoluta; Compose: `/run/secrets/firebase.json`. |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | Alternativa al archivo: JSON completo como secreto. | Entorno backend; dejar vacío si se usa archivo. |
| `STATE_DB` | SQLite local de desarrollo. El archivo no se versiona. | `.env`; valor inicial en `/tmp`. |
| `PORT` | Puerto del proceso Docker; por defecto 8000. | Entorno de ejecución. |
| `APIFY_TOKEN` | Token privado para ejecutar Actors, leer sus runs/datasets y descargar medios de sus key-value stores; exclusivamente backend. | **Secreto**, nunca web/firmware/logs. |
| `APIFY_SEARCH_ACTOR` | Actor de búsqueda; predeterminado `streamers/youtube-scraper`. | Configuración backend. |
| `APIFY_DOWNLOAD_ACTOR` | Actor de audio; predeterminado `lurkapi/youtube-to-mp3-audio-downloader`. | Configuración backend. |
| `APIFY_SEARCH_TIMEOUT_SECONDS` / `APIFY_RUN_TIMEOUT_SECONDS` | Espera acotada de búsqueda/ciclo de seguimiento. | Límites backend. |
| `APIFY_ACTOR_TIMEOUT_SECONDS` | Límite del run remoto enviado en la API de Apify. | Límite backend. |
| `APIFY_SEARCH_CACHE_SECONDS` / `APIFY_SEARCH_MIN_INTERVAL_SECONDS` | Retención de resultados y enfriamiento global de búsquedas. | Límites backend. |
| `APIFY_IMPORT_MIN_INTERVAL_SECONDS` / `APIFY_MAX_ACTIVE_IMPORTS` | Enfriamiento y concurrencia global de nuevas descargas. | Límites backend. |

Las selecciones antiguas que ya están bajo el hash del identificador continúan en la misma ruta; no se cambia el algoritmo ni se migra el nodo existente. Los datos de la antigua colección global `state` no se asignan a un cuadro porque su identidad no puede deducirse.

No rellenar valores Firebase ficticios para sortear el 503: no crean recursos ni credenciales. `storage_configured` y `durable_state` en `/health` solo reflejan presencia de variables; no acreditan conexión o permisos.

## Firebase y acceso directo del dispositivo

Crear/configurar el proyecto y copiar desde su consola URL RTDB y nombre de bucket. Storage requiere Blaze: decidir facturación y región antes de activarlo. Guardar el JSON de servicio en `secrets/firebase.json`, ignorado, o como secreto del servicio. No pegarlo en chat, web, firmware o documentación.

En macOS, la API nativa puede conservar en `backend/.env` la ruta absoluta de credencial. Compose monta `./secrets` en solo lectura y sobrescribe dentro del contenedor `GOOGLE_APPLICATION_CREDENTIALS=/run/secrets/firebase.json`. Para usar ambas modalidades, copia el archivo privado a `secrets/firebase.json` sin modificar la ruta nativa; restringe permisos y no lo añadas a Git. La alternativa `FIREBASE_SERVICE_ACCOUNT_JSON` debe quedar vacía si se usa archivo.

Admin SDK usa credenciales únicamente en backend y herramientas privadas; no se entrega al dispositivo. Por decisión expresa de Carlos, las reglas Firebase permiten leer `slots` y descargar objetos individuales por URL conocida sin sesión; bloquean listados, tareas y escrituras públicas. Cualquier persona que conozca o elija un identificador puede además modificar los datos de ese espacio mediante la API. SHA-256 solo deriva la ruta; no funciona como autorización. No hay Firebase Auth.

La web recibe la URL desde `meta[name="sonoro-api-base"]`. `web/index.html` apunta a `https://cuadro-sonoro.onrender.com`. Al servir estáticos localmente, el navegador llama a Render y no requiere backend Python en el Mac. La credencial Apify solo reside como secreto en el backend. La prueba real está pendiente; configuración y procedimiento están en [PRUEBA_APIFY_RENDER.md](PRUEBA_APIFY_RENDER.md).

El enlace aprobado es `http://cuadro-sonoro-<id-dispositivo>.local/#token=<id-cuadro>`, por ejemplo `http://cuadro-sonoro-dev001.local/#token=cuadro-prueba`. En el entorno Mac de prueba se usa Bonjour/mDNS y el puerto HTTP 80. El sufijo es una etiqueta DNS configurable (1–49 caracteres en el script) y permanece estable aunque cambie la IP; el identificador del fragmento sigue siendo el ámbito SHA-256 existente. Instrucciones completas de instalación, QR, arranque y diagnóstico están en [PRUEBA_WEB_LOCAL.md](PRUEBA_WEB_LOCAL.md).

CORS contempla `http://127.0.0.1:5173`, `http://localhost:5173` y el patrón restringido de hostnames `cuadro-sonoro-*.local`; el preflight debe permitir Authorization. `127.0.0.1` no identifica al Mac desde el teléfono.

Para la prueba de Render se mantienen los dos orígenes exactos de localhost y el patrón restringido de hostname local. La configuración completa de Apify y del servicio está en [PRUEBA_APIFY_RENDER.md](PRUEBA_APIFY_RENDER.md).

```dotenv
ALLOWED_ORIGIN_REGEX=^http://cuadro-sonoro-[a-z0-9-]+\.local$
```

No añadas esta variable a un backend nuevo sin revisar su necesidad. `ALLOWED_ORIGINS` permanece vigente para orígenes exactos. El regex no admite puertos alternativos, HTTPS ni subdominios engañosos como `cuadro-sonoro-dev001.local.ejemplo.com`; para una prueba por IP o puerto alternativo añade el origen exacto (incluyendo puerto) a `ALLOWED_ORIGINS`. La opción vacía/ausente conserva el comportamiento previo. Se permiten los métodos GET/POST/DELETE y cabeceras Authorization/Content-Type.

CORS solo permite que un navegador lea respuestas desde los orígenes indicados. No autentica el hostname ni el cuadro, no vincula ambos identificadores y no sustituye al identificador Bearer. El token en `#token` no se envía como parte del origen ni en la petición que obtiene la página. El flujo móvil requiere una API alcanzable desde la LAN y salida a Internet para los servicios externos.
