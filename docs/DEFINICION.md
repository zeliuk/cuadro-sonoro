# Cuadro sonoro — Definición del proyecto

**Fecha:** 12 de noviembre de 2026  
**Repositorio previsto:** `cuadro-sonoro`, público  
**Nombre visible provisional:** Sonoro  
**Estado:** decisiones de producto acordadas; implementación e integraciones por validar.

Este documento consolida la definición acordada antes de reconstruir el repositorio. Describe el comportamiento que debe tener el producto, no certifica que ya esté implementado. Las propuestas del prototipo anterior deben revisarse contra esta definición; en caso de contradicción, prevalecen las decisiones recogidas aquí.

## 1. Objetivo y alcance inicial

Un cuadro decorativo con pantalla a color, altavoz y reproducción autónoma por Wi-Fi. Puede colgarse en la pared o apoyarse en una estantería. El móvil permite configurar sus selecciones; para escuchar no es necesario mantener la web abierta ni utilizar el teléfono.

La primera versión incluye tres selecciones independientes, cada una con una canción o una emisora. Las canciones se preparan previamente mediante un servicio externo y quedan almacenadas en Firebase. Las emisoras se escuchan directamente desde su streaming.

La experiencia debe resultar sencilla para regalar el cuadro a una persona sin conocimientos técnicos. Esa persona podrá configurar la Wi-Fi con su móvil, sin instalar una aplicación ni programar el dispositivo.

## 2. Acceso por QR/NFC y primera instalación

### Acceso habitual

- Cada cuadro tiene un token aleatorio, largo y difícil de adivinar, fijado por el desarrollador al preparar el dispositivo.
- Ese token relaciona el acceso web, los datos del cuadro y el ESP32. No es un identificador numérico predecible ni una credencial global para todos los cuadros.
- El QR y el NFC habituales abren la web alojada en el servidor de Carlos, con acceso al cuadro correspondiente.
- El enlace entrega el token mediante el fragmento, con formato `https://dominio/#token=<token>`. El navegador lo consume sin incluirlo en la petición al servidor web y después limpia la barra de direcciones.
- No se plantea un registro ni un selector de usuarios para la primera versión. Quien tenga el enlace podrá consultar y cambiar la configuración de ese cuadro.
- Las selecciones pertenecen al cuadro y son compartidas entre quienes acceden desde distintos móviles.
- No se añade una credencial de dispositivo que el destinatario deba introducir o gestionar. El mecanismo técnico de autorización se resolverá durante la implementación respetando esta experiencia.

### Configuración Wi-Fi

1. En la primera instalación, sin una red guardada, el cuadro crea una red Wi-Fi temporal.
2. La pantalla muestra un QR para conectarse a esa red y unas instrucciones breves.
3. El móvil solicita confirmar la conexión. Un portal cautivo abre el asistente; si no aparece, la pantalla ofrece una dirección local de respaldo.
4. La persona selecciona su red doméstica e introduce la contraseña.
5. El ESP32 comprueba la conexión. Si falla, permite corregirla. Si funciona, guarda la configuración y cierra la red temporal.

La contraseña Wi-Fi se conserva en el dispositivo y no se envía a Firebase. Para cambiarla, se mantiene pulsado cualquiera de los tres botones. Una cuenta atrás en pantalla permite soltarlo antes de confirmar el restablecimiento. Este proceso borra únicamente la configuración Wi-Fi y conserva token, selecciones y volumen.

El QR temporal de instalación y el QR/NFC habitual de configuración musical tienen funciones distintas. Una caída temporal de internet no borra la red guardada ni abre automáticamente el asistente de instalación.

## 3. Tres huecos y controles físicos

Cada hueco representa una única canción o emisora. No se incluyen listas de reproducción en la primera versión.

