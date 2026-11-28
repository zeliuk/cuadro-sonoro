# Configuración por entorno

El modo demo no necesita backend ni nube. Para la API local, desde la raíz ejecuta `python3 scripts/setup_local.py`: crea `backend/.env` a partir de la plantilla con SQLite y Firebase vacíos. No genera identificadores ni sobrescribe un archivo existente.

## Identificador del cuadro

No hay registro de usuarios, credencial, lista de cuadros ni paso de aprovisionamiento. Cualquier identificador válido abre o crea su espacio de datos. La web lo recibe como `#token=<identificador>`, lo conserva en `sessionStorage` de la pestaña y lo envía como `Authorization: Bearer <identificador>` por compatibilidad. Bearer es aquí un transporte y no prueba identidad ni permiso.

El formato aceptado es de 1 a 128 caracteres ASCII: el primero debe ser letra o número; los siguientes pueden ser letras, números, guion o guion bajo. Por ejemplo, `mi-cuadro-prueba`. API y cliente directo calculan `SHA-256(UTF-8(identificador))` para conservar la ruta `frames/{sha256}` y el prefijo de Storage `private/frames/{sha256}`. El hash separa cuadros; no oculta ni protege el identificador. No hay endpoint para listar cuadros.

| Variable actual | Función | Ubicación |
|---|---|---|
| `ALLOWED_ORIGINS` | Lista separada por comas de orígenes exactos permitidos por CORS. | `backend/.env`. No autentica usuarios. |
| `ALLOWED_ORIGIN_REGEX` | Regex opcional de origen CORS; vacío/ausente conserva solo la lista exacta. | `backend/.env`; se conserva para los escenarios de desarrollo que la necesiten. |
| `FIREBASE_DATABASE_URL` | URL exacta de RTDB. Vacía: SQLite local. | `backend/.env`. |
| `FIREBASE_STORAGE_BUCKET` | Nombre del bucket sin `gs://`. Vacía: importación no disponible. | `backend/.env`. |
| `GOOGLE_APPLICATION_CREDENTIALS` | Ruta al JSON privado de cuenta de servicio. | Nativo: absoluta; Compose: `/run/secrets/firebase.json`. |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | Alternativa al archivo: JSON completo como secreto. | Entorno backend; dejar vacío si se usa archivo. |
| `STATE_DB` | SQLite local de desarrollo. El archivo no se versiona. | `.env`; valor inicial en `/tmp`. |
| `PORT` | Puerto del proceso Docker; por defecto 8000. | Entorno de ejecución. |
| `RAPIDAPI_KEY` | Clave privada para preparar el MP3 seleccionado mediante RapidAPI; exclusivamente backend. | Secreto, nunca web/firmware/logs. |
| `RAPIDAPI_USERNAME` | Username del perfil RapidAPI. El backend lo añade al `User-Agent` y calcula el `X-RUN` requerido por el host de medios. | Backend local y Render; no es la clave API. |
| `IMPORT_MIN_INTERVAL_SECONDS` | Enfriamiento global entre importaciones. | Límite backend. |
| `IMPORT_MAX_ACTIVE` | Número máximo de importaciones globales activas. | Límite backend. |


Las selecciones antiguas que ya están bajo el hash del identificador continúan en la misma ruta; no se cambia el algoritmo ni se migra el nodo existente. Los datos de la antigua colección global `state` no se asignan a un cuadro porque su identidad no puede deducirse.

No rellenar valores Firebase ficticios para sortear el 503: no crean recursos ni credenciales. `storage_configured` y `durable_state` en `/health` solo reflejan presencia de variables; no acreditan conexión o permisos.

## Firebase y acceso directo del dispositivo

Crear/configurar el proyecto y copiar desde su consola URL RTDB y nombre de bucket. Storage requiere Blaze: decidir facturación y región antes de activarlo. Guardar el JSON de servicio en `secrets/firebase.json`, ignorado, o como secreto del servicio. No pegarlo en chat, web, firmware o documentación.

