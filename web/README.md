# Web

Desde la raíz del repo, con Python 3:

```bash
python3 -m http.server 5173 --bind 127.0.0.1 --directory web
```

Abre [la interfaz](http://127.0.0.1:5173). `Ctrl+C` detiene el servidor y sus logs se ven en esa terminal. No hay instalación npm, bundler ni variables secretas de frontend. No abrir `index.html` como archivo local: usar HTTP para los módulos.

`index.html`, `style.css` y `app.js` conservan el diseño aprobado. Hoy JS está concentrado en un archivo: modularizar sin rediseñar, separando componentes, estado y servicios. La demo usa localStorage, no Firebase; se activa explícitamente con «Probar demostración».

En «Emisora», la web busca Radio Browser por nombre y país opcional, permite elegir un resultado y conserva la entrada manual de URL HTTPS como alternativa. Si Radio Browser proporciona un logo HTTPS, se muestra centrado en la portada; si falta o no carga, la tarjeta conserva el nombre y el diseño habitual. Los resultados pueden estar caídos o usar formatos que el navegador/ESP32 no soporta; la búsqueda no los prueba. La escucha local confirma solo el navegador utilizado.

En una selección real, el botón play superpuesto a la portada inicia el audio en este navegador. Cambia a stop mientras suena; al tocarlo se detiene, y al terminar vuelve a play. No hay panel inferior de reproducción ni autoplay. Esto solo controla la escucha local, no el ESP32.

## Acceso mediante enlace de cuadro

El formato acordado es `http://cuadro-sonoro-<id-dispositivo>.local/#token=<id-cuadro>`; por ejemplo, `http://cuadro-sonoro-dev001.local/#token=cuadro-prueba`. En esta fase lo sirve un Mac en la LAN mediante Bonjour; en el producto lo servirá el ESP32. Debe abrirse desde un móvil conectado a la misma Wi-Fi. No usar `localhost` en un enlace del cuadro: en el móvil señalaría al propio teléfono. La resolución Bonjour/mDNS desde el móvil concreto y router del usuario todavía debe validarse. El identificador admite entre 1 y 128 caracteres ASCII: letra o número inicial, seguidos de letras, números, guion o guion bajo. No es una credencial. El fragmento no se incluye en la petición HTTP que obtiene la web. `app.js` lo lee al cargar o al cambiar el hash, lo guarda en `sessionStorage` de esa pestaña y lo retira de la barra de direcciones sin recargar. Las peticiones a la API lo envían como `Authorization: Bearer ...` para seleccionar el ámbito. Al cambiar de enlace se cancelan las peticiones del cuadro anterior y se limpia su estado antes de consultar el nuevo. Un identificador nuevo crea un cuadro vacío; el mismo recupera los registros existentes. Una entrada mal formada se rechaza sin activar la demo.

La configuración versionada en `meta[name="sonoro-api-base"]` apunta a `https://cuadro-sonoro.onrender.com`; el navegador móvil llama a Render directamente. Para prueba sin backend local, sigue [PRUEBA_WEB_LOCAL.md](../docs/PRUEBA_WEB_LOCAL.md). Esa URL es pública y no contiene credenciales.

Si el fragmento no trae identificador, la interfaz permanece bloqueada hasta abrir un enlace o elegir explícitamente «Probar demostración». La URL base de API es configuración del sitio, no del usuario: no hay popup ni conexión manual en la interfaz.

### Prueba web completa desde un móvil

La configuración pública de la web llama a Render, no a una API local; por eso servirla con `python -m http.server` no requiere ni inicia el backend. Para una prueba móvil con hostname Bonjour, puerto 80, QR, CORS y diagnóstico por IP, sigue [PRUEBA_WEB_LOCAL.md](../docs/PRUEBA_WEB_LOCAL.md). Para ejecutar y verificar la API por separado con SQLite local, usa [backend/README.md](../backend/README.md) y `docs/PRUEBA_API.md`.

La web servida por el ESP32 conservará en `meta[name="sonoro-api-base"]` la URL HTTPS pública de la API; el navegador la utiliza directamente. El QR/NFC físico sigue pendiente; la prueba Mac incluye servidor, anuncio Bonjour y QR local. Sigue la guía de [prueba web móvil](../docs/PRUEBA_WEB_LOCAL.md). Para probar el backend nativo/Docker, consulta [backend/README.md](../backend/README.md). Cualquier persona puede cambiar los datos de un identificador conocido; no uses datos privados. La cuenta de servicio nunca se introduce en la web. Las importaciones siguen necesitando Firebase Storage.

Check desde la raíz, con Node instalado:

```bash
node --check web/app.js
```

Al modificar la UI comprobar móvil, teclado abierto, modales, estados vacíos/error/carga, lectura de progreso y escucha local. El HTML de las búsquedas y los cambios de hueco se actualizan sin recargar la página. No añadir comandos al ESP32.

En el producto, empaquetar los archivos de `web/` en el firmware y servirlos desde el ESP32 en la Wi-Fi doméstica. Esta integración aún no existe y depende de elegir placa y entorno de firmware; documentar instalación, actualización y comprobaciones cuando se implemente. El móvil debe conservar salida a internet para acceder a Render. No se necesita publicar los archivos web en el servidor externo de Carlos.
