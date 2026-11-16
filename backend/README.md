# API: instalar, arrancar y probar

**Todos los comandos parten de la raíz `cuadro-sonoro/`, no de esta carpeta.** La API aísla configuración, tareas y objetos nuevos por identificador Bearer del cuadro; el identificador solo selecciona un ámbito y no autentica usuarios. Ver [límites](../docs/ESTADO.md). La web versionada apunta a Render. Para probar la descarga con backend local, cambia temporalmente el meta a `http://127.0.0.1:8000`, sirve `web/` estática y arranca esta API. Ver [PRUEBA_RAPIDAPI.md](../docs/PRUEBA_RAPIDAPI.md).

## Requisitos e instalación nativa

Python 3.12. La búsqueda usa yt-dlp y requiere salida a YouTube; la extracción necesita un runtime JavaScript compatible (Deno en Docker) y `yt-dlp-ejs`. La descarga del resultado elegido usa RapidAPI (`RAPIDAPI_KEY` y `RAPIDAPI_USERNAME`, solo en backend) y requiere además FFmpeg/ffprobe y Firebase Storage para publicar.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements-dev.txt
python scripts/setup_local.py
python scripts/check_project.py
```

El script crea `backend/.env` a partir de la plantilla. Añade allí `RAPIDAPI_KEY` y el username de RapidAPI (`RAPIDAPI_USERNAME`); solo se usan desde el backend. La llamada RapidAPI prepara un enlace MP3 y el backend descarga el medio a almacenamiento temporal, valida formato y duración y lo publica en Firebase. No hacen falta tokens locales ni listas de cuadros: usa como Bearer un identificador como `mi-cuadro-prueba`. `requirements-dev.txt` incluye las dependencias de ejecución y las de tests.

## Arranque nativo

```bash
python -m uvicorn backend.main:app --env-file backend/.env --host 127.0.0.1 --port 8000 --workers 1
```

Mantén esa terminal abierta. Verás los logs ahí; `Ctrl+C` detiene el proceso. El apagado ordenado deja las tareas vigentes en cola; si el proceso cae sin apagarse, al siguiente inicio se recuperan hasta dos veces desde el principio. Después la tarea queda en error con instrucciones para cancelarla y volver a crearla. Usa siempre `--workers 1`.

### Diagnosticar importaciones

Cada importación emite líneas `import_checkpoint` en los logs del proceso. En Docker local consulta `docker compose logs -f api`; en Render usa el panel Logs. Busca etapas `source_download`, `audio_validation`, `cover_processing`, `firebase_upload` y `publish`. La clave RapidAPI no se registra ni se entrega al navegador. La limpieza puede fallar después de una importación completada sin revertir la publicación.

La tarjeta de la web seguirá mostrando un mensaje general para los fallos de importación. Usa el detalle de los logs del backend para localizar la etapa; no compartas capturas o registros sin revisar que no contengan datos privados.

En otra terminal:

```bash
curl -sS http://127.0.0.1:8000/health
```

Sin Firebase se espera `{"ok":true,"storage_configured":false,"durable_state":false}`. Las banderas no prueban conectividad. La búsqueda de emisoras usa Radio Browser y requiere salida HTTPS a Internet; si el proveedor no responde, `POST /stations/search` devuelve 502. La API no prueba ni descarga las URL de stream.

El identificador Bearer debe tener entre 1 y 128 caracteres ASCII: letras, números, guion o guion bajo; no se compara con ningún registro. Cualquier persona que conozca un identificador puede leer o cambiar los datos de su ámbito mediante la API. Sin Storage configurado, la importación devuelve 503.

Abre [Swagger UI](http://127.0.0.1:8000/docs), [ReDoc](http://127.0.0.1:8000/redoc) o [OpenAPI JSON](http://127.0.0.1:8000/openapi.json). En Swagger, «Authorize» recibe el identificador, sin el prefijo `Bearer`. Usa el catálogo con ejemplos de [API.md](../docs/API.md) y el recorrido de [PRUEBA_API.md](../docs/PRUEBA_API.md).

## Arranque con Docker Compose

Requiere Docker instalado y activo. Desde la raíz:

```bash
python3 scripts/setup_local.py
docker compose config --quiet
docker compose up --build -d
docker compose ps
docker compose logs --tail=100 api
```

Compose inicia API y web en puertos locales 8000 y 5173. La primera construcción descarga dependencias y puede tardar. `config --quiet` valida sin volcar las variables privadas; no compartir una salida expandida de configuración.

Para Firebase real, conserva en `backend/.env` la ruta nativa absoluta de `GOOGLE_APPLICATION_CREDENTIALS` y guarda una copia privada montable en `secrets/firebase.json`. `compose.yaml` sustituye la ruta solo dentro de la API por `/run/secrets/firebase.json`; el montaje es de solo lectura. La copia no se versiona. La alternativa `FIREBASE_SERVICE_ACCOUNT_JSON` debe quedar vacía.

Parar sin borrar configuración:

```bash
docker compose stop
```

Reiniciar procesos existentes:

```bash
docker compose start
```

Tras cambiar código, reconstruir con `docker compose up --build -d`. Tras cambiar `.env`, recrear con `docker compose up -d --force-recreate api` (un simple restart no recarga el entorno). SQLite local se guarda en el volumen nombrado `sonoro-state`, que sobrevive a reinicios, recreación de API y `docker compose down`. `docker compose down -v` elimina deliberadamente el volumen y sus datos; Firebase y `.env` no están en él.

### Recorrido Docker de recuperación

Este recorrido solo escribe datos sintéticos en el volumen local y no necesita credenciales Firebase ni acceso a YouTube:

```bash
docker compose -f compose.recovery.yaml up -d --build api
docker compose -f compose.recovery.yaml exec api python /app/scripts/docker_import_recovery.py seed
docker compose -f compose.recovery.yaml kill api
docker compose -f compose.recovery.yaml run --rm api python /app/scripts/docker_import_recovery.py recover
docker compose -f compose.recovery.yaml run --rm api python /app/scripts/docker_import_recovery.py show
```

`seed` crea una tarea ficticia en fase `uploading`; `kill` simula una caída abrupta. `recover` ejecuta la misma función de recuperación del arranque y debe mostrar estado `queued`, `recoveries: 1` y mensaje de repetición desde el inicio. `show` lee el registro desde un contenedor distinto que monta el mismo volumen. La configuración de recuperación tiene un proyecto y volumen propios, no carga `.env` ni monta `secrets/`; no llama a proveedores. La limpieza de Storage reintenta restos al arrancar, al terminar/cancelar importaciones y cada cinco minutos mientras la API está inactiva.

La configuración `compose.recovery.yaml` no carga `backend/.env`, no monta `secrets/` y usa el volumen independiente `recovery-state`, por lo que el recorrido queda aislado incluso si el Compose normal apunta a Firebase. `docker compose -f compose.recovery.yaml down -v` borra solo los datos sintéticos de este recorrido.

En el Compose normal, `docker compose restart api` reinicia el contenedor existente. `docker compose up -d --force-recreate api` lo reemplaza conservando el volumen. `docker compose down -v` borra el volumen de desarrollo.

## Pruebas aisladas

Con `.venv` activado, desde la raíz:

```bash
env -u FIREBASE_DATABASE_URL -u FIREBASE_STORAGE_BUCKET -u FIREBASE_SERVICE_ACCOUNT_JSON -u GOOGLE_APPLICATION_CREDENTIALS python -m pytest backend/tests scripts/tests -q
python -m compileall -q backend scripts
```

Las pruebas usan identificadores sintéticos y SQLite temporal, simulando descarga/subida. No acreditan acceso real a YouTube ni Firebase. Para ejecutar tests dentro de Docker hace falta instalar también las dependencias de desarrollo: la imagen de ejecución no incluye pytest por defecto.

## Firebase y despliegue

Para una prueba real, usar recursos dedicados y completar el entorno según [CONFIGURACION.md](../docs/CONFIGURACION.md). Nativo: ruta absoluta de la cuenta de servicio en `GOOGLE_APPLICATION_CREDENTIALS`. Compose: archivo privado `secrets/firebase.json` y ruta `/run/secrets/firebase.json`, dejando vacía la alternativa JSON.

La configuración e importación RapidAPI están descritas en [PRUEBA_RAPIDAPI.md](../docs/PRUEBA_RAPIDAPI.md); la integración no se ha probado con cuota ni servicios Firebase reales en esta variante. El acceso desde firmware y la migración manual de datos antiguos dedicados quedan para fases posteriores. No usar varios workers/réplicas todavía. El inicio de API y el vaciado de un hueco eliminan objetos de Storage que ya no estén referenciados por una selección; fallos quedan pendientes para el siguiente intento.