En macOS, la API nativa puede conservar en `backend/.env` la ruta absoluta de credencial. Compose monta `./secrets` en solo lectura y sobrescribe dentro del contenedor `GOOGLE_APPLICATION_CREDENTIALS=/run/secrets/firebase.json`. Para usar ambas modalidades, copia el archivo privado a `secrets/firebase.json` sin modificar la ruta nativa; restringe permisos y no lo añadas a Git. La alternativa `FIREBASE_SERVICE_ACCOUNT_JSON` debe quedar vacía si se usa archivo.

Admin SDK usa credenciales únicamente en backend y herramientas privadas; no se entrega al dispositivo. Por decisión expresa de Carlos, las reglas Firebase permiten leer `slots` y descargar objetos individuales por URL conocida sin sesión; bloquean listados, tareas y escrituras públicas. Cualquier persona que conozca o elija un identificador puede además modificar los datos de ese espacio mediante la API. SHA-256 solo deriva la ruta; no funciona como autorización. No hay Firebase Auth.

La web pública decidida es `https://sonoro.zeliuk.xyz`, con identificador ficticio en el fragmento, por ejemplo `https://sonoro.zeliuk.xyz/#token=cuadro-demo`. `web/index.html` configura actualmente la API `https://cuadro-sonoro.onrender.com`. Para desarrollo local se puede cambiar temporalmente el meta a `http://127.0.0.1:8000`; no cambiar el origen de producción por una dirección Raspberry Pi. La web acepta el identificador en `#token`, lo guarda en `sessionStorage` y limpia la barra. El móvil necesita Internet, no estar en la Wi-Fi del cuadro. La búsqueda usa yt-dlp y la descarga seleccionada RapidAPI; `RAPIDAPI_KEY` y `RAPIDAPI_USERNAME` solo se guardan en el backend. Para requisitos del backend, consulta [PRUEBA_RAPIDAPI.md](PRUEBA_RAPIDAPI.md).

El backend admite `ALLOWED_ORIGINS` (lista exacta, separada por comas) y `ALLOWED_ORIGIN_REGEX` opcional. Para producción, el origen requerido es `https://sonoro.zeliuk.xyz`, sin barra final. Ejemplo de valor de configuración —no evidencia de que ya esté aplicado en Render—:

```dotenv
ALLOWED_ORIGINS=https://sonoro.zeliuk.xyz
```

Conserva junto a él los orígenes exactos necesarios para desarrollo. `Authorization` y `Content-Type` ya son cabeceras permitidas por la implementación. El token del fragmento no forma parte del origen ni se envía en la petición que obtiene el HTML. CORS solo permite que el navegador lea la respuesta; no autentica ni vincula identificadores.

La configuración versionada actual permite como orígenes de desarrollo `http://127.0.0.1:5173` y `http://localhost:5173`; `backend/.env.example` conserva además la regex `.local` para la herramienta macOS. Las variables son las existentes en el código. Los hostnames locales y Bonjour son desarrollo, no requisitos de producción. El procedimiento histórico sigue en [PRUEBA_WEB_LOCAL.md](PRUEBA_WEB_LOCAL.md).

CORS solo permite que un navegador lea respuestas desde los orígenes indicados. No autentica al cuadro ni sustituye al identificador Bearer. El enlace público requiere Internet en el móvil; no depende de la LAN del ESP32. El portal local de Wi-Fi del dispositivo configura solo la conexión del cuadro y nunca envía su contraseña a web, Render o Firebase.

## Firmware ESP32-S3 de prueba

El firmware 0.3 configura Wi-Fi mediante un AP local y hace una lectura HTTPS de solo lectura a RTDB con el ID de prueba `charlie`. No usa cuentas de servicio ni tokens Firebase. La URL pública de RTDB es una opción de `idf.py menuconfig` y queda en el `sdkconfig` local ignorado por Git; la contraseña doméstica se guarda en NVS del dispositivo después de conectar. Usa ESP-IDF 5.5.5, BSP Waveshare 2.0.0 y LVGL 9.5.0 con flash QIO 16 MB y PSRAM OPI 8 MB. La instalación manual fijada de ESP-IDF, la extensión oficial VS Code, compilación, configuración de RTDB, portal, monitor serie y transferencia están en [firmware/README.md](../firmware/README.md). No necesita editar `.env` ni `firebase/device-config.json` para el firmware.
