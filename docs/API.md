# API del prototipo: endpoints y ejemplos

Este catálogo describe **las ocho operaciones que existen en `backend/main.py`**, no un contrato multicuadro ya terminado. Las rutas cambiarán al implementar aislamiento por cuadro y se actualizarán junto al código. Hoy hay una colección global; los huecos son `0`, `1`, `2` en HTTP y «01», «02», «03» en la interfaz.

## Arranque y variables para los ejemplos

Sigue primero [backend/README.md](../backend/README.md). Desde la raíz, con `.venv` activado, la API arrancada y `backend/.env` generado:

```bash
export API_BASE='http://127.0.0.1:8000'
export API_TOKEN="$(python -c 'from dotenv import dotenv_values; print(dotenv_values("backend/.env").get("IMPORT_API_TOKEN", ""))')"
```

El segundo comando carga el token privado sin imprimirlo. No ejecutar con traza de shell (`set -x`), compartir variables o pegar tokens en documentos. Después de las pruebas, `unset API_TOKEN` lo retira de esa terminal. En Swagger, «Authorize» recibe el valor sin el prefijo `Bearer`.

Las operaciones privadas requieren `Authorization: Bearer ...`. Token de servidor vacío: 503; credenciales ausentes o incorrectas: 401. Las validaciones de entrada producen 422, con detalles de Pydantic. Los ejemplos de respuesta son ilustrativos; IDs y tiempos reales cambian.

| Método | Ruta | Acceso | Uso |
|---|---|---|---|
| GET | `/health` | Público | Proceso y presencia de configuración. |
| POST | `/search` | Token | Buscar candidatos en YouTube. |
| POST | `/imports` | Token | Crear una tarea de importación. |
| GET | `/state` | Token | Consultar huecos y tareas. |
| POST | `/jobs/{job_id}/cancel` | Token | Solicitar cancelación. |
| POST | `/stations` | Token | Guardar una radio por URL, todavía sin Radio Browser. |
| DELETE | `/slots/{slot}` | Token | Vaciar un hueco y cancelar sus tareas. |
| GET | `/media/{slot}` | Token | Obtener URL de escucha e imagen. |

