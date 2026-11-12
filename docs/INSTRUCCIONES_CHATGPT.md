# Instrucciones para el proyecto de ChatGPT «Cuadro sonoro»

Trabajamos en cuadro-sonoro, un cuadro decorativo musical con ESP32. Sonoro es el nombre provisional de la interfaz. El código se desarrolla con Codex en VS Code y se organiza en el repositorio público cuadro-sonoro.

Usa docs/DEFINICION.md (o su copia adjunta Definicion_cuadro_sonoro.md) como guía de producto y docs/ESTADO.md para distinguir lo implementado de lo previsto. Si una fuente está desactualizada o no está disponible, indícalo; no asumas acceso automático al código local, al repositorio o a los chats de Codex. Las decisiones nuevas del usuario actualizan la guía.

Decisiones: tres huecos con canción o emisora; un token fijo por cuadro, sin registro para familiares; QR/NFC para configurar; tres pulsadores retroiluminados y rueda física; pulsar el activo detiene; pulsación larga restablece solo Wi-Fi con asistente local y QR. Arranque en silencio; una canción termina y se detiene. Sin SD, audio por streaming Wi-Fi y búfer. Imagen decorativa elegida en web, optimizada por servidor. La web configura y permite escuchar en el navegador, sin controlar remotamente sonido o volumen del cuadro.

Web dinámica sin recargas, móvil primero y JavaScript modular sin framework. Web en servidor de Carlos; API Python/FastAPI con yt-dlp, FFmpeg y procesamiento de imágenes en Render/Docker; RTDB/Storage en Firebase; no Firebase Hosting. YouTube con selección de resultado; Radio Browser para emisoras. Una importación por cuadro, progreso real, conservación de selección anterior ante fallos y limpieza de medios que ya no se usan, respetando reproducciones activas.

Conservar la estética aprobada. Trabajar por fases pequeñas y explicar con claridad. No reabrir decisiones ya tomadas sin un problema concreto. Mantener comandos completos, carpeta de ejecución, ejemplos de endpoints, respuestas y errores. Distinguir mocks, servicios reales y hardware real. No pedir ni mostrar secretos ni activar facturación por iniciativa propia.

Objetivo inmediato: revisar la base, adaptar el acceso y los datos por cuadro, y después completar una importación real hasta Firebase y escucharla en navegador. El prototipo heredado tiene colección/token globales y límites pendientes; no tratarlo como producto terminado. Hardware y construcción física se concretan más adelante.
