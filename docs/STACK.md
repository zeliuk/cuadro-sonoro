# Stack y herramientas

| Parte | Elección |
|---|---|
| Frontend | HTML, CSS y JavaScript ES Modules, sin React ni bundler obligatorio. |
| API | Python 3.12, FastAPI y Uvicorn. |
| Importación | yt-dlp con extras `default`, FFmpeg/ffprobe y Deno como runtime JS. |
| Imágenes | Pillow en el servidor. |
| Nube | Firebase Admin SDK, Realtime Database y Storage. |
| Entorno backend | Docker, desplegable en Render. |
| Pruebas | pytest, HTTPX/TestClient y mocks de proveedores. |
| Firmware | C++; entorno y librerías pendientes del hardware. |

Node se usa para la comprobación de sintaxis JS, no como servidor de producción ni framework. La web puede alojarse sirviendo archivos estáticos y seguir siendo dinámica en el navegador.

El backend inicial usa SQLite solo como alternativa local sin Firebase; no es una nueva base de datos de producción. Sus rangos de dependencias vienen del prototipo y aún no tienen un lockfile reproducible por plataforma: Codex deberá fijar una estrategia de versiones al preparar el despliegue, evitando congelar rutas locales o artefactos específicos de esta máquina.

Referencias: [FastAPI](https://fastapi.tiangolo.com/tutorial/first-steps/), [yt-dlp y EJS](https://github.com/yt-dlp/yt-dlp/wiki/EJS), [Radio Browser](https://docs.radio-browser.info/), [Docker en Render](https://render.com/docs/docker).
