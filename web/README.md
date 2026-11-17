# Web

Desde la raíz del repo, con Python 3:

```bash
python3 -m http.server 5173 --bind 127.0.0.1 --directory web
```

Abre [la interfaz](http://127.0.0.1:5173). `Ctrl+C` detiene el servidor y sus logs se ven en esa terminal. No hay instalación npm, bundler ni variables secretas de frontend. No abrir `index.html` como archivo local: usar HTTP para los módulos.

## Maqueta del objeto

La página independiente está en `web/maqueta/`; al usar el servidor anterior, ábrela en [http://127.0.0.1:5173/maqueta/](http://127.0.0.1:5173/maqueta/). No depende de npm, framework ni variables de entorno. El servidor HTTP de Python sirve el HTML, CSS, JavaScript y la imagen de referencia; sus logs aparecen en la misma terminal y `Ctrl+C` lo detiene.

El objeto ocupa el 90 % del lado más corto de la ventana: 90vh en orientación horizontal y 90vw en vertical. El encabezado y el estado de carga quedan encima, fuera del ancho de la imagen.

Elige el identificador en el enlace, por ejemplo `http://127.0.0.1:5173/maqueta/#token=cuadro-demo`; también se admite `?token=cuadro-demo`. No hay formulario para cambiarlo. Al abrir la página se lee el token de la URL, se conserva en `sessionStorage` de esa pestaña y se limpia el fragmento visible, igual que la interfaz principal. `cuadro-demo` es solo un ejemplo y un identificador válido puede abrir o crear un ámbito vacío. La página consulta `GET /state` y, al activar una selección con portada, `GET /media/{slot}` en la URL de API configurada en su `meta[name="sonoro-api-base"]`. Incluye el identificador como `Authorization: Bearer` por compatibilidad con la API. No es una credencial.

La consulta usa la API, que leerá Firebase si esa instancia está configurada con RTDB/Storage; si no, puede responder desde el almacenamiento local configurado. La maqueta no lleva credenciales de Firebase ni Admin SDK en el navegador. El API debe estar disponible y permitir CORS para el origen que sirve la página; para la prueba anterior es `http://127.0.0.1:5173`. Las respuestas y errores se muestran junto al cuadro; los detalles técnicos se pueden consultar en la consola del navegador y los logs de la API.

La página consulta `/state` al abrirse y después únicamente tras pulsar uno de sus botones; no mantiene un sondeo periódico ni vuelve a consultar al recuperar el foco. Así actualiza las selecciones cuando se interactúa con el cuadro virtual. Al recibir estado nuevo resuelve y conserva en memoria los enlaces de medios publicados para que el toque pueda iniciar el audio local sin esperar otra petición. Si los tres huecos están vacíos, el QR de ese ID queda fijo en la pantalla hasta que una consulta posterior detecte una selección. Los tres pulsadores sobre el cuadro cambian la selección y reproducen su audio en este navegador. Mantener el botón 1 durante 2 s muestra el QR en la pantalla durante 20 s, sin interrumpir la escucha. La portada se superpone a la pantalla. El audio y la rueda de volumen solo afectan a este navegador: no envían órdenes de reproducción ni volumen al ESP32 ni escriben en Firebase. La combinación 2+3 simula la cuenta atrás cancelable del restablecimiento Wi-Fi, pero no cambia datos. La reproducción del cuadro físico no se conoce desde la configuración publicada.

La cabecera, el logo y los colores de fondo y acento coinciden con los de la página principal (`web/style.css`).

## Vista de tablet a pantalla completa

La ruta estática `web/tablet/` dibuja el cuadro virtual a pantalla completa: usa un fondo cálido, una pantalla y controles centrados que escalan según ancho y alto. No muestra el marco de la fotografía de referencia. Los pulsadores y el mando de volumen son imágenes independientes montadas en `web/tablet/assets/`. La página reutiliza `maqueta.js` y la lógica de `/maqueta` para selecciones, audio local, QR y controles simulados; `tablet.css` define esta presentación sin duplicar esa lógica.

Requisitos: navegador moderno con soporte para JavaScript de módulos y Python 3 para servir los archivos estáticos en local. No hay instalación, variables de entorno ni secretos de frontend. Desde la raíz del repositorio, arranca el servidor:

```bash
python3 -m http.server 5173 --bind 127.0.0.1 --directory web
```

Abre `http://127.0.0.1:5173/tablet/#token=cuadro-demo`. Cambia `cuadro-demo` por el identificador del cuadro; también se puede servir la ruta en producción como `https://sonoro.zeliuk.xyz/tablet/#token=<id-cuadro>`. En local, una tablet debe poder acceder al servidor desde la red y el firewall del ordenador debe permitir el puerto 5173. La URL de API se hereda de la configuración HTML compartida. El backend debe permitir CORS para el origen del sitio y tener acceso a los datos que se quieran mostrar.

La primera pulsación en el fondo solicita pantalla completa al navegador; algunos navegadores requieren abrir la página en pantalla completa desde su propio menú o añadirla a la pantalla de inicio. Los botones del cuadro no se interceptan. La vista no muestra encabezado, estado de conexión ni controles externos al objeto; las indicaciones del QR y de restablecimiento aparecen dentro de la pantalla del cuadro, como en la maqueta. El navegador puede impedir el modo inmersivo, pero la página sigue ocupando toda su ventana.

Las selecciones consultadas y la reproducción siguen siendo solo de lectura y locales al navegador: no hay órdenes al ESP32 ni escrituras en Firebase. Revisa errores de JavaScript en la consola del navegador y solicitudes fallidas en los logs de la API; el servidor estático registra accesos en la terminal. Detén el servidor con `Ctrl+C`. Para desplegarla, publica `web/` completo en el hosting HTTPS existente, sin añadir un servicio; no se ha verificado la publicación de `/tablet/`.

El generador QR se incluye localmente en `qrcode.js` con su licencia MIT en `LICENSE-qrcode-generator`; no se envía el identificador a un servicio externo para producir el código. Usa extensión `.js` para que el hosting Nginx sirva el módulo con un tipo MIME de JavaScript reconocido por los navegadores.

Para publicar la sección, incluye `web/maqueta/` junto al resto del contenido estático de `web/`, bajo `/maqueta/`, en el mismo hosting HTTPS. El proveedor y los comandos de publicación siguen siendo los de [DESPLIEGUE.md](../docs/DESPLIEGUE.md); no se inventa un procedimiento de subida.

`index.html`, `style.css` y `app.js` conservan el diseño aprobado. Hoy JS está concentrado en un archivo: modularizar sin rediseñar, separando componentes, estado y servicios. La demo usa localStorage, no Firebase; se activa explícitamente con «Probar demostración».

En «Emisora», la web busca Radio Browser por nombre y país opcional, permite elegir un resultado y conserva la entrada manual de URL HTTPS como alternativa. Si Radio Browser proporciona un logo HTTPS, se muestra centrado en la portada; si falta o no carga, la tarjeta conserva el nombre y el diseño habitual. Los resultados pueden estar caídos o usar formatos que el navegador/ESP32 no soporta; la búsqueda no los prueba. La escucha local confirma solo el navegador utilizado.

En una selección real, el botón play superpuesto a la portada inicia el audio en este navegador. Cambia a stop mientras suena; al tocarlo se detiene, y al terminar vuelve a play. No hay panel inferior de reproducción ni autoplay. Esto solo controla la escucha local, no el ESP32.

## Acceso mediante enlace de cuadro

El acceso habitual decidido es `https://sonoro.zeliuk.xyz/#token=cuadro-demo` (identificador ficticio). El hosting sirve los archivos estáticos de `web/`; el ESP32 no aloja la web. El móvil necesita Internet, pero no la misma Wi-Fi del cuadro. El identificador acepta entre 1 y 128 caracteres ASCII, no es una credencial, y `app.js` lo lee del fragmento, lo guarda en `sessionStorage` de esa pestaña y limpia la barra sin recargar. Las peticiones API lo envían como `Authorization: Bearer ...` para seleccionar ámbito. Al cambiar de enlace se cancelan peticiones anteriores y se limpia el estado antes de consultar el nuevo. Un identificador nuevo crea un cuadro vacío; el mismo recupera registros existentes. Una entrada mal formada se rechaza sin activar demo. El origen y recorrido público aún requieren verificación de publicación.

### Generar el QR público

`scripts/generate_public_qr.py` genera enlaces `https://sonoro.zeliuk.xyz/#token=<id>` y guarda el ejemplo ficticio en `artifacts/qr/sonoro-cuadro-demo.png`. Requiere `qrcode[pil]`; instala la dependencia como se indica en [PRUEBA_WEB_LOCAL.md](../docs/PRUEBA_WEB_LOCAL.md). Para un ID asignado, usa una ruta de salida genérica con `--output`; el generador no imprime el enlace ni permite incluir el ID en el nombre por defecto. No compartas el PNG ni lo añadas al repositorio.

```bash
.venv-qr/bin/python scripts/generate_public_qr.py --token mi-cuadro-prueba --output artifacts/qr/cuadro.png
```

El QR/NFC del cuadro debe abrir la web pública con su ID en el fragmento. El servidor Bonjour y su generador local son herramientas de desarrollo independientes; no se usan para crear los QR del producto.

`web/index.html` configura `meta[name="sonoro-api-base"]` con `https://cuadro-sonoro.onrender.com`. CORS de backend debe permitir `https://sonoro.zeliuk.xyz` mediante `ALLOWED_ORIGINS`; la documentación de esa variable no significa que ya esté aplicada en Render. La búsqueda usa yt-dlp y RapidAPI descarga el resultado seleccionado desde el backend. Carlos comunica que el backend funciona con RapidAPI en Render; no se ha verificado por Codex la web pública ni el flujo desde ella. Ver [PRUEBA_RAPIDAPI.md](../docs/PRUEBA_RAPIDAPI.md).

Si el fragmento no trae identificador, la interfaz permanece bloqueada hasta abrir un enlace o elegir explícitamente «Probar demostración». La URL base de API es configuración del sitio, no del usuario: no hay popup ni conexión manual en la interfaz.

### Prueba web completa desde un móvil

Para la prueba local sirve `web/` en el puerto 5173 y arranca la API en el puerto 8000; ambos se ejecutan en el mismo equipo. La guía [PRUEBA_RAPIDAPI.md](../docs/PRUEBA_RAPIDAPI.md) explica configuración y límites de la descarga. Para desarrollo aislado del backend, usa [backend/README.md](../backend/README.md).

El endpoint de producción es la API Render. Para backend local/Docker, cambia temporalmente el meta a `http://127.0.0.1:8000`; consulta [backend/README.md](../backend/README.md). Cualquier persona que conozca un identificador puede cambiar sus datos; no uses datos privados. La cuenta de servicio nunca se introduce en la web. Las importaciones necesitan Firebase Storage. El QR/NFC habitual abre el dominio público; el QR del portal Wi-Fi local del ESP32 tiene otra finalidad.

Check desde la raíz, con Node instalado:

```bash
node --check web/app.js
```

Al modificar la UI comprobar móvil, teclado abierto, modales, estados vacíos/error/carga, lectura de progreso y escucha local. El HTML de las búsquedas y los cambios de hueco se actualizan sin recargar la página. No añadir comandos al ESP32.

La publicación del producto consiste en servir el directorio estático `web/` desde `https://sonoro.zeliuk.xyz`. Esta dirección está decidida, pero publicación efectiva, HTTPS y conexión CORS requieren verificación. No se conocen proveedor, panel, credenciales o comandos de subida; consultar [DESPLIEGUE.md](../docs/DESPLIEGUE.md) sin asumirlos. El ESP32 solo tendrá su portal local de configuración/restablecimiento Wi-Fi; firmware y hardware siguen pendientes.
