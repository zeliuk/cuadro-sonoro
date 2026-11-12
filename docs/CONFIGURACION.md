# Configuración por entorno

El modo demo no necesita configuración de nube. Para el backend local, ejecuta desde la raíz `python3 scripts/setup_local.py`: crea `backend/.env` con un token aleatorio y valores de nube vacíos. Si ya existe, no lo sobrescribe y no imprime su contenido.

| Variable actual | Función | Ubicación |
|---|---|---|
| `IMPORT_API_TOKEN` | Token global del prototipo, solo para pruebas del desarrollador. No es el acceso por cuadro final. | `.env` privado o secreto de Render. |
| `ALLOWED_ORIGINS` | Orígenes exactos permitidos por CORS. | `.env`/Render. No sustituye autorización. |
| `FIREBASE_DATABASE_URL` | URL exacta de RTDB. Vacía: SQLite local. | `.env`/Render. |
| `FIREBASE_STORAGE_BUCKET` | Nombre del bucket sin `gs://`. Vacío: importación no disponible. | `.env`/Render. |
| `GOOGLE_APPLICATION_CREDENTIALS` | Ruta al JSON privado de cuenta de servicio. | Nativo: absoluta; Compose: `/run/secrets/firebase.json`. |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | Alternativa al archivo: JSON completo como secreto. | Render; dejar vacío si se usa archivo. |
| `STATE_DB` | SQLite local de desarrollo. El archivo no se versiona. | `.env`; valor inicial en `/tmp`. |
| `PORT` | Puerto del proceso Docker/Render; por defecto 8000. | Entorno de ejecución. |

No rellenar valores Firebase ficticios para saltarse el 503: no configuran recursos reales y provocan fallos del worker. `storage_configured` y `durable_state` en `/health` solo reflejan presencia de variables; no acreditan acceso.

## Firebase cuando se aborde la integración

Crear/configurar un proyecto dedicado y copiar desde su consola URL RTDB y nombre de bucket. Storage requiere Blaze: decidir facturación y región antes de activarlo. Guardar el JSON en `secrets/firebase.json`, ignorado, o como secreto del servicio. No pegarlo en chat, web, firmware o documentación.

Usar una sola vía de credencial y reiniciar el proceso tras cambiar variables. Compose usa `env_file`; la ejecución nativa usa `--env-file backend/.env`. La web no carga ese archivo ni recibe sus secretos.

Las reglas iniciales deniegan acceso directo de clientes. Admin SDK usa IAM y no está restringido por esas reglas. La autorización por cuadro está pendiente y debe resolverse antes de distribuir enlaces reales.

El token de enlace del producto estará preparado por cuadro y será visible para quien acceda a él por diseño; no concede administración del proyecto Firebase. Una variable `.env` que termina en JavaScript no queda oculta. `.env.example` debe mantener privados vacíos y ejemplos inequívocos.
