# Prueba web local desde un móvil

Esta prueba sirve únicamente los archivos estáticos de `web/` desde el Mac. El teléfono debe estar en la misma Wi-Fi, con comunicación entre clientes habilitada y salida a internet para llegar directamente a `https://cuadro-sonoro.onrender.com`. No inicia Docker ni la API local. No emula ESP32, botones, pantalla, audio I2S, firmware ni portal Wi-Fi. La demo permanece separada; el enlace real de prueba consulta API/servicios reales si ese cuadro llega a tener datos.

## Requisitos y preparación inicial

- macOS con Python 3 y Bonjour `dns-sd` (incluido en macOS).
- Mac y teléfono conectados a la misma red no invitada; el router no debe aislar clientes y debe permitir mDNS/multicast.
- Para usar puerto 80, macOS debe permitir al proceso actual abrirlo. El script no usa `sudo` ni modifica configuraciones globales. Si el puerto está ocupado o no hay permiso, muestra un diagnóstico y se puede probar con puerto 8080.
- La API desplegada en Render debe tener CORS configurado y reiniciado, ver [CONFIGURACION.md](CONFIGURACION.md). El servidor HTTP no carga `.env` ni hace proxy.

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

El comando genera el QR ficticio `artifacts/local-preview/cuadro-sonoro-dev001.png` y después detecta la interfaz de la ruta por defecto, obtiene su IPv4 LAN, sirve únicamente `web/` por HTTP en `0.0.0.0:80` y ejecuta `dns-sd -P` para publicar el nombre local y el servicio HTTP. Servidor y anuncio permanecen ligados a esa terminal; sus logs salen ahí. `Ctrl+C` termina solamente esos dos procesos hijos iniciados por el script.

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

También se puede indicar el nombre del PNG con `--qr-output artifacts/local-preview/mi-qr.png`. No publiques QR ni enlaces que contengan un ID real.

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

1. En Render, configura `ALLOWED_ORIGIN_REGEX` y reinicia/redeploy la API.
2. Arranca el script y confirma que informa servidor en el puerto 80 y anuncio Bonjour. No copies enlaces ni tokens reales a chats o capturas.
3. Escanea el QR generado con el móvil conectado a la misma Wi-Fi. Resultado esperado: carga la interfaz Sonoro; la aplicación lee el identificador del fragmento, lo guarda en `sessionStorage` y limpia el fragmento de la barra sin recargar. La web consulta Render directamente.
4. Con el QR ficticio sin datos, deben aparecer tres huecos vacíos. Para recuperar selecciones existentes, genera el QR con el ID correspondiente indicado de forma privada en la terminal; la web debe mostrar las selecciones publicadas de ese cuadro. No se crea ni importa contenido como parte de esta prueba.
5. En Render, los registros de acceso de la API pueden confirmar las llamadas. El terminal local muestra solicitudes `GET` de archivos web; no actúa como API ni proxy.

### Diagnóstico separado por IP

Si Bonjour no resuelve desde el móvil, el script imprime una URL de diagnóstico usando la IP detectada. También se puede ver la IP Wi-Fi en Ajustes de macOS > Red. Abrir, por ejemplo, `http://192.168.1.23/#token=cuadro-prueba`. Esta ruta no es el QR hostname y requiere añadir en Render el origen exacto `http://192.168.1.23` a `ALLOWED_ORIGINS`; reemplaza por la IP real. Para puerto alternativo incluye `:8080`. No uses `/etc/hosts`: solo cambiaría la resolución en el Mac, no en el móvil.

Si el hostname no funciona, comprobar en orden: misma Wi-Fi (no red de invitados), aislamiento de clientes desactivado, multicast/mDNS permitido, anuncio aún activo, IP actual y firewall del Mac. Reiniciar el script vuelve a anunciar el mismo nombre con la IP vigente.

## Parada y limpieza

Pulsa `Ctrl+C` en la terminal que ejecuta el script. El proceso sale después de terminar HTTP y Bonjour. No hay daemon, cambio del nombre global del Mac ni archivo de hosts. Los QR, la virtualenv QR y artefactos locales quedan fuera de Git.

## Configuración CORS

La API permite orígenes exactos mediante `ALLOWED_ORIGINS` y, opcionalmente, una regex mediante `ALLOWED_ORIGIN_REGEX`. El patrón acordado cubre solo HTTP estándar y hosts que terminan exactamente en `.local`. `Authorization` y `Content-Type` están permitidos para el uso actual de API. El token está en el fragmento y no forma parte del origen ni se envía en el `GET` de la página. CORS no autentica ni vincula hostname y cuadro.

Añadir en el Environment de Render, sin comillas exteriores:

```dotenv
ALLOWED_ORIGIN_REGEX=^http://cuadro-sonoro-[a-z0-9-]+\.local$
```

Guía completa y CORS por IP/puerto: [CONFIGURACION.md](CONFIGURACION.md).