| Acción | Resultado |
|---|---|
| Pulsar un botón con contenido, sin reproducir ese hueco | Reproduce su selección. |
| Pulsar un botón de otro hueco | Cambia a la selección de ese hueco. |
| Pulsar el botón del hueco que está sonando | Detiene la reproducción y vuelve a la imagen decorativa. |
| Pulsar un hueco vacío | No inicia reproducción. |
| Mantener pulsado cualquiera de los botones | Tras la cuenta atrás, restablece la Wi-Fi y abre el asistente. |
| Girar el control de volumen | Modifica el volumen del cuadro. |

Habrá tres pulsadores momentáneos retroiluminados y un control físico de volumen, preferentemente una rueda. El componente concreto se elegirá con el hardware.

| Estado del hueco | Luz del pulsador |
|---|---|
| Vacío | Apagada. |
| Con selección disponible, sin sonar | Tenue. |
| Conectando o cargando audio para reproducir | Aumenta y disminuye suavemente. |
| Reproduciendo | Fija y más intensa. |
| Reproducción detenida o canción finalizada | Vuelve a tenue. |

Se mantiene la propuesta estética de un color cálido; el brillo y el modelo de pulsador se concretarán más adelante. La luz indica el estado del audio del cuadro, independiente del progreso de importación mostrado en la web.

## 4. Canciones y emisoras

### Añadir una canción

1. Abrir un hueco vacío o cambiar el contenido de uno ocupado.
2. Seleccionar «Canción» e introducir artista y título.
3. El servicio busca en YouTube y devuelve unos pocos resultados con título, miniatura y duración.
4. La persona elige el resultado; no se importa automáticamente la primera coincidencia.
5. Se crea una tarea de importación. El servicio obtiene y prepara el audio, la imagen y los metadatos.
6. La web muestra su progreso. Cuando termina correctamente, la selección queda disponible.

No se utiliza la API de Spotify. El importador previsto utiliza Python, `yt-dlp` y FFmpeg. La obtención desde YouTube requiere validación real desde el alojamiento elegido y puede necesitar mantenimiento.

### Añadir una emisora

Radio Browser es el proveedor elegido para el directorio de emisoras. La web ofrecerá búsqueda por nombre, un filtro opcional por país y unas pocas sugerencias revisadas.

Los resultados mostrarán nombre, país y logo cuando esté disponible. Antes de asignar uno se comprobará el acceso a su emisión y su compatibilidad con el reproductor elegido. Se filtrarán resultados caídos o incompatibles y se tratarán los posibles duplicados.

Se guardan los datos de la emisora y la dirección de streaming. No se descarga ni se graba su programación. El ESP32 se conecta directamente a esa dirección. El directorio no debe ser una dependencia obligatoria en cada reproducción; se conserva también la identidad de la emisora para futuras actualizaciones de su enlace.

## 5. Importaciones, progreso y sustitución

- Se permite una importación por cuadro a la vez. Las otras selecciones siguen utilizándose mientras se procesa.
- Las tareas y su progreso se guardan fuera del navegador. Cerrar la web no cancela una tarea aceptada; al volver se recupera su estado.
- Se muestra actividad durante las etapas sin porcentaje medible y progreso real cuando la descarga o subida lo permitan. No se presentan porcentajes inventados como reales.
- La interfaz distingue búsqueda, descarga, preparación, guardado y resultado final.
- Si una importación falla, se conserva la selección anterior y se ofrece reintentar o cancelar.
- Se admite cancelación y se limpian los archivos temporales y resultados que queden sin utilizar.
- Una tarea completa solo publica una selección cuando audio, imagen y metadatos necesarios están preparados.

La ejecución debe soportar interrupciones y evitar duplicar publicaciones o borrar contenido vigente al reintentar. Guardar el estado en Firebase no sustituye por sí solo un mecanismo fiable de ejecución. La cola, el proceso que la consume y la recuperación tras reinicios se concretarán antes del despliegue definitivo en Render.

### Si el hueco está sonando durante un cambio

