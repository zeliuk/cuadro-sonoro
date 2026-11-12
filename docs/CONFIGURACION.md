# Configuración por entorno

El modo demo no necesita configuración de nube. Para el backend local, ejecuta desde la raíz `python3 scripts/setup_local.py`: crea `backend/.env` con un token aleatorio y valores de nube vacíos. Si ya existe, no lo sobrescribe ni imprime su contenido; si fue creado con el antiguo `IMPORT_API_TOKEN`, añade `LOCAL_FRAME_TOKEN` nuevo a la configuración local y deja las variables Firebase vacías para el modo de desarrollo.

| Variable actual | Función | Ubicación |
|---|---|---|
| `LOCAL_FRAME_TOKEN` | Token aleatorio local generado para los ejemplos HTTP. La API no lo carga como secreto global: cada petición presenta el token del cuadro como Bearer. | `.env` local; no se usa para autenticar el proceso. |
| `FRAME_TOKEN_HASHES` | Hashes SHA-256 hex de los tokens provisionados en producción, separados por comas. | Variable de entorno del servicio. |
| `ALLOWED_ORIGINS` | Orígenes exactos permitidos por CORS. | `.env`/Render. No sustituye autorización. |
| `FIREBASE_DATABASE_URL` | URL exacta de RTDB. Vacía: SQLite local. | `.env`/Render. |
| `FIREBASE_STORAGE_BUCKET` | Nombre del bucket sin `gs://`. Vacío: importación no disponible. | `.env`/Render. |
| `FIREBASE_WEB_API_KEY` | Identificador público del proyecto para Auth REST del dispositivo; no es una credencial Admin. | `.env` privado de aprovisionamiento. |
| `GOOGLE_APPLICATION_CREDENTIALS` | Ruta al JSON privado de cuenta de servicio. | Nativo: absoluta; Compose: `/run/secrets/firebase.json`. |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | Alternativa al archivo: JSON completo como secreto. | Render; dejar vacío si se usa archivo. |
| `STATE_DB` | SQLite local de desarrollo. El archivo no se versiona. | `.env`; valor inicial en `/tmp`. |
| `PORT` | Puerto del proceso Docker/Render; por defecto 8000. | Entorno de ejecución. |

El token de cuadro debe ser aleatorio y largo; generar uno con `python -c 'import secrets; print(secrets.token_urlsafe(32))'` por dispositivo y guardarlo en el sistema seguro usado para preparar el QR/NFC. Para calcular el valor de autorización sin mostrar el token durante la entrada:

```bash
python -c 'import getpass,hashlib; print(hashlib.sha256(getpass.getpass("Token del cuadro: ").encode()).hexdigest())'
```

Añadir ese hash hexadecimal a `FRAME_TOKEN_HASHES`, separado por comas si hay varios cuadros. Reiniciar el servicio después de cambiar la lista. La API recibe el token original en `Authorization: Bearer ...`, comprueba su hash permitido y usa el mismo hash como ámbito. El token original no se guarda en Firebase, SQLite, tareas o rutas de Storage. RTDB usa `frames/{sha256}`; SQLite usa filas independientes en `frame_states`. No hay token global ni endpoint para emitir tokens. `LOCAL_FRAME_TOKEN` solo facilita probar la API local cuando Firebase no está configurado; no se acepta en despliegues con Firebase. Los tokens previos de `IMPORT_API_TOKEN` ya no autentican.

Los datos de la antigua colección única no se asignan automáticamente a un cuadro: su identidad no se puede deducir de forma segura. En local, el nuevo código deja la tabla antigua sin uso y escribe en `frame_states`. No rellenar valores Firebase ficticios para saltarse el 503: no configuran recursos reales y provocan fallos del worker. `storage_configured` y `durable_state` en `/health` solo reflejan presencia de variables; no acreditan acceso.

## Firebase y acceso directo del dispositivo

Crear/configurar un proyecto dedicado y copiar desde su consola URL RTDB y nombre de bucket. Storage requiere Blaze: decidir facturación y región antes de activarlo. Guardar el JSON en `secrets/firebase.json`, ignorado, o como secreto del servicio. No pegarlo en chat, web, firmware o documentación.

Usar una sola vía de credencial y reiniciar el proceso tras cambiar variables. Compose usa `env_file`; la ejecución nativa usa `--env-file backend/.env`. La web no carga ese archivo ni recibe sus secretos.

Admin SDK usa IAM y no está restringido por reglas. La lectura directa está descrita y probada con emuladores en [firebase/README.md](../firebase/README.md): el desarrollador usa el token fijo existente para aprovisionar una cuenta técnica Auth; las reglas exigen UID coincidente para leer solo slots/medios del cuadro. No desplegar reglas en producción hasta probarlas en un proyecto dedicado y autorizado.

El token de enlace del producto estará preparado por cuadro y será visible para quien acceda a él por diseño; no concede administración del proyecto Firebase. Para el dispositivo es el secreto fijo de aprovisionamiento. ID token y refresh token Firebase son estado técnico renovable; no cambian el token del cuadro. Una variable `.env` que termina en JavaScript no queda oculta. `.env.example` debe mantener privados vacíos y ejemplos inequívocos. No versionar `device-private/`.
