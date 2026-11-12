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

El token aleatorio provisionado de cada cuadro se envía en `Authorization: Bearer`. La API exige que su SHA-256 esté en `FRAME_TOKEN_HASHES` y usa ese hash como ámbito en RTDB (`frames/{sha256}`), SQLite local (`frame_states`) y rutas de objetos nuevos en Storage. El token original no se guarda. El familiar no configura una cuenta ni una segunda credencial técnica. Los datos de la antigua colección común no se migran porque no tienen identidad de cuadro.

La web todavía no incorpora automáticamente el token al QR/enlace y el firmware no existe. La API de importación sigue necesitando Render; los enlaces de Storage firmados 30 minutos no permiten afirmar que el ESP32 pueda reproducir con Render dormido. Resolver ese acceso antes de integrar el firmware; no abrir reglas globales ni dar por cumplida esa parte.

## Decisiones aplazadas

Contrato final de autorización y datos; mecanismo de lectura/sincronización del firmware; cola/worker definitivo; referencias para limpieza de reproducciones; límites y formatos finales; hardware. Resolver cada una antes de su fase sin alterar el comportamiento acordado.
