# Cuadro sonoro

Un cuadro decorativo que permite elegir tres canciones o emisoras desde una web y escucharlas mediante botones físicos. Una pequeña pantalla muestra carátulas o una imagen decorativa. **Sonoro** es el nombre provisional de la interfaz.

**Estado: prototipo ejecutable con una primera importación real validada.** La importación y el avance del reproductor web se comprobaron con Firebase real y Chrome Headless; posteriormente se eliminó esa canción y sus medios para validar la limpieza. La lectura pública por URL conocida está aplicada manualmente. Falta validar Render, escucha humana, firmware y QR/NFC físicos. Ver [estado real](docs/ESTADO.md).

## Prueba la interfaz sin credenciales

Desde la raíz del repositorio, con Python 3 disponible:

```bash
python3 -m http.server 5173 --bind 127.0.0.1 --directory web
```

Abre [la interfaz local](http://127.0.0.1:5173) y pulsa «Probar demostración» para recorrerla sin backend. Para un cuadro real usa su enlace, que ya contiene el identificador; no hay que configurar una conexión desde la web. Se detiene con `Ctrl+C`. Los resultados y las barras son simulados y están identificados como demo; la demo actual todavía no reproduce audio de ejemplo.

## Producto definido

- Un identificador por cuadro relaciona su enlace QR/NFC, sus selecciones y el ESP32; no es una credencial.
- Tres huecos, cada uno con una canción o emisora; una importación por cuadro a la vez.
- Búsqueda de canciones con elección de versión y progreso de importación.
- Radio Browser como directorio de emisoras.
- Web dinámica, sin recargas completas y diseñada primero para móvil.
- Escucha de prueba en el navegador. El cuadro se controla con tres pulsadores iluminados y una rueda de volumen.
- Streaming Wi-Fi con búfer, sin microSD; arranque en silencio y parada al terminar una canción.
- Imagen decorativa elegida en la web y optimizada por el servidor.
- Configuración Wi-Fi local mediante QR y asistente, sin instalar una app.

La [definición completa](docs/DEFINICION.md) es la referencia para implementar estos comportamientos.

## Arquitectura elegida

| Parte | Tecnología y ubicación |
|---|---|
| Web | HTML, CSS y JavaScript modular servidos por el ESP32 en la red doméstica; el móvil ejecuta la interfaz. |
| API e importador | Python/FastAPI, yt-dlp y FFmpeg, en Render con Docker. |
| Datos | Firebase Realtime Database. |
| Archivos preparados | Firebase Storage. |
| Dispositivo | ESP32 con pantalla, audio y controles; hardware pendiente. |

La web se aloja fuera de Firebase Hosting. El ESP32 recibirá el audio directamente de Storage o de la emisora; Render no debe intervenir en cada reproducción de una canción ya preparada.

## Empezar a desarrollar

1. Lee [AGENTS.md](AGENTS.md) y [el primer encargo para Codex](docs/PRIMER_PASO_CODEX.md).
2. Sigue [la puesta en marcha](docs/PUESTA_EN_MARCHA.md).
3. Consulta [backend/README.md](backend/README.md) para instalar, arrancar, probar y detener la API.
4. Prueba los endpoints con [los ejemplos de API](docs/API.md) y su [prueba guiada](docs/PRUEBA_API.md).
5. Avanza siguiendo [el plan](docs/PLAN.md), manteniendo actualizadas las instrucciones.

Las instrucciones compartidas de ChatGPT se mantienen en [docs/INSTRUCCIONES_CHATGPT.md](docs/INSTRUCCIONES_CHATGPT.md). Si Codex las cambia, copiar de nuevo su contenido al proyecto ChatGPT y renovar los adjuntos de definición/estado que hayan cambiado.

## Mapa del repositorio

| Ruta | Contenido |
|---|---|
| `web/` | Diseño aprobado y prototipo dinámico. |
| `backend/` | API e importador iniciales; cada identificador válido deriva un ámbito aislado sin alta previa. |
| `firebase/` | Reglas de lectura por URL conocida, sin escrituras/listados, y guía del cliente directo. |
| `firmware/` | Alcance documentado; todavía sin firmware. |
| `docs/` | Definición, arquitectura, comandos, endpoints, fases y decisiones. |
| `scripts/` | Preparación local y verificaciones. |

Documentación adicional: [stack](docs/STACK.md), [configuración](docs/CONFIGURACION.md), [despliegue](docs/DESPLIEGUE.md), [publicación en GitHub](docs/PUBLICAR_GITHUB.md), [contribución](CONTRIBUTING.md) y [seguridad](SECURITY.md).

El primer hito real —buscar, importar, guardar audio e imagen en Firebase y probar el MP3 en navegador— está validado en [VALIDACION.md](docs/VALIDACION.md). Esto no acredita Render ni la compatibilidad con un ESP32. La licencia del código y los recursos de demo está pendiente de elegir; no se atribuye una licencia abierta por defecto.
