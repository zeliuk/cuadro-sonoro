# Arquitectura

La [definición](DEFINICION.md) fija el producto; [ESTADO.md](ESTADO.md) describe el código existente.

## Responsabilidades elegidas

| Componente | Responsabilidad |
|---|---|
| Web en servidor propio | Configuración dinámica, búsqueda/selección, progreso, imagen decorativa y escucha en navegador. |
| API/importador Render | Derivar el ámbito desde cualquier identificador válido, buscar, crear/procesar tareas, preparar medios y publicar configuraciones. No autentica usuarios ni consulta una lista de acceso. |
| Realtime Database | Configuración por cuadro y estado durable de tareas. |
| Storage | Audio e imágenes preparados, con limpieza según referencias. |
| ESP32 | Leer su configuración por el identificador fijado en el enlace, reproducir directamente y gestionar pantalla, botones, volumen y Wi-Fi. |

El audio no atraviesa Render al reproducirse. No se añaden órdenes web de reproducir/detener ni volumen remoto. El estado configurado y la reproducción activa deben modelarse por separado para preservar un audio en uso durante una sustitución.

## Flujo de incorporación

Búsqueda → selección explícita → tarea → descarga → preparación → subida → publicación del hueco. Solo se sustituye tras preparar todos los recursos. El error conserva el contenido anterior. Tras retirar una selección, la API borra los objetos del cuadro sin referencias publicadas ni subidas activas; el reproductor local se detiene antes. El firmware todavía no tiene leases de reproducción.

Una tarea aceptada se guarda en RTDB o SQLite local durable. Con una instancia y un worker, el inicio reencola ejecuciones interrumpidas hasta dos veces para repetir descarga y conversión desde cero; después indica que hay que cancelar y volver a elegir. Cancelar y vaciar hueco actualiza el registro durable, y la publicación comprueba la ejecución vigente en la misma transacción que marca `ready`. SQLite local serializa cambios y Compose mantiene el archivo en un volumen nombrado. No usar varios workers o réplicas: la exclusión distribuida, leases y ejecución administrada para Render siguen pendientes.

## Acceso

El identificador se envía a la API en `Authorization: Bearer` como selector de ámbito, no como autenticación. Cualquier valor de 1–128 caracteres ASCII que cumpla el formato documentado crea o recupera su cuadro; API y cliente de dispositivo derivan el mismo SHA-256 para RTDB (`frames/{sha256}`), SQLite (`frame_states`) y Storage. No hay lista de acceso ni cuentas. Quien conoce o elige un identificador puede cambiar ese ámbito por API. Por decisión expresa de Carlos, RTDB y Storage sirven además lecturas públicas por URL conocida: solo el nodo `slots` del cuadro se puede leer, las tareas y el listado raíz quedan cerrados, y Storage permite obtener objetos individuales sin permitir listarlos. El hash separa datos, no autoriza. Credenciales Admin solo en backend y herramientas privadas.

La web acepta el identificador en el fragmento del enlace. El cliente de prueba de ordenador obtiene los slots y medios directamente sin llamar a la API; el firmware no existe. La API de importación sigue necesitando Render. Los objetos publicados tienen URLs directas estables sujetas a las reglas de lectura pública por URL conocida.

## Decisiones aplazadas

Contrato final de autorización y datos; mecanismo de lectura/sincronización del firmware; cola/worker definitivo; referencias para limpieza de reproducciones; límites y formatos finales; hardware. Resolver cada una antes de su fase sin alterar el comportamiento acordado.
