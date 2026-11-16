> **Herramienta de desarrollo heredada.** Esta guía conserva el servidor local HTTP/Bonjour y su procedimiento como antecedente y utilidad para probar estáticos desde móvil en una LAN. No describe el acceso habitual ni el producto: la web musical se alojará en `https://sonoro.zeliuk.xyz`, no en el ESP32, y el QR/NFC de producción usará ese dominio. La compatibilidad del script con la nueva configuración no implica que el origen público o CORS estén validados. El portal local del ESP32 para Wi-Fi será independiente.

# Prueba frontend local contra Render

La prueba de integración usa estáticos locales y la API remota indicada en `web/index.html`; no hace falta levantar Python/FastAPI en el ordenador. Ejecuta desde la raíz:

```bash
python3 -m http.server 5173 --bind 127.0.0.1 --directory web
```

Abre `http://127.0.0.1:5173/#token=cuadro-prueba-local`. Con el valor versionado, DevTools → Network debe mostrar API en `http://127.0.0.1:8000`; esa dirección solo funciona en el mismo ordenador. Para probar desde el móvil, configura el HTML para apuntar a una API accesible por LAN (por ejemplo, una Raspberry Pi) y ajusta CORS. La descarga RapidAPI siempre se invoca desde el backend; para usar un backend remoto, apunta allí la copia local de la web y revisa [PRUEBA_RAPIDAPI.md](PRUEBA_RAPIDAPI.md). Se conserva también el servidor Bonjour/macOS descrito más abajo para las pruebas de acceso desde móviles.

# Prueba web local desde un móvil

Para probar con un backend remoto, sirve `web/` estática y configura su URL en el meta antes de abrirla. La receta Bonjour/macOS de este documento es una prueba de acceso a estáticos desde móvil; no representa por sí sola hardware.

## Requisitos y preparación inicial

- macOS con Python 3 y Bonjour `dns-sd` (incluido en macOS).
- Mac y teléfono conectados a la misma red no invitada; el router no debe aislar clientes y debe permitir mDNS/multicast.
- Para usar puerto 80, macOS debe permitir al proceso actual abrirlo. El script no usa `sudo` ni modifica configuraciones globales. Si el puerto está ocupado o no hay permiso, muestra un diagnóstico y se puede probar con puerto 8080.
- El backend permite los orígenes exactos `localhost:5173` y `127.0.0.1:5173`. El servidor HTTP estático no carga `.env` ni hace proxy.

Instala la dependencia QR una sola vez, desde la raíz del repositorio:

```bash
python3 -m venv .venv-qr
.venv-qr/bin/python -m pip install 'qrcode[pil]'
```

`.venv-qr` y los QR generados están ignorados por Git.

## Arrancar QR, servidor y Bonjour con un comando

En una terminal, desde la raíz:

```bash
python3 scripts/serve_local_preview.py
```

El comando invoca el generador con `--local` y crea el QR de desarrollo `artifacts/local-preview/cuadro-sonoro-dev001.png`; después detecta la interfaz de la ruta por defecto, obtiene su IPv4 LAN, sirve únicamente `web/` por HTTP en `0.0.0.0:80` y ejecuta `dns-sd -P` para publicar el nombre local y el servicio HTTP. Servidor y anuncio permanecen ligados a esa terminal; sus logs salen ahí. `Ctrl+C` termina solamente esos dos procesos hijos iniciados por el script.

El enlace de ejemplo es:

```text
http://cuadro-sonoro-dev001.local/#token=cuadro-prueba
```

Puedes pasar un sufijo e identificador propios al mismo comando; la ruta del QR usa el sufijo automáticamente:

```bash
python3 scripts/serve_local_preview.py --suffix dev002 --token otro-cuadro-prueba
```

El sufijo admite minúsculas ASCII, números y guiones como etiqueta DNS, de 1 a 49 caracteres, sin guion inicial/final. El identificador admite 1–128 caracteres ASCII válidos. Para recuperar selecciones de un cuadro existente, indica su ID localmente; el lanzador no imprime el enlace para un ID distinto del ejemplo ficticio:

```bash
python3 scripts/serve_local_preview.py --token '<ID_DEL_CUADRO>'
```

