# API del prototipo: endpoints y ejemplos

Este catálogo describe las nueve operaciones implementadas en `backend/main.py`. Todas salvo `/health` requieren el identificador del cuadro en Bearer como selector de ámbito, no como autenticación. Cualquier identificador válido crea o recupera automáticamente su registro. API y cliente directo calculan el mismo SHA-256 UTF-8 para aislar datos y medios; los huecos son `0`, `1`, `2` en HTTP y «01», «02», «03» en la interfaz. No hay usuarios ni lista de cuadros autorizados: quien use un identificador puede leer y cambiar ese ámbito por API. Por decisión expresa de Carlos, RTDB/Storage permiten además lectura sin sesión a quien conozca las URLs concretas, mientras sus reglas bloquean listados y escrituras públicas. Ver [Firebase](../firebase/README.md).

## Arranque y variables para los ejemplos

Sigue primero [backend/README.md](../backend/README.md). Desde la raíz, con `.venv` activado, la API arrancada y `backend/.env` generado:

```bash
export API_BASE='http://127.0.0.1:8000'
export FRAME_ID='mi-cuadro-prueba'
```

El identificador del cuadro tiene entre 1 y 128 caracteres ASCII: letra o número inicial, seguidos de letras, números, guion o guion bajo. `mi-cuadro-prueba` es válido. No es un secreto; la cabecera Bearer solo conserva el transporte existente y no concede ni comprueba permisos. En Swagger, «Authorize» recibe el identificador sin el prefijo `Bearer`. Después, `unset FRAME_ID` lo retira de esa terminal.

Las operaciones de cuadro requieren `Authorization: Bearer ...` con un identificador válido. Ausente o mal formado: 401. El primer `GET /state` crea `slots` y `jobs` vacíos; las peticiones posteriores recuperan el mismo estado. Identificadores distintos generan ámbitos independientes. Las validaciones del cuerpo producen 422, con detalles de Pydantic. Los ejemplos de respuesta son ilustrativos; IDs y tiempos reales cambian.

| Método | Ruta | Acceso | Uso |
|---|---|---|---|
| GET | `/health` | Público | Proceso y presencia de configuración. |
| POST | `/search` | Bearer del cuadro | Buscar candidatos en YouTube. |
| POST | `/stations/search` | Bearer del cuadro | Buscar emisoras en Radio Browser. |
| POST | `/imports` | Bearer del cuadro | Crear una tarea en el ámbito del cuadro. |
| GET | `/state` | Bearer del cuadro | Consultar sus huecos y tareas. |
| POST | `/jobs/{job_id}/cancel` | Bearer del cuadro | Solicitar cancelación de una tarea propia. |
| POST | `/stations` | Bearer del cuadro | Guardar una radio en un hueco propio. |
| DELETE | `/slots/{slot}` | Bearer del cuadro | Vaciar un hueco y cancelar sus tareas. |
| GET | `/media/{slot}` | Bearer del cuadro | Obtener URL de escucha e imagen del cuadro. |

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
  -H "Authorization: Bearer $FRAME_ID" \
  -H 'Content-Type: application/json' \
  -d '{"artist":"Weezer","title":"Island in the Sun"}'
```

Forma de respuesta 200 (ID y datos sintéticos, no una disponibilidad acreditada):

```json
{"results":[{"id":"abcdefghijk","title":"Título del resultado","artist":"Canal","duration":214,"image":"https://i.ytimg.com/vi/abcdefghijk/mqdefault.jpg"}]}
```

Puede haber una lista vacía o duración desconocida. 502 significa que la fuente o la búsqueda fallaron; no implica un problema de Firebase. Una búsqueda correcta no prueba la descarga desde Render.

## POST /stations/search

Busca hasta 12 emisoras por nombre y, opcionalmente, país. El backend consulta Radio Browser con timeout de 12 segundos, pide excluir estaciones marcadas como caídas y descarta resultados sin nombre o sin URL HTTPS válida. No abre ni prueba las URL devueltas. Radio Browser es un directorio comunitario sin garantía de disponibilidad; su respuesta no acredita que el stream siga activo o sea compatible con el navegador o el ESP32.

| Campo JSON | Tipo | Restricción |
|---|---|---|
| `name` | string | Entre 1 y 100 caracteres. |
| `country` | string o null | Opcional, máximo 100 caracteres. |

```bash
curl -sS "$API_BASE/stations/search" \
  -H "Authorization: Bearer $FRAME_ID" \
  -H 'Content-Type: application/json' \
  -d '{"name":"Radio Nacional","country":"Spain"}'
