# Probar la API paso a paso

## A. Comprobación local sin Firebase ni descargas

Esta prueba usa exclusivamente un entorno local dedicado. No arrancar con variables de nube de producción. Desde la raíz y con las dependencias instaladas, preparar y arrancar en una terminal:

```bash
python scripts/setup_local.py
python -m uvicorn backend.main:app --env-file backend/.env --host 127.0.0.1 --port 8000 --workers 1
```

En una segunda terminal, desde la misma raíz:

```bash
source .venv/bin/activate
export API_BASE='http://127.0.0.1:8000'
export API_TOKEN="$(python -c 'from dotenv import dotenv_values; print(dotenv_values("backend/.env").get("LOCAL_FRAME_TOKEN", ""))')"
curl -i "$API_BASE/health"
curl -i "$API_BASE/state"
curl -i "$API_BASE/state" -H "Authorization: Bearer $API_TOKEN"
```

Se espera 200 con flags Firebase falsos, 401 sin token y 200 con `slots`/`jobs` inicialmente vacíos al usar el token local. Esa primera consulta autorizada crea el registro SQLite; futuras consultas reutilizan el mismo registro. En modo local la API admite solo `LOCAL_FRAME_TOKEN`; otro token largo no provisionado devuelve 401. Si ya había datos locales, no vaciarlos automáticamente: utilizar un `.env`/SQLite de desarrollo dedicado. No continuar una prueba de modificación contra datos reales. El estado se guarda bajo el hash del identificador en `frame_states`.

Abrir [Swagger](http://127.0.0.1:8000/docs) y comprobar que coincide con el catálogo [API.md](API.md). Guardar y borrar un registro local sintético, sin descargar audio:

```bash
curl -i "$API_BASE/stations" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"slot":2,"title":"Radio de prueba local","url":"https://example.org/stream.mp3"}'
curl -i "$API_BASE/media/2" -H "Authorization: Bearer $API_TOKEN"
curl -i -X DELETE "$API_BASE/slots/2" -H "Authorization: Bearer $API_TOKEN"
curl -i "$API_BASE/media/2" -H "Authorization: Bearer $API_TOKEN"
```

Se espera 200, 200 con la URL sintética, 200 y 404. Esto verifica operaciones de metadatos, no una emisora funcional. Sin bucket configurado, un POST `/imports` válido debe devolver 503 sin crear una importación; no rellenar nombres ficticios para forzarlo.

Al acabar, `unset API_TOKEN` en la segunda terminal y `Ctrl+C` en la primera. No imprimir `.env` para comprobar valores. En producción el desarrollador prepara un token aleatorio diferente por cuadro y configura su hash en `FRAME_TOKEN_HASHES`; no configura una credencial global en Render. Los tokens anteriores de `IMPORT_API_TOKEN` ya no sirven.

## B. Recorrido real cuando esté preparada la fase de integración

Esta parte todavía requiere configurar recursos dedicados, autorizar su uso y resolver los límites del prototipo. Puede generar consumo y modificar Firebase. No ejecutarla como parte de los tests automáticos de un fork.

1. Configurar backend/Firebase y arrancar según sus guías. Usar el identificador Bearer del cuadro de prueba. El dispositivo puede leer slots/medios por URL sin sesión; las escrituras siguen en API.
2. Buscar con el ejemplo `/search` de [API.md](API.md). Elegir explícitamente uno de sus resultados y anotar `id`, título y artista; no importar automáticamente el primero.
3. Llamar a `/imports` con esos datos y un hueco de prueba. Comprobar 202 y conservar su `id` de tarea.
4. Consultar `/state` y localizar esa tarea en `jobs`. Repetir la consulta hasta `ready`, `error` o `cancelled`; no tratar `percent=100` de una etapa como éxito final.
5. Si está `ready`, comprobar el hueco y sus claves de audio/imagen, obtener `/media/{slot}` y usar la escucha local de la web. Confirmar que es el audio elegido y la imagen esperada.
6. Verificar en Firebase el registro y los objetos del entorno dedicado, sin copiar URLs públicas del cuadro ni credenciales al informe.
7. Comprobar un fallo de importación conservando una selección anterior. Comprobar cancelación y que no publica contenido cancelado.
8. Cerrar/reabrir la web y comprobar estado. Reiniciar el backend y registrar qué se recupera y qué requiere reintento. En Render validar desde su IP; lo probado en el Mac no acredita el alojamiento.
9. Comprobar la limpieza cuando esté implementada. El DELETE actual no borra archivos remotos: no reportarlo como limpieza completa ni usarlo para borrar producción.

El reintento actual consiste en crear una tarea nueva con `/imports`; no existe `/retry`. La continuidad fiable al cerrar la web o reiniciar el servicio es un criterio de aceptación del producto, no una garantía ya demostrada.

Registrar el resultado redactado en [VALIDACION.md](VALIDACION.md): entorno, comandos, resultado por etapa y pendientes. No implementar el firmware antes de validar búsqueda, descarga, conversión, subida y escucha real.
