# Despliegue y publicación

Esta guía documenta destinos y condiciones, no afirma que se haya desplegado nada en esta fase. La URL pública elegida para la web es `https://sonoro.zeliuk.xyz`; Carlos comunica que el backend funciona en Render con RapidAPI. La publicación de la web, HTTPS, CORS desde el dominio y el recorrido integrado todavía requieren comprobación con evidencias.

## Publicar la web estática

El contenido que se publica es el directorio `web/` (HTML, CSS, JavaScript y recursos estáticos). Debe servirse desde el hosting HTTPS de Carlos en el origen exacto `https://sonoro.zeliuk.xyz`, sin barra final. No se conoce el proveedor, panel, método de acceso, credenciales ni ruta del servidor; por ello esta guía no inventa comandos de subida. La actualización del contenido web no requiere actualizar los dispositivos.

El enlace habitual contiene el identificador ficticio o asignado del cuadro en el fragmento, por ejemplo:

```text
https://sonoro.zeliuk.xyz/#token=cuadro-demo
```

La aplicación lee `#token=...`, lo guarda en `sessionStorage` de la pestaña y limpia el fragmento de la barra. `scripts/generate_public_qr.py` genera el QR para este dominio y añade el ID al fragmento. Los QR con ID asignados se guardan como archivos locales privados ignorados por Git. El ESP32 no aloja la web musical. Su portal local para configurar/restablecer Wi-Fi es un flujo distinto; la contraseña queda en el dispositivo.

Antes de publicar, revisar que `web/index.html` use la API prevista. En el código actual `meta[name="sonoro-api-base"]` apunta a `https://cuadro-sonoro.onrender.com`. El móvil necesita Internet para cargar el hosting y comunicarse con Render/Firebase, pero no estar conectado a la Wi-Fi del cuadro.

## Conexión con Render y CORS

La API FastAPI vive en `https://cuadro-sonoro.onrender.com`. Para que un navegador servido desde la web pública pueda leer sus respuestas, permitir el origen exacto con la variable existente `ALLOWED_ORIGINS`:

```dotenv
ALLOWED_ORIGINS=https://sonoro.zeliuk.xyz
```

Si se conservan también los orígenes locales de desarrollo, deben añadirse a la lista separada por comas. `ALLOWED_ORIGIN_REGEX` es una opción existente para necesidades de desarrollo, pero no se necesita para el origen estable de producción. CORS no autentica al usuario ni al cuadro. Esta es la configuración requerida; no confirma que el valor esté aplicado en Render. Los secretos `RAPIDAPI_KEY`, credenciales Firebase y `RAPIDAPI_USERNAME` se configuran solo en el entorno backend correspondiente.

Firebase Realtime Database conserva configuración/selecciones/estados y Storage conserva audio e imágenes. El ESP32 consultará su ámbito y reproducirá MP3 desde Storage o radio desde sus streams. Hosting y API no participan en el recorrido normal del audio ya preparado; no se requiere servidor doméstico ni Raspberry Pi por cuadro.

## Verificación pendiente de publicación

Cuando el propietario publique el contenido y confirme la configuración CORS, comprobar desde un navegador real:

1. HTTPS válido y respuesta de los recursos estáticos de `https://sonoro.zeliuk.xyz`.
2. Un enlace ficticio con `#token=cuadro-demo` carga la interfaz, conserva el valor en `sessionStorage` y retira el fragmento visible.
3. Las peticiones al backend salen a `https://cuadro-sonoro.onrender.com` y el preflight/respuesta CORS admite exactamente el origen público.
4. Una configuración publicada en Firebase no se interpreta como confirmación de que el ESP32 la haya recibido o aplicado.
5. «Escuchar aquí» afecta solo al navegador. Los botones/rueda del dispositivo gobernarán reproducción/volumen cuando firmware exista.

No se ha realizado esta verificación desde el dominio ni en hardware en esta fase. No hacer importaciones reales como parte de una comprobación de publicación sin autorización y presupuesto de cuota.

## Backend y Firebase

Para API local/Docker, instalación, variables, arranque, logs y parada, consultar [backend/README.md](../backend/README.md) y [CONFIGURACION.md](CONFIGURACION.md). RapidAPI y los límites de prueba están en [PRUEBA_RAPIDAPI.md](PRUEBA_RAPIDAPI.md). La configuración Firebase está en [firebase/README.md](../firebase/README.md). La publicación efectiva de variables en Render no se deduce del `.env` local.

## Hardware

Firmware, placa, pantalla, amplificador, alimentación, pines y distribución física siguen pendientes. La propuesta ESP32-S3 con PSRAM es orientativa, no una selección final. La guía del firmware se actualizará cuando esa fase tenga hardware y entorno elegidos. El portal local de Wi-Fi del ESP32 se valida separado de la web musical pública.
