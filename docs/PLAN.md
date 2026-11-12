# Plan de trabajo

## Fase 0 — Revisar la base

Leer definición y estado; revisar Git; ejecutar demo, API local, tests, checks y comandos documentados; registrar límites reales del entorno. No requiere servicios de nube ni hardware.

## Fase 1 — Acceso y datos por cuadro (en curso)

Completado: la API valida el Bearer provisionado, deriva ámbitos aislados y permite una importación activa por cuadro. La web recibe el identificador desde `#token=...`, lo mantiene en `sessionStorage`, limpia la URL y cambia de cuadro cancelando solicitudes anteriores. Las reglas locales permiten GET público solo en rutas concretas conocidas; escrituras e importaciones siguen mediadas por la API. La conexión de Admin SDK a RTDB/Storage, la respuesta API por cuadro y la lectura pública directa real se verificaron; Carlos aplicó reglas desde Firebase Console después de que la CLI quedara bloqueada por permisos. Pendiente: importar audio real, escucharlo en web y trasladar el lector al firmware. Los datos de la antigua colección global no se migran automáticamente.

## Fase 2 — Importación real fiable

Una tarea activa por cuadro; ejecución recuperable; cancelación, reintentos, estados y publicación segura. Validar búsqueda y descarga desde Render, conversión, audio/imagen en Firebase y escucha en navegador. Cerrar la web debe permitir recuperar estado; reiniciar el worker debe tener comportamiento conocido. Elegir configuración real de Render, no asumir garantías de Free.

## Fase 3 — Completar la configuración web

Modularizar conservando diseño; acceso QR/NFC; Radio Browser; imagen decorativa con vista previa y procesamiento; limpieza de medios sin referencias incluyendo reproducciones activas. Separar demo/real y completar demo publicable. Probar móvil, teclado, errores, carga y audio local; no añadir control remoto del sonido.

## Fase 4 — Hardware y firmware

Elegir placa, pantalla, audio, alimentación y conexiones. Validar streaming sin SD, botones y luces, volumen, imagen en reposo y portal Wi-Fi. Comprobar cambios durante reproducción, pérdidas de red y arranque silencioso. Añadir comandos de compilación/carga y monitor serie.

## Fase 5 — Montaje y despliegue final

Resolver estructura física, montaje y pruebas de uso para un familiar. Documentar hosting propio, Render, Firebase, costes observados y diagnóstico. Revisar recursos de demo y licencia antes de anunciar reutilización del código.

Cada fase acaba con documentación operativa, verificaciones relevantes y `ESTADO.md`/`VALIDACION.md` actualizados. La definición es destino del producto, no checklist ya completado.
