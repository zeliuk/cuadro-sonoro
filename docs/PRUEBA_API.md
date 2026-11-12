# Probar la API paso a paso

## A. Comprobación local sin Firebase ni descargas

Esta prueba usa exclusivamente un entorno local dedicado. No arrancar con variables de nube de producción. Desde la raíz y con las dependencias instaladas, preparar y arrancar en una terminal:

```bash
source .venv/bin/activate
export STATE_DB="$(mktemp -t cuadro-sonoro-api)"
LOCAL_API_ENV="$(mktemp -t cuadro-sonoro-env)"
cat > "$LOCAL_API_ENV" <<EOF
STATE_DB=$STATE_DB
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
EOF
env -u FIREBASE_DATABASE_URL -u FIREBASE_STORAGE_BUCKET -u FIREBASE_SERVICE_ACCOUNT_JSON -u GOOGLE_APPLICATION_CREDENTIALS python -m uvicorn backend.main:app --env-file "$LOCAL_API_ENV" --host 127.0.0.1 --port 8000 --workers 1
```

En una segunda terminal, desde la misma raíz:

```bash
source .venv/bin/activate
export API_BASE='http://127.0.0.1:8000'
export FRAME_ID='mi-cuadro-prueba'
curl -i "$API_BASE/health"
curl -i "$API_BASE/state"
curl -i "$API_BASE/state" -H "Authorization: Bearer $FRAME_ID"
```

Se espera 200 con flags Firebase falsos, 401 si falta el identificador y 200 con `slots`/`jobs` vacíos para cualquier identificador válido. La primera consulta crea el registro SQLite; futuras consultas con el mismo identificador recuperan el mismo estado. Un identificador distinto queda aislado. Si ya había datos locales, no vaciarlos automáticamente: utilizar un `.env`/SQLite de desarrollo dedicado.

