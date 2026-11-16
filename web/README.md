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

La configuración versionada en `meta[name="sonoro-api-base"]` apunta a `https://cuadro-sonoro.onrender.com`. Al servir estáticos localmente, el navegador llama a ese backend remoto; no hace falta iniciar Python/FastAPI local. Apify está integrado, pero el recorrido Render/Apify queda pendiente de la prueba real de [PRUEBA_APIFY_RENDER.md](../docs/PRUEBA_APIFY_RENDER.md).

Si el fragmento no trae identificador, la interfaz permanece bloqueada hasta abrir un enlace o elegir explícitamente «Probar demostración». La URL base de API es configuración del sitio, no del usuario: no hay popup ni conexión manual en la interfaz.

### Prueba web completa desde un móvil

Para la prueba solicitada basta servir `web/` en el puerto 5173; la API apunta a Render. La guía [PRUEBA_APIFY_RENDER.md](../docs/PRUEBA_APIFY_RENDER.md) contiene prueba, logs, límites y rollback. Para desarrollo aislado del backend, usa [backend/README.md](../backend/README.md).

El endpoint configurado para la prueba temporal es Render. Cuando el frontend se sirva desde ESP32, se debe volver a revisar conectividad y CORS desde móvil; el servidor/QR/NFC físicos siguen pendientes. Para probar el backend nativo/Docker, consulta [backend/README.md](../backend/README.md). Cualquier persona puede cambiar los datos de un identificador conocido; no uses datos privados. La cuenta de servicio nunca se introduce en la web. Las importaciones siguen necesitando Firebase Storage.

Check desde la raíz, con Node instalado:

```bash
node --check web/app.js
```

Al modificar la UI comprobar móvil, teclado abierto, modales, estados vacíos/error/carga, lectura de progreso y escucha local. El HTML de las búsquedas y los cambios de hueco se actualizan sin recargar la página. No añadir comandos al ESP32.

En el producto, empaquetar los archivos de `web/` en el firmware y servirlos desde el ESP32 en la Wi-Fi doméstica. Esta integración aún no existe y depende de elegir placa y entorno de firmware; documentar instalación, actualización y comprobaciones cuando se implemente. También falta elegir una URL de API accesible desde el móvil en LAN. No se necesita publicar los archivos web en el servidor externo de Carlos.
