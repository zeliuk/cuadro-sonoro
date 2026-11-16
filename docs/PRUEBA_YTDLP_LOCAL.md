# Probar descargas con yt-dlp en el equipo local

Esta variante descarga la canción en la máquina donde se ejecuta FastAPI. Apify sigue disponible en el selector de la web. No se usa Docker para esta guía. La integración yt-dlp no se ha validado todavía contra YouTube ni Firebase reales.

## Requisitos

- Linux ARM64 (por ejemplo Raspberry Pi OS de 64 bits) o macOS; equipo encendido mientras se descarga.
- Python 3.12, salida a Internet y acceso de red a YouTube.
- FFmpeg y ffprobe instalados en el sistema.
- Deno 2 y las dependencias Python del proyecto (`yt-dlp[default]` y `yt-dlp-ejs`). yt-dlp requiere un runtime JavaScript compatible para el soporte completo actual de YouTube. Sigue las instrucciones oficiales de [Deno](https://docs.deno.com/runtime/getting_started/installation/) si todavía no está instalado.
- Firebase RTDB/Storage y credenciales privadas para publicar una importación real. La credencial se configura únicamente en `backend/.env`; Storage requiere el producto y la facturación configurados en Firebase.

La API mantiene archivos temporales de descarga solo durante la importación. El equipo debe tener espacio temporal suficiente para un archivo de hasta 40 MiB, el audio convertido y la portada.

## Instalar dependencias

Comandos desde la raíz del repositorio. En Debian/Raspberry Pi OS:

```bash
sudo apt update
sudo apt install -y ffmpeg python3.12 python3.12-venv
```

En macOS con Homebrew:

```bash
brew install ffmpeg deno
```

Instala Deno desde su guía oficial en Linux y comprueba que `deno` esté en el `PATH` de la misma terminal que arrancará Uvicorn. Luego instala el backend:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements-dev.txt
python scripts/setup_local.py
```

Completa `backend/.env` con Firebase RTDB, Storage y la credencial privada descritas en [CONFIGURACION.md](CONFIGURACION.md). Para `provider=yt_dlp`, `APIFY_TOKEN` puede permanecer vacío. No uses valores ficticios para simular Firebase Storage. En un entorno destinado a Apify conserva su token en esa misma configuración backend.

Comprueba las herramientas sin mostrar credenciales:

```bash
python --version
ffmpeg -version
ffprobe -version
deno --version
```

## Arrancar API y web en el mismo equipo

En una terminal, desde la raíz, con el entorno virtual activo:

```bash
source .venv/bin/activate
python -m uvicorn backend.main:app --env-file backend/.env --host 127.0.0.1 --port 8000 --workers 1
```

Mantén esta terminal abierta para ver logs. En otra terminal sirve los estáticos:

```bash
python3 -m http.server 5173 --bind 127.0.0.1 --directory web
```

Antes de abrirla, configura el `meta[name="sonoro-api-base"]` en la copia local de `web/index.html` como `http://127.0.0.1:8000`; no cambies la URL Render versionada para una instalación permanente. Abre `http://127.0.0.1:5173` en el mismo equipo y usa un identificador de prueba en el enlace local. En el formulario de canción elige «yt-dlp (este servidor)».

## Usar una Raspberry Pi desde un móvil en la LAN

Instala backend y dependencias en la Raspberry Pi. Asigna a la Pi una dirección estable en el router y arranca Uvicorn en una interfaz LAN (por ejemplo, sustituye `--host 127.0.0.1` por `--host 0.0.0.0`). Esto hace que el puerto de API sea alcanzable desde la red local; limita el acceso con el firewall/router de confianza y no lo publiques en Internet. Configura CORS en `backend/.env` para el origen exacto de la web servida desde ESP32/Mac, por ejemplo `ALLOWED_ORIGINS=http://cuadro-sonoro-dev001.local`, o usa el patrón local ya documentado si coincide con el hostname. Prepara una copia de la web servida en esa instalación con `meta[name="sonoro-api-base"]` apuntando a `http://<IP-o-hostname-de-la-Pi>:8000`. El teléfono abre la web local y llama a esa API; selecciona «yt-dlp (este servidor)» para ejecutar la descarga en la Pi.

No uses `127.0.0.1` en el móvil: señalaría al propio teléfono. La estabilidad del hostname mDNS, CORS y la conectividad entre móvil, ESP32 y Raspberry Pi deben probarse en la red concreta. La API actual no autentica personas y el identificador del cuadro no es una credencial; no expongas el puerto API fuera de la red doméstica.

La búsqueda y descarga contactan YouTube. El proceso descarga el audio seleccionado, lo convierte a MP3 de 128 kbps con FFmpeg, limita el archivo a 40 MiB y la duración a 15 minutos, y después sigue el mismo procesamiento/subida/publicación que Apify. Una selección anterior se mantiene hasta completar la publicación. yt-dlp no requiere `APIFY_TOKEN`; la opción Apify sí.

## API y registros

Comprueba el estado del servicio:

```bash
curl -sS http://127.0.0.1:8000/health
```

`/search` conserva el mismo contrato. Para crear una tarea yt-dlp, tras seleccionar un ID real devuelto por `/search`:

```bash
API_BASE=http://127.0.0.1:8000
FRAME_ID=cuadro-prueba-local
curl -sS "$API_BASE/imports" \
  -H "Authorization: Bearer $FRAME_ID" \
  -H 'Content-Type: application/json' \
  -d '{"slot":0,"source_id":"abcdefghijk","title":"Título seleccionado","artist":"Artista seleccionado","provider":"yt_dlp"}'
```

El ID anterior es ficticio y no es una selección válida garantizada; reemplázalo por el ID que elegiste en la búsqueda. Para Apify cambia `provider` a `apify`; ese servicio requiere un token válido y puede generar consumo. El detalle completo de métodos, respuestas y errores está en [API.md](API.md).

Los logs aparecen en la terminal de Uvicorn. Busca `import_checkpoint` y las etapas `source_download`, `audio_validation`, `cover_processing`, `firebase_upload` y `publish`. yt-dlp puede fallar por cambios de YouTube, disponibilidad del vídeo, límites de red o falta del runtime JavaScript. No se reintenta automáticamente una descarga que falla; vuelve a elegir el proveedor o la versión desde la web.

## Detener

Pulsa `Ctrl+C` en las dos terminales. La tarea aceptada se guarda y el ciclo de vida puede recuperarla al volver a iniciar el backend. No borres archivos de estado ni medios reales como limpieza rutinaria.

La elección yt-dlp solo indica dónde intentará descargar la API; no garantiza que YouTube permita la solicitud. La integración con servicios reales y la operación continua en Raspberry Pi quedan pendientes de validación.