La reproducción anterior continúa hasta que se detenga o termine la canción. Publicar la nueva selección no inicia sonido ni corta lo que estaba sonando. La pantalla conserva los datos del audio realmente activo. La nueva selección se utiliza la próxima vez que se inicie ese hueco. Pulsar el botón activo continúa significando «detener».

## 6. Reproducción y escucha desde la web

### En el cuadro

- El ESP32 no lleva microSD ni almacena canciones completas de forma permanente.
- Recibe el MP3 directamente desde Firebase Storage y lo reproduce por streaming con un búfer en memoria.
- No espera a descargar el archivo completo para empezar. El objetivo es un inicio en pocos segundos con una conexión estable; el tiempo real se medirá con el hardware.
- Render interviene en la incorporación de contenido, no en el recorrido normal del audio ya preparado.
- Al terminar una canción se detiene. No repite ni salta automáticamente a otro hueco.
- Las emisoras continúan hasta detenerlas, cambiar de selección o encontrar un problema de conexión que impida seguir.
- Al encender o reiniciar, el cuadro muestra la imagen decorativa y permanece en silencio. Conserva selecciones y último volumen utilizado.
- El volumen se controla con la rueda física. No se incluye ajuste remoto de volumen desde la web.

### En la web

Cada selección podrá ofrecer «Escuchar aquí». El sonido se reproduce en el navegador y no se envían órdenes al cuadro.

Para canciones, la prueba está disponible después de completar la importación y utiliza el mismo MP3 definitivo. Se reproduce una única selección a la vez en la web. La escucha de prueba es independiente del sonido y el volumen físicos del cuadro.

Para emisoras, la escucha en el navegador queda sujeta a que el stream permita reproducción web; esta compatibilidad debe comprobarse aparte de la del ESP32.

No se incluyen comandos remotos de reproducir, detener o volumen dirigidos al cuadro en esta versión. La web modifica configuración y permite escuchar localmente; los botones y la rueda gobiernan el dispositivo.

## 7. Concepto físico y hardware pendiente

El objeto podrá colgarse o apoyarse. Se busca un frente decorativo de vidrio o metacrilato con la pantalla integrada y el sistema oculto detrás.

Como concepto, una lámina, impresión o zona opaca oculta cables y componentes, dejando una ventana para la pantalla. Una pieza o franja inferior puede alojar los pulsadores y la rueda; sus cables pasan directamente a la carcasa trasera. No se pretende que todo el frontal sea transparente y deje la electrónica visible.

Se aplazan medidas, material definitivo, alimentación, altavoz, amplificador, ESP32 concreto, pantalla, distribución de pines y construcción de la carcasa. Habrá que presupuestar conexiones para botones, iluminación, volumen, pantalla y audio antes de comprar componentes.

## 8. Pantalla e imágenes

| Estado | Contenido |
|---|---|
| En reposo | Imagen decorativa independiente, elegida desde la web. |
| Canción reproduciéndose | Carátula, título y artista. |
| Emisora reproduciéndose | Logo y nombre. |
| Conectando al audio | Imagen de la selección e indicador de carga. |
| Ajustando volumen | Nivel de volumen durante unos segundos. |
| Configurando Wi-Fi | QR, instrucciones y resultado del asistente. |
| Restableciendo Wi-Fi | Cuenta atrás de confirmación. |
| Problema de conexión | Mensaje comprensible. |

La pantalla será a color, sin necesidad de función táctil ni vídeo en la primera versión. La información de canción en una emisora solo podrá considerarse una mejora posterior si los metadatos del stream lo permiten; no es requisito para su funcionamiento.

### Imagen decorativa

1. La persona sube una imagen normal desde el móvil u ordenador.
2. La web muestra una vista previa con la proporción real de pantalla y permite ajustar el encuadre.
3. Render valida el archivo, corrige orientación, aplica encuadre, adapta resolución y comprime.
4. Se eliminan metadatos innecesarios, incluida ubicación GPS cuando exista.
5. Se guarda la versión optimizada y se actualiza la configuración cuando esté lista.

