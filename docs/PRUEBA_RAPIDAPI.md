# Configurar y probar la descarga con RapidAPI

Esta ruta mantiene la búsqueda de candidatos con yt-dlp y delega la preparación del MP3 a `youtube-mp36.p.rapidapi.com`. FastAPI consume la API HTTP de RapidAPI directamente; el MCP `mcp-remote` instalado en Codex no forma parte del proceso de la aplicación ni estará disponible en una Raspberry Pi. La clave solo se guarda en el backend.

## Requisitos y configuración

- Python 3.12, dependencias Python del proyecto, yt-dlp, `yt-dlp-ejs`, runtime JavaScript compatible (Deno en Docker), FFmpeg/ffprobe.
- Acceso HTTPS desde el backend a YouTube, RapidAPI, Firebase RTDB y Firebase Storage.
- Suscripción y cuota disponibles para YouTube MP3 en RapidAPI.

Desde la raíz, crea el entorno y la plantilla siguiendo [backend/README.md](../backend/README.md). En `backend/.env`, configura `RAPIDAPI_KEY` y `RAPIDAPI_USERNAME` para backend local. Para Render, configúralos por separado en el panel del servicio; el `.env` local no se publica ni sincroniza. `RAPIDAPI_USERNAME` es el username del perfil RapidAPI, no el correo ni la clave. El backend lo añade al `User-Agent` y usa el MD5 como cabecera `X-RUN`, según el workaround reportado para errores 403/404 del host de medios. Configura también Firebase Storage y RTDB en el entorno destino según [CONFIGURACION.md](CONFIGURACION.md). En Render permite el origen de la web mediante `ALLOWED_ORIGINS` o `ALLOWED_ORIGIN_REGEX` (por ejemplo, el hostname `.local` servido por Bonjour). Nunca pongas la clave en `web/`, HTML, firmware ni en el repositorio. La búsqueda no consume esta API; la conversión de cada descarga puede consumir cuota según el plan vigente.

La web versionada apunta a Render. Para probar una API local, cambia temporalmente `meta[name="sonoro-api-base"]` a `http://127.0.0.1:8000`; para Raspberry Pi, apunta la copia servida a `http://<IP-o-hostname-de-la-Pi>:8000` y configura CORS para el origen de la web. No publiques la API de desarrollo directamente en Internet.

## Arranque, URL y verificación

Activa `.venv` y arranca un solo worker:

```bash
python -m uvicorn backend.main:app --env-file backend/.env --host 127.0.0.1 --port 8000 --workers 1
curl -sS http://127.0.0.1:8000/health
```

Abre la web local y busca un tema. La búsqueda usa `POST /search`; al elegir una versión, la aplicación crea una tarea `POST /imports`. El backend consulta `GET https://youtube-mp36.p.rapidapi.com/dl?id=<ID>`, obtiene `link`, `filesize` y `duration`, descarga el MP3, comprueba el tamaño máximo y que se haya recibido todo el `Content-Length` anunciado por el servidor del archivo. `filesize` de RapidAPI se registra como referencia, pero no se trata como tamaño exacto. Después valida formato y duración, genera la portada y publica la selección en Firebase. Estas comprobaciones no acreditan por sí solas que el audio sea audible o corresponda a la selección.

No se ha ejecutado esta prueba en esta variante; no se afirma que una importación real, la cuota o la compatibilidad con Raspberry Pi estén verificadas. Una solicitud real a RapidAPI puede consumir cuota. Para una primera verificación, revisa el plan y saldo en RapidAPI antes de seleccionar una canción.

## Logs, límites y parada

Los logs de Uvicorn muestran `import_checkpoint` con fases `source_download`, `audio_validation`, `cover_processing`, `firebase_upload` y `publish`. No deben contener la clave. El importador limita el audio a 40 MiB y 15 minutos y usa un solo worker. Cancelar detiene la descarga en curso desde el backend, aunque no existe cancelación remota del trabajo de conversión ya solicitado a RapidAPI.

Detén Uvicorn con `Ctrl+C`; en Docker usa `docker compose stop`. Para revisar contrato, ejemplos y errores HTTP, consulta [API.md](API.md) y [PRUEBA_API.md](PRUEBA_API.md). Antes de desplegar, actualiza el secreto del entorno destino y apunta allí el frontend de esa instalación. No se ha desplegado ni se ha hecho una llamada pagada como parte de este cambio.
