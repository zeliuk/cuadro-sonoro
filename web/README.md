# Web

Desde la raíz del repo, con Python 3:

```bash
python3 -m http.server 5173 --bind 127.0.0.1 --directory web
```

Abre [la interfaz](http://127.0.0.1:5173). `Ctrl+C` detiene el servidor y sus logs se ven en esa terminal. No hay instalación npm, bundler ni variables secretas de frontend. No abrir `index.html` como archivo local: usar HTTP para los módulos.

`index.html`, `style.css` y `app.js` conservan el diseño aprobado. Hoy JS está concentrado en un archivo: modularizar sin rediseñar, separando componentes, estado y servicios. La demo usa localStorage, no Firebase; se activa explícitamente desde el engranaje.

## Acceso mediante enlace de cuadro

El formato es `https://dominio-del-cuadro/#token=<token_urlsafe>`, por ejemplo `https://cuadro.example/#token=TOKEN_FICTICIO_NO_VALIDO`. El ejemplo es deliberadamente inválido. El fragmento no se incluye en la petición HTTP que obtiene la web. `app.js` lo lee al cargar o al cambiar el hash, lo guarda en `sessionStorage` de esa pestaña y lo retira de la barra de direcciones sin recargar. Las peticiones a la API lo envían como `Authorization: Bearer ...`. Al cambiar de enlace se cancelan las peticiones del cuadro anterior y se limpia su estado antes de consultar el nuevo. Una respuesta 401 invalida el acceso de esa pestaña, vacía sus datos y muestra un error; no activa la demo.

Al servir la web en producción, configura la URL pública de la API en `web/index.html`, en `meta[name="sonoro-api-base"]`. Ejemplo ficticio: `<meta name="sonoro-api-base" content="https://api.example.invalid">`. No pongas tokens en esa etiqueta. La URL queda pública; los tokens solo viajan en el fragmento de acceso y en la cabecera Bearer de las llamadas a la API.

Si el fragmento no trae token pero ya hay una URL local guardada, se puede guardar esa URL desde ajustes y abrir luego el enlace del cuadro. El acceso manual con token sigue disponible para desarrollo. Si no hay token, la interfaz permanece bloqueada hasta abrir un enlace, configurar manualmente un token de desarrollo o elegir la demostración.

### Prueba local de un enlace

Todos los comandos parten de la raíz del repositorio. No se necesita Firebase. La API usa el `LOCAL_FRAME_TOKEN` de `backend/.env` y SQLite local.

```bash
python3 scripts/setup_local.py
source .venv/bin/activate
export STATE_DB="$(mktemp -t cuadro-sonoro-link)"
env -u FIREBASE_DATABASE_URL -u FIREBASE_STORAGE_BUCKET -u FIREBASE_SERVICE_ACCOUNT_JSON -u GOOGLE_APPLICATION_CREDENTIALS python -m uvicorn backend.main:app --env-file backend/.env --host 127.0.0.1 --port 8000 --workers 1
```

En otra terminal, también desde la raíz:

```bash
python3 -m http.server 5173 --bind 127.0.0.1 --directory web
```

Abre `http://127.0.0.1:5173`, entra en ajustes, selecciona «Servicio real» y guarda `http://127.0.0.1:8000` dejando vacío el token. Esto guarda solo la URL local y deja la vista bloqueada. Abre después el enlace en la barra del navegador, sustituyendo el ejemplo por el valor local de `LOCAL_FRAME_TOKEN` que ya tengas guardado en tu entorno privado:

```text
http://127.0.0.1:5173/#token=TOKEN_FICTICIO_NO_VALIDO
```

Resultado esperado: la página elimina el fragmento sin recargarse, muestra los tres huecos del token local y mantiene el acceso al recargar esa pestaña. Para probar el rechazo, abre `http://127.0.0.1:5173/#token=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA`; es un token ficticio de 43 caracteres y no está provisionado. La página debe mostrar el error de acceso, vaciar los huecos y no enseñar la demo. Elige «Demostración» explícitamente en ajustes para comprobar el modo aislado; al volver a abrir el enlace del cuadro, debe reaparecer el estado real y ocultarse la nota de demo. Detén ambos procesos con `Ctrl+C`. El servidor local no tiene Firebase Storage: configurar una canción devolverá 503.

En el hosting publicado, reemplaza el contenido vacío de `meta[name="sonoro-api-base"]` en `web/index.html` por la URL HTTPS de la API. Esta URL es pública y no lleva el token. No necesitas introducir esa dirección en el navegador del familiar. El token se distribuye por el enlace/NFC como `https://dominio/#token=<token_urlsafe>`; generar la imagen QR y programar NFC siguen fuera de esta fase.

Para desarrollo local, arranca la API como indica [su guía](../backend/README.md). En la interfaz, abre ajustes, selecciona «Servicio real», guarda `http://127.0.0.1:8000` sin token para asociar la URL local y luego abre un enlace con el `LOCAL_FRAME_TOKEN` generado en `backend/.env`. El token debe permanecer en la URL solo hasta que la web lo quite; no lo copies en código, issues, historial compartido o capturas. La cuenta de servicio nunca se introduce en la web. Las importaciones siguen necesitando Firebase Storage.

Check desde la raíz, con Node instalado:

```bash
node --check web/app.js
```

Al modificar la UI comprobar móvil, teclado abierto, modales, estados vacíos/error/carga, lectura de progreso y escucha local. El HTML de las búsquedas y los cambios de hueco se actualizan sin recargar la página. No añadir comandos al ESP32.

Para publicar, servir el contenido de `web/` en el hosting de Carlos con HTTPS. No subir el resto del repo ni `.env` al directorio público. Ajustar la URL de API y CORS al configurar el hosting. No hay comando de despliegue del hosting propio porque aún no se ha definido su proveedor/método de subida; documentarlo al configurarlo.