La resolución, formato, calidad y peso máximo se decidirán con la pantalla. No se conserva el original como archivo permanente. Carátulas y logos también se optimizan, con un tratamiento de encuadre adecuado para no cortar información relevante.

La imagen anterior permanece hasta completar la nueva. Al terminar o detener el sonido se vuelve a la imagen decorativa. El detalle de su conservación local y la presentación en arranque sin red se resolverá al implementar el firmware, sin añadir almacenamiento de canciones completas.

## 9. Acceso y protección de datos

El modelo de producto es acceso mediante posesión del enlace con token del cuadro. No hay roles de propietario e invitado ni inicio de sesión para el destinatario en la primera versión. El desarrollador prepara la vinculación del dispositivo.

Esto no significa hacer públicos los registros ni entregar credenciales de administración. La API recibe el token aleatorio fijo del cuadro como Bearer; comprueba su SHA-256 contra `FRAME_TOKEN_HASHES` y usa ese hash como ámbito. Para que el ESP32 lea directamente sin Render, el desarrollador aprovisiona el mismo token como contraseña de una cuenta técnica Firebase Auth con UID derivado del hash. Firebase emite ID/refresh tokens técnicos; el dispositivo renueva la sesión Firebase cuando haga falta, pero el token del cuadro no cambia. Las reglas autorizan solo `frames/{sha256}/slots` y medios bajo `private/frames/{sha256}/`, tras comprobar identidad autenticada y cuadro coincidente. Conocer la ruta o su hash no basta. El familiar no crea ni gestiona cuentas o credenciales. Esta ruta de acceso está implementada con soporte mínimo y pendiente de validación contra un proyecto Firebase real y el firmware.

Los tokens reales, credenciales administrativas, archivos de cuentas de servicio y claves privadas no se publican en GitHub, capturas, documentación de ejemplo o registros de diagnóstico. La contraseña doméstica se mantiene en el ESP32.

## 10. Datos, conservación y limpieza

| Lugar | Contenido |
|---|---|
| Realtime Database | Cuadros, relación con su acceso, tres selecciones, imagen decorativa y tareas con su estado/progreso. |
| Firebase Storage | MP3 e imágenes optimizadas que siguen en uso y resultados temporales necesarios para una sustitución. |
| ESP32 | Configuración técnica, Wi-Fi, último volumen y los datos necesarios para funcionar; audio solo en búfer. |
| Navegador en demo | Datos ficticios separados del sistema real. |

No se construye una biblioteca histórica ilimitada. Al sustituir o eliminar contenido se borran los archivos y metadatos que dejan de tener referencias. Si un recurso está compartido entre huecos o cuadros, o sigue utilizándose en una reproducción, se conserva mientras corresponda.

Durante una sustitución pueden coexistir temporalmente la versión anterior y la nueva. También se limpia contenido abandonado por fallos y cancelaciones. El detalle de referencias de reproducción, plazos de limpieza y política de borrado del bucket debe concretarse para que la limpieza sea segura y predecible.

## 11. Stack y arquitectura

| Componente | Elección |
|---|---|
| Web | HTML, CSS y JavaScript en módulos, manteniendo el diseño aprobado. |
| API | Python con FastAPI. |
| Importador | `yt-dlp`, FFmpeg y procesamiento de imágenes. |
| Backend externo | Docker desplegado en Render. |
| Datos | Firebase Realtime Database. |
| Audio e imágenes | Firebase Storage. |
| Firmware | C++; entorno y librerías por concretar con el hardware. |

La web será dinámica: búsquedas, resultados, formularios, progreso, actualización de huecos, imagen y escucha local funcionan sin recargas completas durante el uso normal. La interfaz separa estilos, componentes visuales, servicios de comunicación y lógica de estado.