Abrir [Swagger](http://127.0.0.1:8000/docs) y comprobar que coincide con el catálogo [API.md](API.md). Guardar y borrar un registro local sintético, sin descargar audio:

```bash
curl -i "$API_BASE/stations" \
  -H "Authorization: Bearer $FRAME_ID" \
  -H 'Content-Type: application/json' \
  -d '{"slot":2,"title":"Radio de prueba local","url":"https://example.org/stream.mp3"}'
curl -i "$API_BASE/media/2" -H "Authorization: Bearer $FRAME_ID"
curl -i -X DELETE "$API_BASE/slots/2" -H "Authorization: Bearer $FRAME_ID"
curl -i "$API_BASE/media/2" -H "Authorization: Bearer $FRAME_ID"
```

Se espera 200, 200 con la URL sintética, 200 y 404. Esto verifica operaciones de metadatos, no una emisora funcional. Sin bucket configurado, un POST `/imports` válido debe devolver 503 sin crear una importación; no rellenar nombres ficticios para forzarlo.

Al acabar, `unset FRAME_ID` en la segunda terminal y `Ctrl+C` en la primera. El identificador no es un secreto ni se necesita configurarlo en Render. No imprimir `.env` para comprobar credenciales Firebase.

## B. Búsqueda de emisoras (Radio Browser)

Con la API local en marcha y sin Firebase, abre un enlace de cuadro de prueba y busca una emisora desde la pestaña «Emisora». La búsqueda real requiere conexión a Radio Browser; selecciona un resultado para guardarlo y usa «Escuchar aquí» para comprobar la escucha en ese navegador. La lista del directorio y el filtro de estaciones marcadas como caídas no garantizan que el stream siga disponible o sea compatible. La prueba del navegador tampoco acredita compatibilidad con ESP32.

También se puede comprobar el endpoint:

```bash
curl -i "$API_BASE/stations/search" \
  -H "Authorization: Bearer $FRAME_ID" \
  -H 'Content-Type: application/json' \
  -d '{"name":"Radio Nacional","country":"Spain"}'
```

Se espera 200 y una lista `results` (que puede estar vacía), o 502 si el servicio no responde. No guarda nada en el cuadro. La prueba automatizada simula la respuesta del proveedor y filtra URLs que no sean HTTPS; no sustituye una búsqueda ni una escucha reales.

## C. Recorrido real ya validado en Firebase

El 12 de noviembre de 2026 se completó una importación real desde Docker local, YouTube, la API y Firebase RTDB/Storage, seguida de reproducción en Chrome Headless. El detalle, versiones, comandos, resultados y límites está en [VALIDACION.md](VALIDACION.md). No repetir el POST de importación: el hueco 0 ya contiene «Carefree» de Kevin MacLeod y volver a importarlo crearía otra tarea y otros objetos.

Para abrir el cuadro de prueba en este Mac, desde la raíz del repositorio:

1. Desde la raíz, ejecuta `docker compose up -d` si API y web no están ya en marcha; sus URL locales son `http://127.0.0.1:8000` y `http://127.0.0.1:5173`.
2. Abre directamente [http://127.0.0.1:5173/#token=mi-cuadro-prueba](http://127.0.0.1:5173/#token=mi-cuadro-prueba). La web consume el fragmento y lo quita de la barra. El primer acceso crea el registro vacío en Firebase; los siguientes lo recuperan.
3. Para escuchar la importación existente del cuadro anterior, copia su enlace local al portapapeles sin imprimirlo:

   ```bash
   python3 - <<'PY' | pbcopy
   from pathlib import Path
   previous_id = Path('secrets/frame-test-token.txt').read_text(encoding='utf-8').strip()
   print('http://127.0.0.1:5173/#token=' + previous_id)
   PY
   ```

   Pégalo en el navegador del mismo Mac y pulsa el control de prueba del hueco 0.

El identificador de ejemplo es público y cualquiera puede modificar su ámbito. No uses datos privados ni compartas enlaces de Storage.

### Recorrido repetible en un cuadro vacío

Solo si se prepara otro cuadro/slot de prueba autorizado, seguir estos pasos. El hueco 0 ya está ocupado; no ejecutar sobre él ni borrar su selección como limpieza.

1. Configurar backend/Firebase y arrancar según sus guías. Usar el identificador Bearer del cuadro de prueba. El dispositivo puede leer slots/medios por URL sin sesión; las escrituras siguen en API.
2. Buscar con el ejemplo `/search` de [API.md](API.md). Elegir explícitamente uno de sus resultados y anotar `id`, título y artista; no importar automáticamente el primero.
3. Llamar a `/imports` con esos datos y un hueco de prueba. Comprobar 202 y conservar su `id` de tarea.
4. Consultar `/state` y localizar esa tarea en `jobs`. Repetir la consulta hasta `ready`, `error` o `cancelled`; no tratar `percent=100` de una etapa como éxito final.
5. Si está `ready`, comprobar el hueco y sus claves de audio/imagen, obtener `/media/{slot}` y usar la escucha local de la web. Confirmar que es el audio elegido y la imagen esperada.
6. Verificar en Firebase el registro y los objetos del entorno dedicado, sin copiar URLs públicas del cuadro ni credenciales al informe.
7. Comprobar un fallo de importación conservando una selección anterior. Comprobar cancelación y que no publica contenido cancelado.
8. Cerrar/reabrir la web y comprobar estado. Reiniciar el backend y registrar qué se recupera y qué requiere reintento. En Render validar desde su IP; lo probado en el Mac no acredita el alojamiento.
9. El DELETE de un hueco elimina los medios que ya no tengan referencias. En Firebase real, úsalo solo cuando quieras borrar definitivamente ese favorito. La limpieza también reintenta huérfanos cuando se vacía un hueco y al arrancar la API.

El reintento actual consiste en crear una tarea nueva con `/imports`; no existe `/retry`. La continuidad fiable al cerrar la web o reiniciar el servicio es un criterio de aceptación del producto, no una garantía ya demostrada.

Los resultados ejecutados, incluidos los límites que siguen pendientes, se registran en [VALIDACION.md](VALIDACION.md). Esta validación local no acredita Render, hardware ESP32 ni que una persona haya percibido el sonido.
