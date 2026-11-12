# Estado real de la base

Esta entrega conserva el código del prototipo como punto de partida, con documentación nueva basada en la definición. No es una implementación terminada de todo el producto. Fecha: 12 de noviembre de 2026.

| Área | Existe ahora | Pendiente para el producto |
|---|---|---|
| Interfaz | HTML/CSS/JS dinámico, tres huecos, búsqueda/progreso simulados, entrada manual de radio y conexión experimental al backend. | Modularizar JS, acceso mediante token de cuadro, Radio Browser, imagen decorativa y pulido móvil. |
| Demo | Datos en localStorage, resultados y progreso identificados como simulados. | Audio/recursos de ejemplo publicables y completar el flujo final; las tareas de demo no continúan al cerrar la página. |
| API | Ocho operaciones de prototipo y OpenAPI. | Contrato por cuadro, permisos limitados y resto de funciones acordadas. |
| Identidad | `IMPORT_API_TOKEN` global de desarrollo introducido manualmente. | Token fijo por cuadro y acceso por QR/NFC; no distribuir el token global. |
| Persistencia | Colección única `prototypes/sonoro` en RTDB, SQLite temporal en local. | Aislamiento por cuadro y referencias a recursos/reproducciones activas. |
| Tareas | Cola de registros y un worker dentro del proceso Uvicorn. | Una importación activa por cuadro y recuperación fiable. Hoy la exclusión es por hueco y el estado de cancelación está parcialmente en memoria. |
| Medios | MP3 a 128 kbps, carátula 320×320 y subida a Storage. | Límites definitivos, normalización configurable, imagen decorativa y eliminación de recursos que ya no se usan. |
| Limpieza | Temporales de importación y algunas subidas fallidas se limpian. | Medios sustituidos, cancelaciones tardías y recursos huérfanos; no hay limpieza remota completa. |
| Emisoras | Nombre y URL HTTPS introducidos a mano. | Búsqueda Radio Browser y validación real de formato, acceso y compatibilidad web/ESP32. |
| ESP32 | Sin código funcional ni hardware elegido. | Streaming, pantalla, controles, persistencia local y portal Wi-Fi. |

Los límites de 15 minutos, 40 MiB y la carátula 320×320 son valores del prototipo, no decisiones definitivas de producto. No confundir flags de configuración de `/health` con permisos verificados. Las URLs firmadas actuales caducan a los 30 minutos y no son una solución de autorización para firmware ya validada.

Consultar [validaciones](VALIDACION.md), [plan](PLAN.md) y [definición](DEFINICION.md). No desplegar el importador global como si ya ofreciera acceso aislado a invitados y múltiples cuadros.
