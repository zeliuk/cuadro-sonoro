# Preparar y ejecutar la prueba Apify en Render

La integración Apify está implementada, pero todavía no está validada con Actors reales ni desde Render. No se ha desplegado nada ni se ha iniciado ninguna ejecución de pago. Mantén una sola instancia y un worker (`--workers 1`): la cola durable y el límite global de esta prueba no coordinan varias instancias independientes.

## 1. Revisar los Actors y proteger el gasto

En la cuenta Apify, abre y acepta/revisa los términos y el plan de `streamers/youtube-scraper` y `lurkapi/youtube-to-mp3-audio-downloader`. Comprueba en sus páginas de Input/Output que el esquema siga igual. La página de Store muestra actualmente precios iniciales de $2.40/1,000 vídeos scrapeados para búsqueda y $2.00/1,000 minutos descargados para audio; pueden cambiar. El README del descargador indica cobro por minutos descargados exitosamente y fallos sin cargo del Actor; conservar archivos depende del plan. El cargo efectivo puede incluir uso de plataforma/proxies/plan según la configuración. Un límite de uso/gasto mensual de cuenta de Apify solo cubre lo que indique Apify para ese plan y no limita Render, Firebase, tráfico ni cargos externos. Configura además límites/cuotas en la cuenta y vigila su uso; la app limita a una importación simultánea global, 5 resultados, una descarga por URL, cooldown de búsquedas y caché de 5 minutos, pero no implementa un techo monetario total.

