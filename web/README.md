# Web

Desde la raíz del repo, con Python 3:

```bash
python3 -m http.server 5173 --bind 127.0.0.1 --directory web
```

Abre [la interfaz](http://127.0.0.1:5173). `Ctrl+C` detiene el servidor y sus logs se ven en esa terminal. No hay instalación npm, bundler ni variables secretas de frontend. No abrir `index.html` como archivo local: usar HTTP para los módulos.

`index.html`, `style.css` y `app.js` conservan el diseño aprobado. Hoy JS está concentrado en un archivo: modularizar sin rediseñar, separando componentes, estado y servicios. La demo usa localStorage, no Firebase; se activa explícitamente con «Probar demostración».

En una selección real, el botón play superpuesto a la portada inicia el audio en este navegador. Cambia a stop mientras suena; al tocarlo se detiene, y al terminar vuelve a play. No hay panel inferior de reproducción ni autoplay. Esto solo controla la escucha local, no el ESP32.

## Acceso mediante enlace de cuadro

El formato es `https://dominio-del-cuadro/#token=<identificador>`, por ejemplo `http://127.0.0.1:5173/#token=mi-cuadro-prueba`. El identificador admite entre 1 y 128 caracteres ASCII: letra o número inicial, seguidos de letras, números, guion o guion bajo. No es una credencial. El fragmento no se incluye en la petición HTTP que obtiene la web. `app.js` lo lee al cargar o al cambiar el hash, lo guarda en `sessionStorage` de esa pestaña y lo retira de la barra de direcciones sin recargar. Las peticiones a la API lo envían como `Authorization: Bearer ...` para seleccionar el ámbito. Al cambiar de enlace se cancelan las peticiones del cuadro anterior y se limpia su estado antes de consultar el nuevo. Un identificador nuevo crea un cuadro vacío; el mismo recupera los registros existentes. Una entrada mal formada se rechaza sin activar la demo.

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

En el hosting publicado, reemplaza el valor local de `meta[name="sonoro-api-base"]` por la URL HTTPS de la API. No necesitas introducir esa dirección en el navegador del familiar. El identificador se distribuye por el enlace/NFC como `https://dominio/#token=<identificador>`; generar la imagen QR y programar NFC siguen fuera de esta fase.

Para desarrollo local, arranca API y web según [backend/README.md](../backend/README.md) y abre `http://127.0.0.1:5173/#token=mi-cuadro-prueba`. Cualquier persona puede cambiar los datos de un identificador conocido; no uses datos privados. La cuenta de servicio nunca se introduce en la web. Las importaciones siguen necesitando Firebase Storage.

Check desde la raíz, con Node instalado:

```bash
node --check web/app.js
```

Al modificar la UI comprobar móvil, teclado abierto, modales, estados vacíos/error/carga, lectura de progreso y escucha local. El HTML de las búsquedas y los cambios de hueco se actualizan sin recargar la página. No añadir comandos al ESP32.

Para publicar, servir el contenido de `web/` en el hosting de Carlos con HTTPS. No subir el resto del repo ni `.env` al directorio público. Ajustar la URL de API y CORS al configurar el hosting. No hay comando de despliegue del hosting propio porque aún no se ha definido su proveedor/método de subida; documentarlo al configurarlo.
