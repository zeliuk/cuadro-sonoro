# Arquitectura

La [definición](DEFINICION.md) fija el producto; [ESTADO.md](ESTADO.md) describe el código existente.

## Responsabilidades elegidas

| Componente | Responsabilidad |
|---|---|
| Web en servidor propio | Configuración dinámica, búsqueda/selección, progreso, imagen decorativa y escucha en navegador. |
| API/importador Render | Validar acceso por cuadro, buscar, crear/procesar tareas, preparar medios e imágenes y publicar configuraciones. |
| Realtime Database | Configuración por cuadro y estado durable de tareas. |
| Storage | Audio e imágenes preparados, con limpieza según referencias. |
| ESP32 | Leer su configuración autorizada, reproducir directamente y gestionar pantalla, botones, volumen y Wi-Fi. |

El audio no atraviesa Render al reproducirse. No se añaden órdenes web de reproducir/detener ni volumen remoto. El estado configurado y la reproducción activa deben modelarse por separado para preservar un audio en uso durante una sustitución.

## Flujo de incorporación

Búsqueda → selección explícita → tarea → descarga → preparación → subida → publicación del hueco. Solo se sustituye tras preparar todos los recursos. El error conserva el contenido anterior; la limpieza espera a que no existan referencias activas.

Una tarea aceptada debe poder sobrevivir a cerrar la web. Persistir su registro no garantiza que un worker vuelva a ejecutarla. Concretar antes del despliegue la ejecución, reclamación de tareas, recuperación, reintentos, idempotencia, cancelación y concurrencia por cuadro.

## Acceso

El token de un cuadro sirve como llave de su configuración. El familiar no configura una cuenta ni una segunda credencial técnica. El servicio debe validar ese acceso sin revelar IAM/Admin SDK. Definir un acceso seguro del ESP32 a configuración y medios que mantenga la reproducción independiente de un servicio Render dormido; no abrir reglas globales ni asumir que un ID secreto en una ruta basta para proteger todos los recursos.

El prototipo todavía no implementa esa solución: tiene un token global y colección única. Es el primer cambio del plan.

## Decisiones aplazadas

Contrato final de autorización y datos; mecanismo de lectura/sincronización del firmware; cola/worker definitivo; referencias para limpieza de reproducciones; límites y formatos finales; hardware. Resolver cada una antes de su fase sin alterar el comportamiento acordado.