También se puede indicar el nombre del PNG local con `--qr-output artifacts/local-preview/mi-qr.png`. No publiques QR ni enlaces que contengan un ID real. Para generar el QR público, usa `scripts/generate_public_qr.py`; las instrucciones están en [web/README.md](../web/README.md).

Para elegir otra interfaz (por ejemplo Wi-Fi `en0`):

```bash
python3 scripts/serve_local_preview.py --interface en0
```

O fija directamente una dirección LAN:

```bash
python3 scripts/serve_local_preview.py --ip 192.168.1.23
```

Sustituye la IP por la de tu Mac. Si cambia, reinicia el script; el sufijo y el enlace permanecen iguales. También puedes cambiar el sufijo de forma estable para cada equipo con `--suffix dev002`.

### Puerto alternativo para diagnóstico

Si 80 no está disponible:

```bash
python3 scripts/serve_local_preview.py --port 8080
```

El enlace pasa a `http://cuadro-sonoro-dev001.local:8080/#token=cuadro-prueba`; CORS exige permitir ese origen de puerto explícitamente con `ALLOWED_ORIGINS`. Para probar por IP, el origen incluye también el puerto, por ejemplo `http://192.168.1.23:8080`. No se puede usar la regex de hostname para una URL por IP.

## Abrir y verificar desde el móvil

1. Arranca también la API local si vas a probar el flujo real desde el Mac. La demo no necesita backend.
2. Arranca el script y confirma que informa servidor en el puerto 80 y anuncio Bonjour. No copies enlaces ni tokens reales a chats o capturas.
3. Escanea el QR generado con el móvil conectado a la misma Wi-Fi. Resultado esperado: carga la interfaz Sonoro; la aplicación lee el identificador del fragmento, lo guarda en `sessionStorage` y limpia el fragmento de la barra sin recargar. Sin una API LAN configurada, el móvil no podrá consultar el estado real; usa «Probar demostración» para verificar la interfaz.
4. Para consultar selecciones o importar desde la API local, abre el sitio en el mismo Mac (`http://127.0.0.1:5173`) y levanta Docker Compose. El QR Bonjour no cambia el destino `127.0.0.1` del API.
5. El terminal local muestra solicitudes `GET` de archivos web; las llamadas de API aparecen en los logs de Compose.

### Diagnóstico separado por IP

Si Bonjour no resuelve desde el móvil, el script imprime una URL de diagnóstico usando la IP detectada. También se puede ver la IP Wi-Fi en Ajustes de macOS > Red. Abrir, por ejemplo, `http://192.168.1.23/#token=cuadro-prueba`. Esto solo verifica que el móvil carga la página; la URL loopback de API sigue apuntando al móvil. No uses `/etc/hosts`: solo cambiaría la resolución en el Mac, no en el móvil.

Si el hostname no funciona, comprobar en orden: misma Wi-Fi (no red de invitados), aislamiento de clientes desactivado, multicast/mDNS permitido, anuncio aún activo, IP actual y firewall del Mac. Reiniciar el script vuelve a anunciar el mismo nombre con la IP vigente.

## Parada y limpieza

Pulsa `Ctrl+C` en la terminal que ejecuta el script. El proceso sale después de terminar HTTP y Bonjour. No hay daemon, cambio del nombre global del Mac ni archivo de hosts. Los QR, la virtualenv QR y artefactos locales quedan fuera de Git.

## Configuración CORS

La API permite orígenes exactos mediante `ALLOWED_ORIGINS` y, opcionalmente, una regex mediante `ALLOWED_ORIGIN_REGEX`. El patrón acordado cubre solo HTTP estándar y hosts que terminan exactamente en `.local`. `Authorization` y `Content-Type` están permitidos para el uso actual de API. El token está en el fragmento y no forma parte del origen ni se envía en el `GET` de la página. CORS no autentica ni vincula hostname y cuadro.

La configuración que se usaba en Render queda aquí solo como referencia histórica:

```dotenv
ALLOWED_ORIGIN_REGEX=^http://cuadro-sonoro-[a-z0-9-]+\.local$
```

Un futuro backend LAN deberá permitir el origen desde el que el ESP32 sirva la web. Guía CORS: [CONFIGURACION.md](CONFIGURACION.md).