Documentación automática: [Swagger](http://127.0.0.1:8000/docs), [ReDoc](http://127.0.0.1:8000/redoc) y [OpenAPI](http://127.0.0.1:8000/openapi.json). Se incluye también el [esquema exportado del prototipo](openapi.prototype.json). No son endpoints de control del ESP32.

## GET /health

```bash
curl -sS "$API_BASE/health"
```

Respuesta 200 sin nube:

```json
{"ok":true,"storage_configured":false,"durable_state":false}
```

`storage_configured` indica que hay un nombre de bucket en el entorno; `durable_state` que hay una URL RTDB y se ha seleccionado ese modo. No verifican permisos, existencia de recursos, descarga ni subida. El inicio del proceso puede fallar si se configuró una nube inaccesible.

## POST /search

Busca hasta cinco resultados a partir de artista y título. Requiere dependencias/red; no descarga audio ni modifica huecos. Filtra directos y resultados que excedan la duración del prototipo cuando ese dato está disponible.

| Campo JSON | Tipo | Restricción |
|---|---|---|
| `artist` | string | Entre 1 y 120 caracteres. |
| `title` | string | Entre 1 y 160 caracteres. |

```bash
curl -sS "$API_BASE/search" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"artist":"Weezer","title":"Island in the Sun"}'
```

Forma de respuesta 200 (ID y datos sintéticos, no una disponibilidad acreditada):

```json
{"results":[{"id":"abcdefghijk","title":"Título del resultado","artist":"Canal","duration":214,"image":"https://i.ytimg.com/vi/abcdefghijk/mqdefault.jpg"}]}
```

Puede haber una lista vacía o duración desconocida. 502 significa que la fuente o la búsqueda fallaron; no implica un problema de Firebase. Una búsqueda correcta no prueba la descarga desde Render.

## POST /imports

Crea una tarea, sin esperar a que termine. Requiere Storage configurado; el worker necesitará también credenciales y datos Firebase válidos para completar el proceso. Crea/actualiza registros y, si termina, archivos y el hueco. Probar solo con recursos dedicados.

| Campo JSON | Tipo | Restricción |
|---|---|---|
| `slot` | integer | 0, 1 o 2. |
| `source_id` | string | ID del resultado, exactamente 11 caracteres de letras, números, `_` o `-`. |
| `title` | string | Entre 1 y 200 caracteres. |
| `artist` | string | Entre 1 y 200 caracteres. |

El siguiente ID es sintético: sustituirlo por uno seleccionado realmente en `/search` antes de ejecutar una importación real.

```bash
curl -sS "$API_BASE/imports" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"slot":0,"source_id":"abcdefghijk","title":"Título elegido","artist":"Artista elegido"}'
```

Forma de respuesta 202:

```json
{"slot":0,"source_id":"abcdefghijk","title":"Título elegido","artist":"Artista elegido","id":"id-de-tarea","status":"queued","percent":null,"message":"Esperando turno","created_at":1700000000.0}
```

Errores: 503 si falta configuración Storage; 409 si **ese hueco** ya tiene una tarea activa; 422 si el cuerpo no cumple restricciones. El producto exige una tarea por cuadro, pero el prototipo todavía limita por hueco. No hay clave de idempotencia: repetir una petición después de acabar/cancelar puede crear una tarea nueva.

La selección anterior se conserva hasta completar audio, imagen y publicación. Estados: `queued`, `downloading`, `processing`, `uploading`, `ready`, `error`, `cancelled`. `percent` puede ser `null` y, en descarga, `estimated` puede marcar una estimación. El porcentaje es de la etapa, no del proceso completo.

## GET /state

```bash
curl -sS "$API_BASE/state" \
  -H "Authorization: Bearer $API_TOKEN"
```

Respuesta inicial 200:

```json
{"slots":{},"jobs":{}}
```

Los huecos se indexan por `slot-0`, `slot-1`, `slot-2`; las tareas por su `id`. Una canción lista contiene `id`, `kind: "song"`, `title`, `artist`, `source_id`, `duration`, `audio_key`, `image_key` y `created_at`. Una emisora contiene `id`, `kind: "station"`, `title`, `artist` y `url`.

Las tareas incluyen los datos de solicitud, estado, mensaje, porcentaje y marcas temporales que se hayan publicado. El prototipo consulta esta ruta periódicamente para mostrar progreso. No hay SSE ni un endpoint de consulta individual de tarea implementado; usar `jobs[job_id]`. La poda actual conserva un número limitado de tareas finalizadas y aún debe revisarse.

## POST /jobs/{job_id}/cancel

En la terminal, define `JOB_ID` con el `id` devuelto por `/imports`. Para probar el caso 404 puede usarse el ID sintético siguiente:

```bash
export JOB_ID='tarea-inexistente-de-prueba'
curl -sS -X POST "$API_BASE/jobs/$JOB_ID/cancel" \
  -H "Authorization: Bearer $API_TOKEN"
```

200: `{"ok":true}` si la tarea existe; 404: `{"detail":"Tarea no encontrada."}` si no existe. Si está activa, se solicita la cancelación y el worker la comprueba durante el proceso. Una respuesta 200 no prueba que todos los archivos remotos hayan sido eliminados. Si ya es terminal, devuelve `ok` sin revertir una canción publicada.

Para reintentar, la interfaz vuelve a llamar a `/imports` con los datos originales y obtiene un ID nuevo. No hay endpoint `/retry` en esta base. Persistencia de cancelación, recuperación y limpieza están pendientes de adaptación.

## POST /stations

Guarda una emisora en el hueco. Hoy recibe la URL manualmente; no busca ni comprueba el contenido del stream. Puede sustituir el registro anterior y no elimina sus archivos remotos.

| Campo JSON | Tipo | Restricción |
|---|---|---|
| `slot` | integer | 0, 1 o 2. |
| `title` | string | Entre 1 y 100 caracteres. |
| `url` | string | Máximo 1000 caracteres; HTTPS con hostname y sin usuario/contraseña. |

Ejemplo sintético para comprobar el contrato en **desarrollo local**; el enlace no es una emisora funcional:

```bash
curl -sS "$API_BASE/stations" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"slot":2,"title":"Radio de prueba local","url":"https://example.org/stream.mp3"}'
```

200: `{"ok":true}`. 409 si el hueco tiene una importación activa. 422 si no cumple las restricciones. El backend no obtiene esta URL; aceptar su forma no acredita reproducción. Integrar Radio Browser y validación real en la fase prevista.

## DELETE /slots/{slot}

Modifica datos. Ejecutar el siguiente ejemplo solo sobre el hueco local de prueba del apartado anterior:

```bash
curl -sS -X DELETE "$API_BASE/slots/2" \
  -H "Authorization: Bearer $API_TOKEN"
```

200: `{"ok":true}`; vaciar un hueco ya vacío también devuelve 200. 422 para índices fuera de 0–2. Cancela las tareas relacionadas y retira la selección de la colección. **Todavía no elimina los MP3/carátulas de Storage** ni gestiona referencias de reproducción activa. La política final está en la definición y debe implementarse, no darse por hecha.

## GET /media/{slot}

```bash
curl -sS "$API_BASE/media/0" \
  -H "Authorization: Bearer $API_TOKEN"
```

200 para una emisora:

```json
{"audio_url":"https://example.org/stream.mp3","image_url":null}
```

Para una canción, devuelve URLs firmadas de Storage, con vigencia actual de 30 minutos. No incluirlas en Git, capturas o informes. La ruta devuelve JSON, no el MP3: abrir `audio_url` en el reproductor del navegador, que hace su petición directa. No envía comandos al ESP32. Un hueco sin contenido devuelve 404: `{"detail":"Espacio vacío."}`.

La generación de enlaces requiere configuración y credenciales capaces de firmar; errores de permisos/firma no tienen aún un contrato de errores completo y pueden producir 500. Deben manejarse al endurecer el backend, sin filtrar detalles sensibles.

## Qué no está implementado

No existen todavía endpoints por cuadro, búsqueda de Radio Browser, imagen decorativa, limpieza de huérfanos, estado de dispositivo ni comandos remotos. No añadir rutas de reproducir/detener/volumen del cuadro: no pertenecen al alcance inicial. Los límites definitivos y el acceso a medios para firmware se decidirán antes de esa integración.

Consultar [PRUEBA_API.md](PRUEBA_API.md) para el orden de prueba, [ESTADO.md](ESTADO.md) para las diferencias con el producto y [VALIDACION.md](VALIDACION.md) para la evidencia ejecutada.
