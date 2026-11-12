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

El identificador aleatorio fijo se envía a la API en `Authorization: Bearer`. La API exige que su SHA-256 esté en `FRAME_TOKEN_HASHES` y usa ese hash como ámbito en RTDB (`frames/{sha256}`), SQLite local (`frame_states`) y rutas de Storage. Por decisión expresa de Carlos, RTDB y Storage sirven lectura pública por URL conocida: solo el nodo `slots` del cuadro se puede leer, las tareas y el listado raíz quedan cerrados, y Storage permite obtener objetos individuales sin permitir listarlos. El hash separa datos, pero no autentica a quien conoce el enlace. Las reglas no autorizan escrituras; cambios e importaciones siguen pasando por la API con Bearer. Credenciales Admin solo en backend y herramientas privadas.

La web acepta el identificador en el fragmento del enlace. El cliente de prueba de ordenador obtiene los slots y medios directamente sin llamar a la API; el firmware no existe. La API de importación sigue necesitando Render. Los objetos publicados tienen URLs directas estables sujetas a las reglas de lectura pública por URL conocida.

## Decisiones aplazadas

Contrato final de autorización y datos; mecanismo de lectura/sincronización del firmware; cola/worker definitivo; referencias para limpieza de reproducciones; límites y formatos finales; hardware. Resolver cada una antes de su fase sin alterar el comportamiento acordado.
