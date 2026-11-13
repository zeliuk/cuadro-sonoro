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

En el producto, el formato previsto es `http://sonoro-<sufijo-unico>.local/#token=<identificador>`; por ejemplo, en desarrollo local `http://127.0.0.1:5173/#token=mi-cuadro-prueba`. El primer enlace lo servirá el ESP32 por mDNS y debe abrirse desde un móvil conectado a la misma Wi-Fi. No usar `localhost` en un enlace del cuadro: en el móvil señalaría al propio teléfono. La resolución mDNS en Android/iOS y routers todavía no está validada. El identificador admite entre 1 y 128 caracteres ASCII: letra o número inicial, seguidos de letras, números, guion o guion bajo. No es una credencial. El fragmento no se incluye en la petición HTTP que obtiene la web. `app.js` lo lee al cargar o al cambiar el hash, lo guarda en `sessionStorage` de esa pestaña y lo retira de la barra de direcciones sin recargar. Las peticiones a la API lo envían como `Authorization: Bearer ...` para seleccionar el ámbito. Al cambiar de enlace se cancelan las peticiones del cuadro anterior y se limpia su estado antes de consultar el nuevo. Un identificador nuevo crea un cuadro vacío; el mismo recupera los registros existentes. Una entrada mal formada se rechaza sin activar la demo.

La copia local apunta inicialmente a `http://127.0.0.1:8000`, de modo que el enlace de ejemplo funciona directamente cuando Compose está activo. Antes de publicar, configura la URL HTTPS pública de la API en `meta[name="sonoro-api-base"]`. Esa URL queda pública y no contiene credenciales.

Si el fragmento no trae identificador, la interfaz permanece bloqueada hasta abrir un enlace o elegir explícitamente «Probar demostración». La URL base de API es configuración del sitio, no del usuario: no hay popup ni conexión manual en la interfaz.

### Prueba local de un enlace

Todos los comandos parten de la raíz del repositorio. No se necesita Firebase. Para aislar esta prueba, usa una configuración local sin URL de Firebase y SQLite temporal.

```bash
source .venv/bin/activate
export STATE_DB="$(mktemp -t cuadro-sonoro-link)"
LOCAL_API_ENV="$(mktemp -t cuadro-sonoro-env)"
cat > "$LOCAL_API_ENV" <<EOF
STATE_DB=$STATE_DB
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
EOF
env -u FIREBASE_DATABASE_URL -u FIREBASE_STORAGE_BUCKET -u FIREBASE_SERVICE_ACCOUNT_JSON -u GOOGLE_APPLICATION_CREDENTIALS python -m uvicorn backend.main:app --env-file "$LOCAL_API_ENV" --host 127.0.0.1 --port 8000 --workers 1
```

En otra terminal, también desde la raíz:

```bash
python3 -m http.server 5173 --bind 127.0.0.1 --directory web
```

Abre el enlace directamente; la URL base local ya apunta a la API:

```text
http://127.0.0.1:5173/#token=mi-cuadro-prueba
```

Resultado esperado: la página elimina el fragmento sin recargarse, crea y muestra tres huecos vacíos, y mantiene el acceso al recargar esa pestaña. El mismo enlace recupera el registro. Para comprobar aislamiento, abre `http://127.0.0.1:5173/#token=otro-cuadro-prueba`; su estado debe ser independiente. Un identificador con `!` o más de 128 caracteres se rechaza. La demo continúa siendo una elección explícita y separada. Detén los servidores con `Ctrl+C`. Sin Firebase Storage, configurar una canción devuelve 503.

La web servida por el ESP32 conservará en `meta[name="sonoro-api-base"]` la URL HTTPS pública de la API; no se introduce esa dirección en el móvil. El identificador se distribuye por QR/NFC en el fragmento de la URL local. La API en Render tendrá que permitir por CORS el origen local. El ESP32, el hostname mDNS y la generación/programación de QR/NFC siguen pendientes.

Para desarrollo local, arranca API y web según [backend/README.md](../backend/README.md) y abre `http://127.0.0.1:5173/#token=mi-cuadro-prueba`. Cualquier persona puede cambiar los datos de un identificador conocido; no uses datos privados. La cuenta de servicio nunca se introduce en la web. Las importaciones siguen necesitando Firebase Storage.

Check desde la raíz, con Node instalado:

```bash
node --check web/app.js
```

Al modificar la UI comprobar móvil, teclado abierto, modales, estados vacíos/error/carga, lectura de progreso y escucha local. El HTML de las búsquedas y los cambios de hueco se actualizan sin recargar la página. No añadir comandos al ESP32.

En el producto, empaquetar los archivos de `web/` en el firmware y servirlos desde el ESP32 en la Wi-Fi doméstica. Esta integración aún no existe y depende de elegir placa y entorno de firmware; documentar instalación, actualización y comprobaciones cuando se implemente. El móvil debe conservar salida a internet para acceder a Render. No se necesita publicar los archivos web en el servidor externo de Carlos.
