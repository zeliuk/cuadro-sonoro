# Arquitectura

La [definición](DEFINICION.md) fija el producto; [ESTADO.md](ESTADO.md) describe el código existente.

## Responsabilidades elegidas

| Componente | Responsabilidad |
|---|---|
| Hosting web de Carlos | Sirve los archivos estáticos de `web/` por HTTPS en `https://sonoro.zeliuk.xyz`. El navegador ejecuta configuración, búsqueda/selección, progreso, imagen decorativa y escucha local. El QR/NFC habitual incorpora `#token=<id-cuadro>`. |
| API/importador | Derivar el ámbito desde cualquier identificador válido, buscar, crear/procesar tareas, preparar medios y publicar configuraciones. No autentica usuarios ni consulta una lista de acceso. Cada tarea usa RapidAPI para preparar el MP3 seleccionado. Carlos comunica que el backend funciona en Render con RapidAPI; Codex no verificó el servicio en esta fase ni el recorrido desde la web pública. |
| Realtime Database | Configuración por cuadro y estado durable de tareas. |
| Storage | Audio e imágenes preparados, con limpieza según referencias. |
| `firmware/common/` | Implementación compartida de las vistas LVGL, presentación de QR y recursos de prueba portables. No accede a sistema de archivos, SDL, red ni periféricos. |
| `firmware/simulator/` | Ventana SDL2, entrada de teclado, carga de imágenes locales, script de lectura RTDB/Storage y modo Firebase del simulador. |
| `firmware/esp32/` | Arranque ESP-IDF, BSP oficial Waveshare, panel 480 × 480 y memoria de placa. El firmware v0.1 recorre cuatro vistas de diagnóstico; no implementa todavía funciones de producto. |

El audio no atraviesa la API al reproducirse. No se añaden órdenes web de reproducir/detener ni volumen remoto. El estado configurado y la reproducción activa deben modelarse por separado para preservar un audio en uso durante una sustitución.

## Flujo de incorporación

Búsqueda → selección explícita → tarea → descarga → preparación → subida → publicación del hueco. Solo se sustituye tras preparar todos los recursos. El error conserva el contenido anterior. Tras retirar una selección, la API borra los objetos del cuadro sin referencias publicadas ni subidas activas; el reproductor local se detiene antes. El firmware todavía no tiene leases de reproducción.

Una tarea aceptada se guarda en RTDB o SQLite local durable. Con una instancia y un worker, el inicio reencola ejecuciones interrumpidas hasta dos veces para repetir descarga y conversión desde cero; después indica que hay que cancelar y volver a elegir. Cancelar y vaciar hueco actualiza el registro durable, y la publicación comprueba la ejecución vigente en la misma transacción que marca `ready`. SQLite local serializa cambios y Compose mantiene el archivo en un volumen nombrado. Si Compose usa la misma RTDB que Render, su worker puede consumir tareas creadas por Render; no se deben ejecutar ambos contra una cola compartida hasta resolver coordinación/exclusión.

## Acceso

El identificador se envía a la API en `Authorization: Bearer` como selector de ámbito, no como autenticación. Cualquier valor de 1–128 caracteres ASCII que cumpla el formato documentado crea o recupera su cuadro; API y cliente de dispositivo derivan el mismo SHA-256 para RTDB (`frames/{sha256}`), SQLite (`frame_states`) y Storage. No hay lista de acceso ni cuentas. Quien conoce o elige un identificador puede cambiar ese ámbito por API. Por decisión expresa de Carlos, RTDB y Storage sirven además lecturas públicas por URL conocida: solo el nodo `slots` del cuadro se puede leer, las tareas y el listado raíz quedan cerrados, y Storage permite obtener objetos individuales sin permitir listarlos. El hash separa datos, no autoriza. Credenciales Admin solo en backend y herramientas privadas.

La web acepta el identificador en el fragmento, lo guarda en `sessionStorage` y limpia la barra. Cualquier identificador válido crea/recupera su ámbito. RapidAPI solo se comunica desde el backend; su clave no llega al navegador. Los objetos publicados tienen URLs directas estables sujetas a las reglas de lectura pública por URL conocida. La reproducción del navegador es local y no informa sobre el estado de reproducción física.

El acceso habitual usa `https://sonoro.zeliuk.xyz/#token=cuadro-demo`; web y cuadro pueden estar en redes distintas si el móvil tiene Internet. El navegador llama a `https://cuadro-sonoro.onrender.com`; CORS requiere el origen exacto `https://sonoro.zeliuk.xyz` en `ALLOWED_ORIGINS` (sin barra final). Esta variable existe en el backend, pero no se afirma que Render ya tenga el valor aplicado. La URL `meta[name="sonoro-api-base"]` del código aún apunta a Render. La búsqueda usa yt-dlp y RapidAPI descarga el ID seleccionado desde backend. Los fallos históricos HTTP 429/403 correspondían a descargas yt-dlp y son antecedentes, no bloqueo vigente de RapidAPI.

Los scripts de servidor local/Bonjour se conservan como herramientas de desarrollo y sus pruebas como antecedentes, no como acceso de producto. Versiones del firmware: ESP-IDF 5.5.5, BSP `waveshare/esp32_s3_touch_lcd_4b` 2.0.0 y LVGL 9.5.0 en ambos destinos. El firmware compila en macOS Intel; la compilación en Apple Silicon y las pruebas físicas siguen pendientes. Los componentes para el primer prototipo y el cableado propuesto están en [HARDWARE.md](HARDWARE.md); no hay montaje físicamente validado. No se conoce el proveedor o procedimiento de publicación del hosting de Carlos; la guía solo puede especificar publicar el contenido estático de `web/` por HTTPS sin inventar comandos ni rutas.

## Primera instalación y controles físicos acordados

Sin credenciales guardadas, el ESP32 crea un punto de acceso temporal identificable por dispositivo y protegido por una contraseña propia incluida en el QR de conexión. La pantalla guía a la persona al portal cautivo local; si este no se abre, muestra una dirección de respaldo aún por confirmar en firmware. El asistente permite actualizar redes, introducir la contraseña doméstica y volver a probar sin reiniciar el recorrido. Opera sin Internet ni servicios cloud. Se distingue conexión al router de acceso a Internet: perder Internet no invalida ni borra credenciales.

Una vez conectado, el cuadro conserva las credenciales, cierra el punto temporal y muestra el QR musical. El dispositivo genera este QR desde el identificador estable; no lo descarga desde Firebase. Mantener botón 1 durante 2 segundos lo muestra durante 20 segundos sin tocar el audio. Para restablecer únicamente Wi-Fi se mantienen 2+3 juntos durante 5 segundos; la cuenta atrás se cancela al soltar cualquiera. Se conservan identificador, selecciones, imagen decorativa y volumen. Pulsaciones cortas activan/detienen huecos y la rueda solo ajusta volumen. El firmware debe dar prioridad a 2+3, suprimir la acción corta cuando hay gesto largo/combinado y evitar repetición mientras se mantienen los botones.

Con credenciales guardadas, el cuadro intenta reconectar e informa de fallos temporales sin abrir el asistente automáticamente. Los tiempos, la dirección del portal y todo el comportamiento están acordados pero pendientes de implementación y comprobación en hardware. No se ha elegido placa ni librería; WiFiManager es solo candidato.

## Decisiones aplazadas

Mecanismo de lectura/sincronización del firmware de producto; cola/worker definitivo; referencias para limpieza de reproducciones; límites y formatos finales; validación física del hardware. La URL pública de web está decidida; publicación efectiva, HTTPS, CORS y recorrido completo desde ese origen están pendientes de comprobación.