Diseño primero para móvil: una columna cuando corresponda, controles cómodos, ventanas adaptadas al teclado y sin desbordamientos, imágenes optimizadas, audio iniciado por acción del usuario, dependencias mínimas y peticiones limitadas a lo necesario. El procesamiento pesado se realiza en Render.

La configuración publicada y lo que está reproduciéndose son estados distintos. No se debe afirmar que el ESP32 ha aplicado un cambio por el mero hecho de guardarlo en Firebase. Tampoco se requiere añadir un panel de órdenes remotas para cumplir la configuración básica.

## 12. Alojamiento, coste y recuperación

- La web se aloja en el servidor y dominio de Carlos. No se utiliza Firebase Hosting.
- API e importaciones se ejecutan externamente en Render con Docker; Firebase Functions queda como alternativa no elegida para esta base.
- Firebase proporciona datos y almacenamiento de archivos. Sus cuotas, región y configuración de facturación se revisarán antes del despliegue. Storage requiere Blaze; no se garantiza coste cero.
- La suspensión de Render gratuito y la ejecución fiable de trabajos son aspectos pendientes de validar. No se dará por garantizada la continuidad de una tarea por dejarla en un proceso de fondo sin recuperación.
- Cada reproducción desde Storage genera tráfico de salida, aunque solo existan tres selecciones y se limpie contenido antiguo.

| Incidencia | Comportamiento acordado |
|---|---|
| Búsqueda fallida | Mensaje y opción de reintentar. |
| Importación fallida | Mantener selección previa, reintentar o cancelar. |
| Cerrar la web | Recuperar configuración y estado de tareas al volver. |
| Error al escuchar en el navegador | Informar y permitir reproducir de nuevo. |
| Caída de internet en el cuadro | Intentar reconectar; si se agota el búfer, detener e informar. |
| Caída temporal de red | Conservar credenciales Wi-Fi y selecciones. |

Queda pendiente fijar si el cuadro reanuda automáticamente un audio interrumpido por la red. Sí está decidido que el encendido y reinicio no arrancan música automáticamente.

## 13. Identidad y demostración

El repositorio se llama `cuadro-sonoro`. Sonoro continúa como nombre provisional de la interfaz. Se conserva el lenguaje visual cálido y decorativo del prototipo aprobado; no se rediseña por introducir organización modular.

Habrá un modo demostración para portfolio, utilizable sin credenciales y claramente identificado. Usará datos y recursos de ejemplo separados, sin acceder a cuadros reales, crear importaciones reales ni generar costes en los servicios del proyecto.

La demo podrá simular el flujo y el progreso, indicando que son simulaciones. Sus recursos de audio e imagen deben ser adecuados para publicarse junto al proyecto. La demo no demuestra por sí misma el funcionamiento real de YouTube, Firebase, Render o el ESP32.

## 14. Repositorio, documentación y forma de trabajar

Un único repositorio con esta separación:

| Carpeta | Responsabilidad |
|---|---|
| `web/` | Interfaz y modo demostración. |
| `backend/` | API, importador, procesamiento y pruebas. |
| `firmware/` | Código del ESP32 cuando se aborde esa fase. |
| `firebase/` | Configuración y reglas versionables sin credenciales. |
| `docs/` | Arquitectura, decisiones, configuración, despliegue y fases. |

El README presentará el proyecto, funcionamiento, demo, instalación y estado real. `AGENTS.md` explicará cómo trabajar, documentos que leer, límites del alcance, convenciones y verificaciones. Se mantendrán documentación de arquitectura, stack, configuración, seguridad, contribución y primer encargo para Codex.

Credenciales en variables de entorno o mecanismos privados del proveedor, con plantillas de ejemplo sin valores reales. Una variable enviada al navegador es visible para ese navegador aunque proceda de un `.env`; los secretos administrativos permanecen en el backend. Los tokens de cuadros se introducen en la preparación privada del dispositivo y no se compilan como un valor compartido en el repositorio público.

