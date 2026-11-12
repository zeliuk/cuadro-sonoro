# Estado real de la base

Esta entrega conserva el código del prototipo como punto de partida, con documentación nueva basada en la definición. No es una implementación terminada de todo el producto. Fecha: 12 de noviembre de 2026.

| Área | Existe ahora | Pendiente para el producto |
|---|---|---|
| Interfaz | HTML/CSS/JS dinámico; acepta `#token=...`, usa Bearer y conserva el token en `sessionStorage` de la pestaña. Sin token muestra acceso bloqueado; demo es explícita. Se conserva el acceso manual de desarrollo. | Preparar/imprimir QR y programar NFC, modularizar JS, Radio Browser, imagen decorativa y pulido móvil. |
| Demo | Datos en localStorage, resultados y progreso identificados como simulados. | Audio/recursos de ejemplo publicables y completar el flujo final; las tareas de demo no continúan al cerrar la página. |
| API | Ocho operaciones; operaciones del cuadro protegidas con Bearer de al menos 32 caracteres. OpenAPI actualizado. | Autorización y lectura directa de medios para ESP32; Radio Browser, imagen decorativa y otras funciones. |
| Identidad | Token aleatorio provisionado por cuadro; la API valida su SHA-256 en `FRAME_TOKEN_HASHES` y usa el hash como ámbito. No hay token global ni emisión de credenciales en el servicio. | Integración del token en QR/NFC y mecanismo seguro de acceso autónomo del ESP32. |
| Persistencia | RTDB bajo `frames/{sha256}` y SQLite local en filas separadas `frame_states`. El estado antiguo `prototypes/sonoro`/`state` no se migra. | Referencias a reproducciones activas, migración manual de datos antiguos destinados a un cuadro. |
| Tareas | Un worker dentro del proceso Uvicorn recorre los ámbitos; una importación activa por cuadro. | Recuperación fiable y exclusión/concurrencia entre procesos o réplicas; cancelación sigue parcialmente en memoria. |
| Medios | MP3 a 128 kbps, carátula 320×320 y nuevos objetos bajo `private/frames/{sha256}/{job_id}`. | Límites definitivos, normalización configurable, imagen decorativa y eliminación de recursos que ya no se usan. |
| Limpieza | Temporales de importación y algunas subidas fallidas se limpian. | Medios sustituidos, cancelaciones tardías y recursos huérfanos; no hay limpieza remota completa. |
| Emisoras | Nombre y URL HTTPS introducidos a mano. | Búsqueda Radio Browser y validación real de formato, acceso y compatibilidad web/ESP32. |
| ESP32 | Sin código funcional ni hardware elegido. | Streaming, pantalla, controles, persistencia local y portal Wi-Fi. |

Los límites de 15 minutos, 40 MiB y la carátula 320×320 son valores del prototipo, no decisiones definitivas de producto. No confundir flags de configuración de `/health` con permisos verificados. Las URLs firmadas actuales caducan a los 30 minutos; no están validadas como mecanismo de acceso autónomo para el firmware.

La revisión local del 12 de noviembre de 2026 preparó `.venv` con Python 3.12.15 y ejecutó la demo y la API sin Firebase. Las comprobaciones y sus límites están en [VALIDACION.md](VALIDACION.md). El backend aísla cuadros y la web consume el enlace con token; generar QR, programar NFC y dar acceso autónomo al ESP32 siguen pendientes.

Consultar [validaciones](VALIDACION.md), [plan](PLAN.md) y [definición](DEFINICION.md). No desplegar el prototipo actual como producto listo: faltan el acceso del dispositivo, la integración QR/NFC, la recuperación fiable de tareas y la validación real del flujo de medios.
