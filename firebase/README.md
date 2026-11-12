# Lectura pública por URL conocida

## Decisión de acceso

Por decisión expresa de Carlos, la configuración musical publicada y los medios se pueden leer sin sesión desde Firebase si se conoce la URL. El identificador del cuadro no es una credencial: la web lo entrega como `#token=<identificador>` y la API lo recibe en Bearer únicamente para derivar `frames/{sha256}` y `private/frames/{sha256}/...`. API y cliente de dispositivo usan la misma función SHA-256 sobre UTF-8. No hay lista de identificadores ni Firebase Auth; la API no concede identidad, sino que agrupa las operaciones del ID presentado.

Las reglas de RTDB dejan leer únicamente `frames/{sha256}/slots`. El acceso a `/frames.json`, a la raíz, a `jobs` y a escrituras queda denegado. Las reglas de Storage permiten obtener un objeto individual bajo `private/frames/{sha256}/` por una URL estable, sin sesión; no permiten listar ni escribir. No hay Firebase Auth, contraseña de dispositivo ni sesión temporal que renovar. El hash separa registros, no autoriza: quien conozca el enlace puede derivar la ruta de configuración, ver sus claves de medios y descargar esos objetos. Esta exposición de los datos publicados está aceptada. La API mantiene su Bearer para modificar configuración y crear importaciones; Admin SDK y credenciales administrativas se quedan en backend/herramientas privadas.

## Emuladores y prueba reproducible

Ejecuta desde la raíz del repositorio. Requisitos locales: Node/npm, Java 17 para la versión de Firebase CLI fijada en el comando y `.venv` con las dependencias del proyecto. La prueba no necesita cuenta de nube, credenciales, API, Render ni facturación. `npx` descarga la CLI y los emuladores la primera vez.

```bash
source .venv/bin/activate
npx --yes firebase-tools@14.22.0 emulators:exec --only database,storage --project demo-sonoro-device --log-verbosity=QUIET 'source .venv/bin/activate && python scripts/test_device_access.py'
```

Resultado esperado: `PASS` confirma lectura de configuración y medios sin sesión, separación entre dos cuadros, denegación del listado general, tareas y escrituras, y descarga completa desde el cliente de ordenador. El arnés exige que la API local no esté escuchando en `127.0.0.1:8000`; toda lectura sale directamente a los emuladores. Los datos de prueba son aleatorios y temporales. Los emuladores se detienen al terminar.

## Conexión pública para el dispositivo

Desde la raíz, copia la plantilla pública y completa el URL exacto de RTDB y el nombre de bucket que muestra el proyecto Firebase. Esos dos valores identifican endpoints públicos; no son credenciales. La copia local está ignorada por Git.

```bash
cp firebase/device-config.example.json firebase/device-config.json
```

Luego ejecuta el cliente para el hueco 0:

```bash
source .venv/bin/activate
python scripts/device_client.py read --config firebase/device-config.json --slot 0 --out /tmp/cuadro-pista.mp3
```

El cliente solicita de forma oculta el identificador fijo, calcula su SHA-256, hace GET a RTDB y descarga `audio_key` e `image_key` directamente de Storage. No envía el identificador a Firebase como credencial y no llama a la API. La salida esperada muestra el título y bytes descargados. El archivo de imagen se guarda junto al audio con sufijo `.cover`.

## URLs directas de ejemplo

Las URL siguientes son ficticias. El primer GET no lleva autenticación y devuelve solo la configuración publicada de un cuadro:

```bash
curl --fail-with-body 'https://example-sonoro-default-rtdb.europe-west1.firebasedatabase.app/frames/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa/slots.json'
```

Si un hueco devuelve `audio_key: "private/frames/<sha256>/<job>/audio.mp3"`, la URL de descarga tiene esta forma; se sustituye el bucket y el nombre de objeto por los valores leídos de RTDB:

```bash
curl --fail-with-body --location 'https://firebasestorage.googleapis.com/v0/b/example-sonoro.firebasestorage.app/o/private%2Fframes%2Faaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa%2Fjob-ficticio%2Faudio.mp3?alt=media' --output /tmp/cuadro-pista.mp3
```

No añadir token Firebase, cookie, firma ni query de sesión. Cualquier persona que conozca esa URL puede obtener el archivo; los enlaces no caducan a los 30 minutos. No publicar URLs reales del cuadro en capturas o informes públicos si no se quiere compartir su música.

La URL de `/frames.json` y las rutas `jobs` deben responder 401/403. PUT/POST/DELETE públicos de RTDB y Storage también deben responder 401/403. Las escrituras se realizan mediante la API, que separa cada cambio por el identificador presentado; no hay comprobación de usuario ni alta.

## Firebase real: estado de validación

El proyecto tiene URL RTDB y bucket configurados localmente. Se verificaron el acceso administrativo del backend a RTDB/Storage, lectura pública por las reglas aplicadas manualmente, rechazo de listados y escrituras, y la importación real de audio e imagen descrita en [VALIDACION.md](../docs/VALIDACION.md). El lector de dispositivo sigue siendo un script de ordenador; el firmware no existe.

La CLI no pudo publicar las reglas por problemas de OAuth/IAM. El comando que se intentó desde la raíz fue:

```bash
npx --yes firebase-tools@14.22.0 deploy --only database,storage --project cuadro-sonoro --non-interactive
```

No se desplegó nada por CLI ni se modificaron otras reglas. Para futuros cambios con CLI habrá que renovar su sesión autorizada o dar a la identidad de despliegue los permisos necesarios; el resultado funcional de las reglas procede de la aplicación manual. Posteriormente se validó una importación real y su reproducción en navegador; ver [VALIDACION.md](../docs/VALIDACION.md).

Las credenciales de Admin SDK solo se configuran en `backend/.env` o en el entorno privado de backend. Nunca se copian al archivo público de conexión ni al cliente ESP32. Las referencias oficiales sobre lectura sin sesión y reglas `get/list` están en [VALIDACION.md](../docs/VALIDACION.md).