El trabajo se divide en cambios pequeños, con comprobaciones relevantes y revisión móvil. Se respetan los cambios existentes y se actualizan los documentos cuando cambie una decisión. No se añade un framework por defecto ni se confunde una comprobación con mocks con una integración verificada.

### Instrucciones compartidas con ChatGPT

Las instrucciones del proyecto ChatGPT se versionan en `docs/INSTRUCCIONES_CHATGPT.md`, dentro del mismo repositorio. Git es la referencia de ese texto. Codex lo actualiza cuando cambien producto, alcance, stack o forma de trabajo y avisa de ello al cerrar la tarea. Carlos copia manualmente el contenido actualizado a las instrucciones de ChatGPT y renueva los adjuntos de definición/estado cuando corresponda. No hay sincronización automática entre esos archivos y el proyecto ChatGPT.

### Documentación operativa obligatoria por componente

La documentación debe permitir arrancar y probar cada parte desde una instalación limpia, sin depender de explicaciones del chat. No basta con describir la arquitectura: se incluyen los comandos completos y la respuesta esperada de cada comprobación. Cada carpeta tendrá un README operativo, enlazado desde el README raíz, y guías específicas cuando el detalle lo justifique.

| Componente | Instrucciones y comandos que debe incluir |
|---|---|
| `web/` | Requisitos, configuración de demo y modo real, arranque del servidor local, URL que abrir, conexión con la API, comprobaciones disponibles y publicación en el servidor de Carlos. |
| `backend/` | Versiones y dependencias, entorno virtual, instalación, plantilla de variables, arranque local y con Docker, ejecución de las tareas en segundo plano, pruebas, logs, parada, reinicio y despliegue en Render. |
| `firebase/` | Creación/configuración de recursos, conexión desde el backend, reglas, comandos de validación y despliegue cuando corresponda, emuladores si se incorporan y verificación de acceso con un cuadro de prueba. |
| `firmware/` | Al abordar esta fase: herramientas, preparación privada del cuadro, compilación, carga por USB, monitor serie, configuración Wi-Fi, pruebas de audio/pantalla/controles y restablecimiento Wi-Fi. |
| `docs/` | Guía de inicio completa, catálogo de API, recorrido de prueba paso a paso, despliegue y resolución de problemas habituales. |

Cada bloque de comandos indicará desde qué carpeta ejecutarlo, qué requisitos debe tener instalados la persona, qué variables de ejemplo necesita y qué resultado debe obtener. Se distinguirá terminal anfitrión, entorno virtual y contenedor; también los comandos locales y los de despliegue. Se documentará cómo detener los procesos y limpiar recursos de prueba sin borrar configuración o archivos reales. La ruta recomendada se explicará de principio a fin; las alternativas solo se incluirán si están soportadas.

### Documentación detallada de la API

El backend tendrá un catálogo de todos los endpoints implementados, complementado con documentación interactiva basada en OpenAPI. El catálogo explicará el propósito y el uso real de cada operación, incluyendo:

- Método HTTP, ruta, URL base y requisitos de acceso mediante el token del cuadro, según el contrato de autorización que se implemente.
- Parámetros de ruta y consulta, cabeceras, cuerpo JSON o subida de archivos, campos obligatorios, tipos y límites.
- Ejemplo completo de llamada con `curl`, usando únicamente tokens y datos ficticios, con las variables necesarias definidas de forma explícita.
- Ejemplo de respuesta, códigos HTTP relevantes y errores habituales con su significado y forma de resolverlos.
- Si una operación es síncrona o crea una tarea; identificador de tarea, estados, consulta o seguimiento del progreso, cancelación, reintento y comportamiento ante solicitudes repetidas cuando corresponda.
- Recursos que modifica, archivos que crea o elimina y condiciones para publicar la nueva selección.
- Diferencias entre modo demostración, proveedores simulados, emuladores y servicios reales, cuando proceda.

