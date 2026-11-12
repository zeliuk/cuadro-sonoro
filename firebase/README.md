# Lectura del ESP32 desde Firebase

El dispositivo usa directamente Realtime Database y Storage; Render no participa durante reproducción. El token fijo ya asignado al cuadro se reutiliza como Bearer de la API y como contraseña de una cuenta técnica Firebase Auth creada por el desarrollador. No hay registro para familiares ni una credencial administrativa dentro del dispositivo. Firebase Auth entrega un ID token temporal y un refresh token: esos valores de sesión cambian automáticamente, pero el token configurado en el cuadro permanece fijo. El firmware guardará el estado de sesión de forma privada y podrá renovar/restablecer la sesión sin contactar Render.

La identidad Auth tiene UID `frame-reader-{sha256(token)}`. Las reglas comparan ese UID con la ruta y solo permiten leer `frames/{sha256}/slots` y objetos `private/frames/{sha256}/...`; toda escritura y el resto del árbol quedan denegados. El hash/ruta no es una autorización sin una sesión autenticada. No se usan URLs firmadas para el ESP32 (las actuales siguen para escucha web).

## Emuladores locales y prueba reproducible

Desde la raíz del repositorio se necesitan Node/npm, Java 17 o superior para la versión fijada de Firebase CLI y el entorno del proyecto `.venv` ya instalado. No se necesita proyecto de nube, cuenta de servicio, facturación ni Render. `npx` descarga `firebase-tools@14.22.0` y los emuladores la primera vez.

```bash
source .venv/bin/activate
npx --yes firebase-tools@14.22.0 emulators:exec --only auth,database,storage --project demo-sonoro-device --log-verbosity=QUIET 'source .venv/bin/activate && python scripts/test_device_access.py'
```

Resultado esperado: salida `PASS` que confirma lectura de RTDB y Storage propios, rechazo de otro cuadro, sesión ausente y escrituras, y renovación Firebase forzada manteniendo el Bearer fijo. La prueba usa datos y tokens aleatorios temporales, emuladores aislados y no invoca la API/Render. Los emuladores se detienen al terminar. La expiración se simula adelantando el vencimiento local y ejercitando el endpoint de refresh; no espera una hora real.

## Aprovisionar un dispositivo para un proyecto real

Esto aún requiere un proyecto Firebase dedicado ya configurado con Realtime Database, Storage y Authentication (proveedor Email/Password habilitado), datos y medios importados bajo las rutas de cuadro, reglas revisadas y una cuenta de servicio privada de desarrollador. Storage puede requerir Blaze; este procedimiento no habilita facturación ni despliega reglas. No usar recursos reales hasta decidir proyecto, región y facturación.

Desde la raíz, activar el entorno virtual y editar localmente `backend/.env` (ignorado por Git). `FRAME_TOKEN_HASHES` debe contener el SHA-256 del token que ya usa la API, y las variables Firebase deben apuntar al mismo proyecto; `GOOGLE_APPLICATION_CREDENTIALS` apunta al archivo privado de Admin SDK. `FIREBASE_WEB_API_KEY` es la clave pública del proyecto usada por el cliente Auth REST, no un secreto administrativo. Nunca imprimir el `.env` ni pasar el token por argumento:

```bash
source .venv/bin/activate
python scripts/provision_device.py --env-file backend/.env --output device-private/cuadro-config.json
```

El script solicita el token ocultando la entrada, verifica su hash contra `FRAME_TOKEN_HASHES`, crea o actualiza la cuenta técnica con Admin SDK y guarda configuración no secreta en `device-private/cuadro-config.json` (carpeta ignorada). No copia el token a ese archivo. Admin SDK se usa solo durante aprovisionamiento en una máquina del desarrollador; no va al ESP32. El token fijo deberá cargarse en el dispositivo por el proceso físico de preparación, fuera de Git y sin mostrarlo en logs.

## Cliente de prueba desde ordenador

El cliente reproduce el flujo esperado del futuro dispositivo, sin llamar a Render. Los archivos de sesión contienen el Bearer y credenciales temporales; guárdalos localmente, no los adjuntes ni versionees. Ejecutar desde la raíz:

```bash
source .venv/bin/activate
python scripts/device_client.py login --config device-private/cuadro-config.json --state device-private/cuadro-session.json
python scripts/device_client.py read --state device-private/cuadro-session.json --slot 0 --out /tmp/cuadro-pista.mp3
```

`login` pide el token fijo de forma oculta. `read` renueva la sesión Firebase si está cerca de caducar, lee `frames/{sha256}/slots` y descarga el `audio_key` y `image_key` indicados por la configuración; `--force-refresh` permite comprobar renovaciones inmediatamente. Salida esperada: metadatos de selección, número de bytes y `session_renewed`, nunca token o URL firmada. El audio de ejemplo se guarda en `/tmp`; el cliente limita permisos locales de los archivos de sesión/salida.

## Límites de validación

Solo el recorrido de emuladores está verificado localmente. No se desplegaron reglas ni se contactó un proyecto Firebase real. Antes del firmware hay que, en un proyecto dedicado y autorizado, validar creación de Auth user, API key, lectura de RTDB/Storage con reglas, refresh real después de caducidad, aislamiento entre dos cuadros y acceso a datos producidos por una importación real. Comprobar aparte políticas de persistencia segura del refresh token del hardware elegido. No basta con una prueba contra URLs sintéticas.

Las referencias oficiales consultadas están enlazadas en [VALIDACION.md](../docs/VALIDACION.md): Firebase Auth REST (sign-in/refresh), autenticación RTDB REST y variables `auth.uid`/`request.auth.uid` en reglas.
