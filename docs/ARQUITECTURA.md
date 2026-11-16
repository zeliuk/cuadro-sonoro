# Arquitectura

La [definición](DEFINICION.md) fija el producto; [ESTADO.md](ESTADO.md) describe el código existente.

## Responsabilidades elegidas

| Componente | Responsabilidad |
|---|---|
| Web estática en ESP32 | Sirve HTML/CSS/JS en la red doméstica. El navegador del móvil ejecuta la interfaz de configuración, búsqueda/selección, progreso, imagen decorativa y escucha local. Se accede con QR/NFC mediante hostname local único, preferentemente mDNS; el firmware sirve los archivos, no ejecuta la aplicación web. |
| API/importador Docker | Derivar el ámbito desde cualquier identificador válido, buscar, crear/procesar tareas, preparar medios y publicar configuraciones. No autentica usuarios ni consulta una lista de acceso. La integración de prueba ejecuta Actors Apify desde backend Render; despliegue y compatibilidad real siguen sin validar. |
| Realtime Database | Configuración por cuadro y estado durable de tareas. |
| Storage | Audio e imágenes preparados, con limpieza según referencias. |
| ESP32 | Servir los archivos estáticos de la web; leer su configuración por el identificador fijado en el enlace; reproducir directamente y gestionar pantalla, botones, volumen, hostname local y Wi-Fi. |

El audio no atraviesa la API al reproducirse. No se añaden órdenes web de reproducir/detener ni volumen remoto. El estado configurado y la reproducción activa deben modelarse por separado para preservar un audio en uso durante una sustitución.

## Flujo de incorporación

Búsqueda → selección explícita → tarea → descarga → preparación → subida → publicación del hueco. Solo se sustituye tras preparar todos los recursos. El error conserva el contenido anterior. Tras retirar una selección, la API borra los objetos del cuadro sin referencias publicadas ni subidas activas; el reproductor local se detiene antes. El firmware todavía no tiene leases de reproducción.

Una tarea aceptada se guarda en RTDB o SQLite local durable. Con una instancia y un worker, el inicio reencola ejecuciones interrumpidas hasta dos veces para repetir descarga y conversión desde cero; después indica que hay que cancelar y volver a elegir. Cancelar y vaciar hueco actualiza el registro durable, y la publicación comprueba la ejecución vigente en la misma transacción que marca `ready`. SQLite local serializa cambios y Compose mantiene el archivo en un volumen nombrado. Si Compose usa la misma RTDB que Render, su worker puede consumir tareas creadas por Render; no se deben ejecutar ambos contra una cola compartida hasta resolver coordinación/exclusión.

## Acceso

El identificador se envía a la API en `Authorization: Bearer` como selector de ámbito, no como autenticación. Cualquier valor de 1–128 caracteres ASCII que cumpla el formato documentado crea o recupera su cuadro; API y cliente de dispositivo derivan el mismo SHA-256 para RTDB (`frames/{sha256}`), SQLite (`frame_states`) y Storage. No hay lista de acceso ni cuentas. Quien conoce o elige un identificador puede cambiar ese ámbito por API. Por decisión expresa de Carlos, RTDB y Storage sirven además lecturas públicas por URL conocida: solo el nodo `slots` del cuadro se puede leer, las tareas y el listado raíz quedan cerrados, y Storage permite obtener objetos individuales sin permitir listarlos. El hash separa datos, no autoriza. Credenciales Admin solo en backend y herramientas privadas.

La web acepta el identificador en el fragmento del enlace. El cliente de prueba de ordenador obtiene los slots y medios directamente sin llamar a la API; el firmware no existe. La prueba actual sirve el frontend desde el ordenador y usa la URL Render del meta. Apify solo se comunica desde el backend. Los objetos publicados tienen URLs directas estables sujetas a las reglas de lectura pública por URL conocida.

El enlace aprobado es `http://cuadro-sonoro-<id-dispositivo>.local/#token=<id-cuadro>`. En la prueba previa al hardware, un proceso Python del Mac sirve solo `web/` y Bonjour publica el hostname/IP LAN. El `meta` apunta a `https://cuadro-sonoro.onrender.com`. El navegador nunca conoce la credencial Apify. El diagnóstico histórico de yt-dlp en Render devolvió HTTP 429/403; la ruta nueva Apify aún debe verificarse. En hardware, el ESP32 ocupará el lugar del servidor web; su servidor aún no existe.

## Decisiones aplazadas

Contrato final de autorización y datos; mecanismo de lectura/sincronización del firmware; cola/worker definitivo; referencias para limpieza de reproducciones; límites y formatos finales; hardware. Resolver cada una antes de su fase sin alterar el comportamiento acordado.