Los esquemas consultados están enlazados aquí: [buscador: entrada](https://apify.com/streamers/youtube-scraper/input-schema), [buscador: salida](https://apify.com/streamers/youtube-scraper/output-schema), [descargador: entrada](https://apify.com/lurkapi/youtube-to-mp3-audio-downloader/input-schema), [descargador: salida](https://apify.com/lurkapi/youtube-to-mp3-audio-downloader/output-schema) y [API de creación de run](https://docs.apify.com/api/v2/actors-runs-post). El buscador recibe `searchQueries`, `maxResults`, `maxResultsShorts` y `maxResultStreams`; la salida de duración es texto `HH:MM:SS`. El descargador recibe `videoUrls`, `audioFormat`, `audioBitrate` y `maxVideosPerUrl`; su dataset tiene resultado individual `status`/`error`, `audioFileUrl`, campos de thumbnail, metadata y duración. El código comprueba tanto el estado del run como el registro individual. API v2 admite `timeout` por ejecución; limita duración, pero no representa un techo monetario universal. La referencia de API indica que `maxTotalChargeUsd` no aplica a Actors pay-per-result; los Actors elegidos publican precios por resultado/minuto. Configura límites de uso de cuenta disponibles y supervisión manual; no presentes ninguno como tope de todos los cargos. Los Actors son productos de terceros mantenidos por sus autores y la compatibilidad/coste real debe confirmarse en una ejecución revisada.

## 2. Configurar el servicio en Render

En el servicio web `cuadro-sonoro`, añade/modifica estas variables desde **Environment**. No pongas secretos en Git, HTML, JavaScript, URL, capturas o chat.

| Variable | Valor | Tipo |
|---|---|---|
| `APIFY_TOKEN` | Token creado en Apify con permisos mínimos necesarios para iniciar/leer/abortar runs y leer datasets | **Secreto** |
| `APIFY_SEARCH_ACTOR` | `streamers/youtube-scraper` | Configuración |
| `APIFY_DOWNLOAD_ACTOR` | `lurkapi/youtube-to-mp3-audio-downloader` | Configuración |
| `APIFY_SEARCH_TIMEOUT_SECONDS` | `90` | Límite de espera por petición de búsqueda |
| `APIFY_RUN_TIMEOUT_SECONDS` | `180` por ciclo de worker; conserva run ID y reanuda si continúa | Límite |
| `APIFY_ACTOR_TIMEOUT_SECONDS` | `240` límite remoto enviado al crear cada ejecución | Límite |
| `APIFY_SEARCH_CACHE_SECONDS` | `300` | Frecuencia/caché |
| `APIFY_SEARCH_MIN_INTERVAL_SECONDS` | `2` | Frecuencia global |
| `APIFY_IMPORT_MIN_INTERVAL_SECONDS` | `10` | Frecuencia global de nuevas ejecuciones de descarga |
| `APIFY_MAX_ACTIVE_IMPORTS` | `1` | Concurrencia global |
| `ALLOWED_ORIGINS` | `http://127.0.0.1:5173,http://localhost:5173` (añadir solo orígenes exactos adicionales necesarios) | CORS exacto |
| `ALLOWED_ORIGIN_REGEX` | `^http://cuadro-sonoro-[a-z0-9-]+\.local$` | CORS hostname local existente |
| Firebase variables | Mantén los valores privados ya configurados para el servicio | Secretos/configuración |

No uses wildcard CORS. Confirma una sola instancia y comando de arranque con un worker. Render debe conservar almacenamiento durable compatible con el estado ya configurado; revisa que reiniciar servicio no borre la base. El cambio no convierte Render en un proveedor de importación validado hasta completar la prueba real.

Para obtener la credencial, abre Apify Console → **Settings → API & Integrations → Personal API tokens → Create a new token**. Pon una descripción específica (por ejemplo, “Cuadro Sonoro Render”), usa permisos/expiración mínimos compatibles con iniciar y consultar runs, datasets y abortar, y copia el valor a un gestor de contraseñas: Apify lo muestra una sola vez al crearlo/rotarlo. La guía oficial está en [API integration](https://docs.apify.com/integrations/api). En Render, agrega `APIFY_TOKEN` como **Environment Secret**, pega el valor allí directamente y no lo incluyas en `.env`, Git, web, logs ni chat. Si Render ya tiene `APIFY_TOKEN`, usa **Edit** para reemplazarlo sin mostrarlo. No lo compartas con Codex. Reinicia/redeploy desde el panel cuando hayas revisado el diff y aceptes iniciar la prueba. Este repositorio no lo despliega.

## 3. Desplegar y revisar logs

Revisa y confirma el commit en tu flujo habitual; después inicia el deploy manual en Render. En **Logs**, busca `import_checkpoint` y etapas `source_download`, `audio_validation`, `cover_processing`, `firebase_upload` y `publish`. No pegues logs sin revisar que no contengan identificadores de cuadros o datos privados. El backend redacta URLs y no registra el token de Apify.

Una creación POST cuya respuesta sea ambigua queda en error y se marca para revisión, sin volver a crear otro run. Antes de reintentar, localiza el run en la consola Apify y verifica su estado/coste. Si la ejecución sigue, deja que la tarea existente se recupere; si falló, cancélala explícitamente y crea una nueva solo después de revisar consumo. Un run remoto guardado en la tarea se consulta tras reinicio; no se crea otro run.

## 4. Prueba frontend local contra Render

Desde la raíz del repositorio:

```bash
python3 -m http.server 5173 --bind 127.0.0.1 --directory web
```

Abre [http://127.0.0.1:5173/#token=cuadro-prueba-apify](http://127.0.0.1:5173/#token=cuadro-prueba-apify). En DevTools → Network, confirma que las llamadas de API usan `https://cuadro-sonoro.onrender.com` y que `Authorization` viaja solo a ese backend. Las lecturas de reproducción desde Firebase son esperadas. El navegador no debe llamar a `api.apify.com` ni a `apify.com`. La web solo sirve estáticos: no hace falta arrancar Python/FastAPI en el ordenador.

1. Comprueba `/health` y que la página carga el cuadro de prueba vacío.
2. Busca artista y título, revisa resultados y elige explícitamente una versión autorizada para esta prueba.
3. Importa. Observa la etapa y, durante la transferencia a Render, el progreso medido si el servidor informa `Content-Length`.
4. Recarga la página mientras la tarea sigue activa; debe recuperar el estado desde API.
5. Al terminar, confirma el nuevo contenido en el hueco y reproduce el MP3. La publicación en Firebase debe ocurrir solo al final.
6. Para probar preservación: con una selección previa, inicia una canción no disponible o que falle el Actor. Espera el estado de error y confirma que la selección anterior sigue ahí. Cancelar debe impedir publicación tardía.
7. Revisa las ejecuciones y el uso/coste en Apify. Registra el resultado sin tokens, IDs privados ni URLs de Storage.

Si el navegador bloquea CORS, revisa el origen exacto y el preflight. Se conservan `http://127.0.0.1:5173`, `http://localhost:5173` y hostnames locales `cuadro-sonoro-*.local`; Authorization debe aparecer en `Access-Control-Allow-Headers`.

## 5. Volver a la versión anterior

En Render, selecciona el último deploy anterior a este cambio y haz rollback desde el panel. El frontend versionado aquí ahora apunta a la URL de Render: para volver al endpoint/configuración anterior restaura también `web/index.html` desde el commit anterior y vuelve a servirlo. Retira `APIFY_TOKEN` del servicio después de confirmar que no hay runs en curso; no borres la base durable ni selecciones Firebase. Verifica logs y `/health`. No borres los datasets/runs de Apify hasta revisar si son evidencia/coste de la prueba.
