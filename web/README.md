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
