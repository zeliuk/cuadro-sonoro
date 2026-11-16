# Stack y herramientas

| Parte | Elección |
|---|---|
| Frontend | HTML, CSS y JavaScript ES Modules, sin React ni bundler obligatorio. |
| API | Python 3.12, FastAPI y Uvicorn. |
| Importación | yt-dlp para búsqueda de YouTube; RapidAPI para descargar audio tras seleccionar resultado; FFmpeg/ffprobe, Deno y Pillow en backend. |
| Imágenes | Pillow en el servidor. |
| Nube | Firebase Admin SDK, Realtime Database y Storage. |
| Entorno backend | API alojada en Render según Carlos, que comunica funcionamiento con RapidAPI. No es una comprobación realizada por Codex en esta fase; verificar el flujo web público, métricas y recuperación. |
| Pruebas | pytest, HTTPX/TestClient y mocks de proveedores. |
| Firmware | C++; entorno y librerías pendientes del hardware. |

Node se usa para la comprobación de sintaxis JS, no como servidor de producción ni framework. La web estática se alojará en `https://sonoro.zeliuk.xyz`; sigue siendo dinámica en el navegador. El ESP32 no la aloja.

El backend inicial usa SQLite solo como alternativa local sin Firebase; no es una nueva base de datos de producción. Sus rangos de dependencias vienen del prototipo y aún no tienen un lockfile reproducible por plataforma: Codex deberá fijar una estrategia de versiones al preparar el despliegue, evitando congelar rutas locales o artefactos específicos de esta máquina.

Referencias: [FastAPI](https://fastapi.tiangolo.com/tutorial/first-steps/), [RapidAPI Hub](https://rapidapi.com/ytjar/api/youtube-mp36), [Radio Browser](https://docs.radio-browser.info/).
