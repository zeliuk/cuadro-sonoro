# Web

Desde la raíz del repo, con Python 3:

```bash
python3 -m http.server 5173 --bind 127.0.0.1 --directory web
```

Abre [la interfaz](http://127.0.0.1:5173). `Ctrl+C` detiene el servidor y sus logs se ven en esa terminal. No hay instalación npm, bundler ni variables secretas de frontend. No abrir `index.html` como archivo local: usar HTTP para los módulos.

`index.html`, `style.css` y `app.js` conservan el diseño aprobado. Hoy JS está concentrado en un archivo: modularizar sin rediseñar, separando componentes, estado y servicios. La demo usa localStorage, no Firebase; si había una configuración antigua, usa «Modo demostración» en el engranaje.

El modo real actual es experimental y pide URL API y el Bearer del cuadro de forma manual. El backend aísla sus datos por hash del token. La incorporación automática del acceso por QR/NFC sigue pendiente; no publicar tokens dentro del código web ni introducir credenciales de Firebase.

Para probar la API local, arrancarla según [su guía](../backend/README.md), usar `http://127.0.0.1:8000` y el token local. La cuenta de servicio nunca se introduce en la web. La prueba de audio actual solo se habilita en modo real tras tener un archivo preparado.

Check desde la raíz, con Node instalado:

```bash
node --check web/app.js
```

Al modificar la UI comprobar móvil, teclado abierto, modales, estados vacíos/error/carga, lectura de progreso y escucha local. El HTML de las búsquedas y los cambios de hueco se actualizan sin recargar la página. No añadir comandos al ESP32.

Para publicar, servir el contenido de `web/` en el hosting de Carlos con HTTPS. No subir el resto del repo ni `.env` al directorio público. Ajustar la URL de API y CORS al configurar el hosting. No hay comando de despliegue del hosting propio porque aún no se ha definido su proveedor/método de subida; documentarlo al configurarlo.
