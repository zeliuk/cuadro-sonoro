# Validación de esta entrega

Fecha: 12 de noviembre de 2026. Entorno de comprobación: Linux, Python 3.12.14 y un entorno virtual limpio. El usuario continuará en macOS; no se ha ejecutado la instalación en su Mac.

| Comprobación | Resultado |
|---|---|
| Instalar `backend/requirements-dev.txt` | Correcto en entorno virtual limpio; incluye dependencias de ejecución. |
| Tests de backend y control de repositorio | 10 superados, con proveedores simulados y datos temporales. |
| Arranque y parada Uvicorn con `.env` local | Correctos, sin configurar Firebase. |
| HTTP local | 17 comprobaciones: health, autorización, estado, documentación, metadatos de radio sintética, vaciado y errores esperados. |
| Catálogo API frente a OpenAPI real | Coinciden las ocho operaciones; exportación en `openapi.prototype.json`. |
| `node --check web/app.js` | Correcto. |
| Diseño conservado | HTML, CSS y JS idénticos al ZIP original recuperado. |
| Firebase Hosting | Retirado de `firebase.json`; web prevista en servidor propio. |
| Enlaces internos de documentación | Comprobados. |
| Control básico de publicación | 56 archivos preparados sin hallazgos de sus patrones; no es una auditoría del historial. |

La radio sintética utiliza `example.org` y solo verifica el contrato y los registros, no reproduce una emisora real. La búsqueda se probó únicamente con entrada inválida para verificar 422. La importación se probó sin Storage para verificar 503; la ejecución completa se cubre solo con mocks existentes.

El conjunto de dependencias resuelto produce un aviso de deprecación de Starlette/TestClient sobre HTTPX. Las pruebas pasan; fijar y revisar compatibilidad de dependencias al preparar la base reproducible de despliegue.

## Límites de la evidencia

- Docker y Deno no estaban disponibles en este entorno: no se ha construido la imagen ni ejecutado Compose.
- No se ha accedido a servicios Firebase reales ni descargado contenido de YouTube en esta comprobación.
- No se ha desplegado en Render, Firebase ni el servidor de Carlos.
- No se ha implementado aislamiento por cuadro, Radio Browser, imagen decorativa ni firmware.
- No se ha hecho una nueva revisión visual en navegador; se conservan los archivos visuales originales sin cambios. La validación móvil del producto final corresponde a su fase.

Las guías de Docker, Firebase CLI y despliegue son recetas para ejecutar/validar en el entorno correspondiente, no pruebas de despliegue realizadas. Actualizar este documento con cada hito real y registrar errores de forma redactada.

## Reproducir los checks

Desde la raíz, con `.venv` activado:

```bash
env -u FIREBASE_DATABASE_URL -u FIREBASE_STORAGE_BUCKET -u FIREBASE_SERVICE_ACCOUNT_JSON -u GOOGLE_APPLICATION_CREDENTIALS python -m pytest backend/tests scripts/tests -q
python -m compileall -q backend scripts
node --check web/app.js
```

El recorrido HTTP manual está en [PRUEBA_API.md](PRUEBA_API.md). El esquema se puede actualizar desde una API local arrancada con `curl -sS http://127.0.0.1:8000/openapi.json -o docs/openapi.prototype.json`, revisando el diff junto a `API.md` antes de commit.

## Ajuste de contexto compartido

Las instrucciones de ChatGPT se trasladaron al archivo versionado `docs/INSTRUCCIONES_CHATGPT.md`. Se actualizaron las referencias, la definición y la regla de mantenimiento en AGENTS.md. Cambio documental; comprobados enlaces y contenido del ZIP, sin modificar lógica ni repetir pruebas de ejecución.