```

Respuesta 200: `{"results":[{"stationuuid":"id-radio","name":"Radio Nacional","country":"Spain","url":"https://stream.example/radio","favicon":null,"homepage":null,"codec":"MP3","bitrate":128}]}`. Los valores son ilustrativos. Puede devolver cero resultados. 401 si falta o no es válido el identificador; 422 para cuerpo no válido; 502 si Radio Browser falla o no responde. La búsqueda no modifica el estado del cuadro.

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
  -H "Authorization: Bearer $FRAME_ID" \
  -H 'Content-Type: application/json' \
  -d '{"slot":0,"source_id":"abcdefghijk","title":"Título elegido","artist":"Artista elegido"}'
```

Forma de respuesta 202:

```json
{"slot":0,"source_id":"abcdefghijk","title":"Título elegido","artist":"Artista elegido","id":"id-de-tarea","status":"queued","percent":null,"message":"Esperando turno","created_at":1700000000.0}
```

Errores: 503 si falta configuración Storage; 409 si el cuadro ya tiene una tarea activa, incluso en otro hueco; 422 si el cuerpo no cumple restricciones. No hay clave de idempotencia: repetir una petición después de acabar/cancelar puede crear una tarea nueva.

La selección anterior se conserva hasta completar audio, imagen y publicación. Estados: `queued`, `downloading`, `processing`, `uploading`, `ready`, `error`, `cancelled`. `percent` puede ser `null` y, en descarga, `estimated` puede marcar una estimación. El porcentaje es de la etapa, no del proceso completo.

## GET /state

```bash
curl -sS "$API_BASE/state" \
  -H "Authorization: Bearer $FRAME_ID"
```

Respuesta inicial 200:

```json
{"slots":{},"jobs":{}}
```

Los huecos se indexan por `slot-0`, `slot-1`, `slot-2`; las tareas por su `id`. Una canción lista contiene `id`, `kind: "song"`, `title`, `artist`, `source_id`, `duration`, `audio_key`, `image_key` y `created_at`. Una emisora contiene `id`, `kind: "station"`, `title`, `artist` y `url`. El estado corresponde al identificador Bearer. En Firebase, la ruta `slots` se lee sin autenticación y su URL conocida permite acceder a esos datos; las tareas no se incluyen en esa ruta pública. Una primera consulta API con su identificador crea y persiste el estado vacío del cuadro; las siguientes reutilizan el mismo registro.

Las tareas incluyen los datos de solicitud, estado, mensaje, porcentaje y marcas temporales que se hayan publicado. El prototipo consulta esta ruta periódicamente para mostrar progreso. No hay SSE ni un endpoint de consulta individual de tarea implementado; usar `jobs[job_id]`. La poda actual conserva un número limitado de tareas finalizadas y aún debe revisarse.

## POST /jobs/{job_id}/cancel

En la terminal, define `JOB_ID` con el `id` devuelto por `/imports`. Para probar el caso 404 puede usarse el ID sintético siguiente:

```bash
export JOB_ID='tarea-inexistente-de-prueba'
curl -sS -X POST "$API_BASE/jobs/$JOB_ID/cancel" \
  -H "Authorization: Bearer $FRAME_ID"
```

200: `{"ok":true}` si la tarea existe; 404: `{"detail":"Tarea no encontrada."}` si no existe. Si está activa, se solicita la cancelación y el worker la comprueba durante el proceso. Una respuesta 200 no prueba que todos los archivos remotos hayan sido eliminados. Si ya es terminal, devuelve `ok` sin revertir una canción publicada.

Para reintentar, la interfaz vuelve a llamar a `/imports` con los datos originales y obtiene un ID nuevo. No hay endpoint `/retry` en esta base. Tareas y cancelación están aisladas por cuadro. Persistencia de cancelación y recuperación fiable siguen pendientes de adaptación.

## POST /stations

Guarda una emisora en el hueco. Acepta URL manual o los metadatos de la selección de Radio Browser; no comprueba el contenido del stream. Puede sustituir el registro anterior; después intenta eliminar medios sin referencias.

