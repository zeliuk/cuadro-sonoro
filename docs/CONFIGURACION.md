# Configuración por entorno

El modo demo no necesita backend ni nube. Para la API local, desde la raíz ejecuta `python3 scripts/setup_local.py`: crea `backend/.env` a partir de la plantilla con SQLite y Firebase vacíos. No genera identificadores ni sobrescribe un archivo existente.

## Identificador del cuadro

No hay registro de usuarios, credencial, lista de cuadros ni paso de aprovisionamiento. Cualquier identificador válido abre o crea su espacio de datos. La web lo recibe como `#token=<identificador>`, lo conserva en `sessionStorage` de la pestaña y lo envía como `Authorization: Bearer <identificador>` por compatibilidad. Bearer es aquí un transporte y no prueba identidad ni permiso.

El formato aceptado es de 1 a 128 caracteres ASCII: el primero debe ser letra o número; los siguientes pueden ser letras, números, guion o guion bajo. Por ejemplo, `mi-cuadro-prueba`. API y cliente directo calculan `SHA-256(UTF-8(identificador))` para conservar la ruta `frames/{sha256}` y el prefijo de Storage `private/frames/{sha256}`. El hash separa cuadros; no oculta ni protege el identificador. No hay endpoint para listar cuadros.

| Variable actual | Función | Ubicación |
|---|---|---|
| `ALLOWED_ORIGINS` | Orígenes exactos permitidos por CORS. | `.env`/Render. No autentica usuarios. |
| `FIREBASE_DATABASE_URL` | URL exacta de RTDB. Vacía: SQLite local. | `.env`/Render. |
| `FIREBASE_STORAGE_BUCKET` | Nombre del bucket sin `gs://`. Vacía: importación no disponible. | `.env`/Render. |
| `GOOGLE_APPLICATION_CREDENTIALS` | Ruta al JSON privado de cuenta de servicio. | Nativo: absoluta; Compose: `/run/secrets/firebase.json`. |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | Alternativa al archivo: JSON completo como secreto. | Render; dejar vacío si se usa archivo. |
| `STATE_DB` | SQLite local de desarrollo. El archivo no se versiona. | `.env`; valor inicial en `/tmp`. |
| `PORT` | Puerto del proceso Docker/Render; por defecto 8000. | Entorno de ejecución. |

Las selecciones antiguas que ya están bajo el hash del identificador continúan en la misma ruta; no se cambia el algoritmo ni se migra el nodo existente. Los datos de la antigua colección global `state` no se asignan a un cuadro porque su identidad no puede deducirse.

No rellenar valores Firebase ficticios para sortear el 503: no crean recursos ni credenciales. `storage_configured` y `durable_state` en `/health` solo reflejan presencia de variables; no acreditan conexión o permisos.

## Firebase y acceso directo del dispositivo

Crear/configurar el proyecto y copiar desde su consola URL RTDB y nombre de bucket. Storage requiere Blaze: decidir facturación y región antes de activarlo. Guardar el JSON de servicio en `secrets/firebase.json`, ignorado, o como secreto del servicio. No pegarlo en chat, web, firmware o documentación.

En macOS, la API nativa puede conservar en `backend/.env` la ruta absoluta de credencial. Compose monta `./secrets` en solo lectura y sobrescribe dentro del contenedor `GOOGLE_APPLICATION_CREDENTIALS=/run/secrets/firebase.json`. Para usar ambas modalidades, copia el archivo privado a `secrets/firebase.json` sin modificar la ruta nativa; restringe permisos y no lo añadas a Git. La alternativa `FIREBASE_SERVICE_ACCOUNT_JSON` debe quedar vacía si se usa archivo.

Admin SDK usa credenciales únicamente en backend y herramientas privadas; no se entrega al dispositivo. Por decisión expresa de Carlos, las reglas Firebase permiten leer `slots` y descargar objetos individuales por URL conocida sin sesión; bloquean listados, tareas y escrituras públicas. Cualquier persona que conozca o elija un identificador puede además modificar los datos de ese espacio mediante la API. SHA-256 solo deriva la ruta; no funciona como autorización. No hay Firebase Auth.

La web recibe la URL de API desde `meta[name="sonoro-api-base"]`; la copia actual para desarrollo local apunta inicialmente a `http://127.0.0.1:8000`, mientras que `web/index.html` está configurado para `https://cuadro-sonoro.onrender.com`. En el producto, el ESP32 servirá los archivos estáticos y el navegador del móvil llamará directamente a esa API HTTPS de Render. La credencial Admin no se envía al navegador.

El QR/NFC del producto usará un hostname local único del ESP32, preferentemente `http://sonoro-<sufijo-unico>.local/#token=<identificador>`, no `localhost`: en el móvil, `localhost` apunta al propio teléfono. El hostname se anunciará por mDNS y deberá probarse en las versiones objetivo de Android/iOS y routers; si mDNS falla, habrá que aplicar una reserva DHCP o mostrar una dirección local alternativa. El móvil debe permanecer conectado a la red doméstica y tener salida a internet para llegar a Render. La API tendrá que permitir por CORS el origen de la página local; CORS no autentica ni autoriza el identificador.