Se cubrirán las operaciones que realmente existan para búsqueda de canciones y emisoras, importación y tareas, consulta/actualización de los tres huecos, imágenes y comprobación de disponibilidad del servicio. Esta lista describe capacidades que deben quedar documentadas, no fija todavía nombres de rutas. No se añadirán endpoints de control remoto del sonido del cuadro, que quedan fuera del alcance inicial.

Habrá además un recorrido reproducible de prueba manual: arrancar los servicios, comprobar su disponibilidad, buscar una canción, elegirla, iniciar la importación, seguir su estado, comprobar la selección publicada y escuchar el archivo final en el navegador. Se documentarán también el caso de error y la conservación de la selección anterior. Las pruebas que generen consumo real o modifiquen datos se identificarán, empleando un cuadro y recursos destinados a pruebas.

### Regla para Codex y mantenimiento de las instrucciones

`AGENTS.md` exigirá actualizar las guías y los ejemplos en el mismo cambio que modifique rutas, campos, variables, comandos o comportamiento. Los comandos y ejemplos se contrastarán con el código y se ejecutarán cuando el entorno lo permita; se indicará cualquier paso pendiente de verificación. No se presentarán rutas propuestas como endpoints ya disponibles ni comandos sin comprobar como una puesta en marcha validada.

Esta definición incorpora el requisito documental. El catálogo con comandos y rutas concretos se elaborará al preparar la base ejecutable y evolucionará junto a su implementación.

### Orden de validación

1. Consolidar esta definición en la documentación y preparar una base coherente de repositorio.
2. Validar el recorrido real: buscar, elegir, procesar desde Render, subir audio e imagen a Firebase y escuchar el MP3 desde el navegador.
3. Conectar la web dinámica a tareas reales, incluyendo progreso, reintentos, sustitución y limpieza; integrar Radio Browser.
4. Elegir hardware y validar reproducción de MP3 y radio por Wi-Fi, controles físicos y volumen.
5. Integrar pantalla, imagen decorativa, luces y asistente Wi-Fi; comprobar recuperación y cambios durante reproducción.
6. Resolver diseño físico y documentar montaje y despliegue reproducibles.

### Pendientes antes o durante la implementación

- Placa, memoria, pantalla, audio, alimentación, ruedas/pulsadores, pines y medidas.
- Lectura autónoma del ESP32 y reglas de acceso directo a Firebase.
- Ejecución y recuperación de tareas, concurrencia global, plan de Render y validación de descargas desde ese entorno.
- Duración máxima de canciones, tiempos máximos de tareas, calidad MP3 y límites de subida de imágenes.
- Resolución y formato de imágenes, brillo de pantalla y duración exacta de pulsación para restablecer Wi-Fi.
- Conservación local de la imagen decorativa y comportamiento de pantalla sin red.
- Política de limpieza de recursos en uso, retención de estados de tareas y configuración de borrado del bucket.
- Comportamiento de reanudación tras una interrupción de audio por la red.
- Licencia del código y recursos publicables de demostración.

Estos pendientes no sustituyen las decisiones de producto ya acordadas. Se resolverán en su fase, documentando el resultado antes de extender el alcance.

### Referencias técnicas consultadas durante la definición

- [Render: Docker](https://render.com/docs/docker)
- [Render: servicios gratuitos](https://render.com/docs/free)
- [Firebase: precios y cuotas](https://firebase.google.com/pricing)
- [Firebase: requisitos de Storage](https://firebase.google.com/docs/storage/faqs-storage-changes-announced-sept-2024)
- [Radio Browser: API](https://docs.radio-browser.info/)
- [Espressif: reproducción y ejemplos multimedia](https://docs.espressif.com/projects/esp-adf/en/latest/multimedia-examples/index.html)
- [WiFiManager: configuración Wi-Fi mediante portal cautivo](https://github.com/tzapu/WiFiManager)

Los límites y condiciones de los proveedores pueden cambiar; se comprobarán de nuevo al desplegar.
