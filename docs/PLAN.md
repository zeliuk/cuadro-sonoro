# Plan de trabajo

## Fase 0 — Revisar la base

Leer definición y estado; revisar Git; ejecutar demo, API local, tests, checks y comandos documentados; registrar límites reales del entorno. No requiere servicios de nube ni hardware.

## Fase 1 — Acceso y datos por cuadro (en curso)

Completado: la API deriva ámbitos del identificador sin alta previa; IDs válidos crean o recuperan estado y se aíslan mediante SHA-256. La web recibe el valor desde `#token=...`, lo mantiene en `sessionStorage`, limpia la URL y cambia de cuadro cancelando solicitudes anteriores. Las reglas locales permiten GET público solo en rutas concretas conocidas; las escrituras públicas siguen cerradas en Firebase y las mutaciones API quedan agrupadas por ID sin autenticación de usuario. La conexión Admin, la importación real y la reproducción web se validaron en Firebase real y Docker local. Pendientes: Render, recuperación de tareas, firmware y QR/NFC físicos. Los datos de la antigua colección global no se migran automáticamente.

## Fase 2 — Importación real fiable

Comprobación inicial completada en Docker local: búsqueda de YouTube, selección explícita, descarga y conversión, subida de MP3/portada a Firebase real, publicación RTDB y reproducción en Chrome Headless. Implementado y probado localmente: recuperación acotada tras reinicio, cancelación durable, publicación atómica e idempotencia por ejecución, conservación de selección previa y volumen SQLite Docker. Pendiente: validar durabilidad y ciclo de ejecución en Render, escucha humana y elegir su configuración sin asumir garantías de Free.

## Fase 3 — Completar la configuración web

Modularizar conservando diseño; alojar los archivos estáticos en el servidor HTTP del ESP32; acceso QR/NFC mediante hostname local único (mDNS preferido), validando resolución y CORS; Radio Browser (búsqueda y selección ya integradas); validar streams en navegador/ESP32 y preparar sugerencias revisadas; imagen decorativa con vista previa y procesamiento; limpieza de medios sin referencias incluyendo reproducciones activas. Separar demo/real y completar demo publicable. Probar móvil, teclado, errores, carga y audio local; no añadir control remoto del sonido.

## Fase 4 — Hardware y firmware

Elegir placa, memoria flash/RAM suficientes para firmware y recursos web, pantalla, audio, alimentación y conexiones. Validar servidor web estático, hostname mDNS en móviles y routers objetivo, streaming sin SD, botones y luces, volumen, imagen en reposo y portal Wi-Fi. Comprobar cambios durante reproducción, pérdidas de red y arranque silencioso. Añadir comandos de compilación/carga y monitor serie.

## Fase 5 — Montaje y despliegue final

Resolver estructura física, montaje y pruebas de uso para un familiar. Documentar firmware/servidor web del ESP32, Render, Firebase, hostname local, CORS, costes observados y diagnóstico. Revisar recursos de demo y licencia antes de anunciar reutilización del código.

Cada fase acaba con documentación operativa, verificaciones relevantes y `ESTADO.md`/`VALIDACION.md` actualizados. La definición es destino del producto, no checklist ya completado.