| Campo JSON | Tipo | Restricción |
|---|---|---|
| `slot` | integer | 0, 1 o 2. |
| `title` | string | Entre 1 y 100 caracteres. |
| `url` | string | Máximo 1000 caracteres; HTTPS con hostname y sin usuario/contraseña. |
| `stationuuid`, `country`, `homepage`, `favicon`, `codec` | string o null | Metadatos opcionales del directorio; límites definidos en OpenAPI. |
| `bitrate` | integer o null | Opcional, entre 0 y 100000. |

Ejemplo sintético para comprobar el contrato en **desarrollo local**; el enlace no es una emisora funcional:

```bash
curl -sS "$API_BASE/stations" \
  -H "Authorization: Bearer $FRAME_ID" \
  -H 'Content-Type: application/json' \
  -d '{"slot":2,"title":"Radio de prueba local","url":"https://example.org/stream.mp3"}'
```

200: `{"ok":true}`. 409 si el cuadro tiene una importación activa. 422 si no cumple las restricciones. El backend no obtiene esta URL; aceptar su forma no acredita reproducción. La selección de Radio Browser conserva también los metadatos descritos arriba; la compatibilidad real aún debe validarse.

## DELETE /slots/{slot}

Modifica datos. Ejecutar el siguiente ejemplo solo sobre el hueco local de prueba del apartado anterior:

```bash
curl -sS -X DELETE "$API_BASE/slots/2" \
  -H "Authorization: Bearer $FRAME_ID"
```

200: `{"ok":true,"deleted_objects":2,"cleanup_pending":false}`; el contador puede ser 0. Vaciar un hueco ya vacío también devuelve 200 y reintenta la limpieza de objetos huérfanos del cuadro. 422 para índices fuera de 0–2. Cancela las tareas relacionadas, retira la selección y elimina de Storage todo objeto del cuadro que ya no esté referenciado por otro hueco ni pertenezca a una importación activa. Si Firebase falla, `cleanup_pending` es `true`; la limpieza se vuelve a intentar al reiniciar la API o al vaciar otro hueco. Al iniciar, la API también limpia medios sin referencias. El reproductor local se detiene al vaciar su favorito; no hay hardware ni seguimiento de reproducciones del ESP32 todavía.

## GET /media/{slot}

```bash
curl -sS "$API_BASE/media/0" \
  -H "Authorization: Bearer $FRAME_ID"
```

200 para una emisora:

```json
{"audio_url":"https://example.org/stream.mp3","image_url":null}
```

Para una canción, devuelve URLs directas estables de Storage, legibles sin sesión mientras siga vigente la regla de acceso por URL conocida. Ejemplo ficticio de la forma de `audio_url`: `https://firebasestorage.googleapis.com/v0/b/example-sonoro.firebasestorage.app/o/private%2Fframes%2F<sha256>%2F<job>%2Faudio.mp3?alt=media`. Cualquiera que conozca esta URL podrá descargar el archivo. La ruta devuelve JSON, no el MP3: abrir `audio_url` en el reproductor del navegador, que hace su petición directa. No envía comandos al ESP32. Un hueco sin contenido devuelve 404: `{"detail":"Espacio vacío."}`.

El endpoint sigue recibiendo el Bearer para seleccionar el registro del cuadro, pero construir la URL no contacta Firebase ni firma un enlace temporal. Se requiere `FIREBASE_STORAGE_BUCKET`; sin bucket responde 503. El ESP32 no depende de este endpoint durante la reproducción: obtiene `audio_key` desde RTDB y forma la URL directa descrita en [Firebase](../firebase/README.md). Un hueco sin contenido devuelve 404: `{"detail":"Espacio vacío."}`.

## Qué no está implementado

El SHA-256 del identificador válido deriva el ámbito: RTDB guarda cada uno bajo `frames/{sha256}`; SQLite local usa filas independientes en `frame_states`; los objetos nuevos de Storage se guardan bajo `private/frames/{sha256}/{job_id}/`. No hay lista de IDs ni usuarios. Los registros antiguos de `prototypes/sonoro` y la tabla local `state` no se migran porque no identifican un cuadro de forma fiable. La búsqueda de Radio Browser ya está disponible; no existen aún imagen decorativa, estado de dispositivo ni comandos remotos. No añadir rutas de reproducir/detener/volumen del cuadro: no pertenecen al alcance inicial.

Consultar [PRUEBA_API.md](PRUEBA_API.md) para el orden de prueba, [ESTADO.md](ESTADO.md) para las diferencias con el producto y [VALIDACION.md](VALIDACION.md) para la evidencia ejecutada.
