# Instrucciones para trabajar en cuadro-sonoro

## Lectura inicial y referencias

Lee este archivo, `docs/PRIMER_PASO_CODEX.md`, `docs/DEFINICION.md`, `docs/ESTADO.md`, README y el plan. Consulta después arquitectura, configuración y la guía del componente afectado. La definición contiene el producto acordado; el estado y el código describen qué existe hoy. Una diferencia entre ambos es trabajo pendiente, no permiso para cambiar el producto. Las instrucciones actuales del propietario prevalecen; registra las decisiones nuevas.

## Alcance que se conserva

- Repo `cuadro-sonoro`; Sonoro es nombre provisional de interfaz. Documentación y UI en español.
- HTML/CSS/JavaScript organizado en módulos, sin framework y con prioridad móvil. Conservar el diseño aprobado de `web/`; separar módulos por responsabilidad sin rediseñar.
- Web en el servidor de Carlos; Python/FastAPI, yt-dlp, FFmpeg y procesamiento de imágenes en Render/Docker; RTDB y Storage en Firebase. No Firebase Hosting.
- Token por cuadro preparado por el desarrollador, sin registro ni gestión de credenciales por el familiar. No confundirlo con una credencial administrativa de Firebase.
- Tres selecciones, tres pulsadores iluminados y rueda física. La web configura y permite escuchar localmente; no envía órdenes de reproducción ni volumen al ESP32.
- Sin microSD ni canciones permanentes en el dispositivo. No autoplay al arrancar; una canción termina y se detiene.
- Imagen decorativa optimizada desde la web; Wi-Fi mediante portal local y QR. Hardware y firmware van después de validar la importación real.
- Una importación por cuadro; conservar selección anterior ante fallos. Cambiar configuración no interrumpe la reproducción activa.
- Modo demo identificado, separado y sin uso de servicios reales.

## Cómo avanzar

Antes de editar, revisa `git status --short` y los cambios existentes. Trabaja por fases pequeñas, preserva trabajo ajeno y resuelve decisiones rutinarias dentro de lo autorizado. No borres, recrees ni reescribas un repositorio remoto por seguir una receta de inicio. No introduzcas un segundo framework, base de datos, autenticación para el destinatario o servicio sin justificarlo frente al alcance.

El backend deriva ámbitos por cuadro a partir del identificador Bearer; la web acepta el valor desde el fragmento y lo mantiene en la pestaña. Por decisión expresa de Carlos, Firebase deja leer sin sesión la configuración/medios publicados por URL conocida, con listados, tareas y escrituras cerrados. La API mantiene `FRAME_TOKEN_HASHES` para cambios e importaciones. Lee `docs/ESTADO.md` para los límites restantes: validar reglas/importación en Firebase real, preparar QR/NFC, firmware, tareas, limpieza y Radio Browser. No basta con renombrar variables o actualizar un README. No prometer continuidad de tareas en Render Free porque exista un hilo de fondo. No hacer que el ESP32 dependa de un Render dormido para cada reproducción.

## Documentación obligatoria

Cada componente tendrá instrucciones desde cero: requisitos/versiones, carpeta de ejecución, variables de ejemplo, instalación, arranque, URL, verificación, logs, parada y despliegue. Actualiza documentación y código en el mismo cambio. Para cada endpoint documenta método/ruta, acceso, parámetros, cuerpo, ejemplos `curl`, respuesta y errores; añade seguimiento/reintentos/cancelación si corresponde. Mantén `docs/API.md` alineado con OpenAPI y actualiza `docs/PRUEBA_API.md`.

No presentar como verificados comandos no ejecutados ni como implementadas rutas o funciones solo previstas. Mantener README breve; detalles en las guías. Los comentarios explican motivos y límites, no narran cada línea.

Las instrucciones del proyecto ChatGPT también son parte del repositorio: `docs/INSTRUCCIONES_CHATGPT.md`. Si cambia una decisión de producto, alcance, stack o forma de trabajo, actualiza ese archivo junto con definición/estado y avisa al cerrar la tarea de que hay que copiarlo de nuevo a ChatGPT. Esa copia y la renovación de adjuntos son manuales; no afirmes sincronización automática.

## Secretos y datos

Versionar plantillas vacías, nunca `.env`, cuentas de servicio, tokens reales, cookies, audios privados o bases de ejecución. Admin SDK solo en el servidor, nunca en web o firmware. Un `.env` no oculta valores enviados al navegador. No imprimir secretos ni identificadores/enlaces reales de cuadros al verificar una configuración. No abrir reglas para superar una prueba. No borrar datos reales como limpieza rutinaria de tests. La política de eliminación de medios del producto debe implementarse de forma explícita y segura.

Usa pruebas aisladas sin entorno de nube heredado. No activar facturación, publicar recursos o desplegar cambios fuera del alcance autorizado. No pedir de nuevo permisos ya concedidos. Si falta una decisión material, prepara el resultado revisable y explica qué falta.

## Comprobaciones

Desde la raíz, con el entorno virtual activado:

```bash
env -u FIREBASE_DATABASE_URL -u FIREBASE_STORAGE_BUCKET -u FIREBASE_SERVICE_ACCOUNT_JSON -u GOOGLE_APPLICATION_CREDENTIALS python -m pytest backend/tests scripts/tests -q
python -m compileall -q backend scripts
node --check web/app.js
```

Después de preparar el commit:

```bash
python3 scripts/check_public_repo.py --staged
```

El control de secretos es limitado y no revisa historial. Si cambias JS a varios módulos, amplía el check. Verifica móvil si hay cambios visuales y Docker si cambias su configuración; si no puedes ejecutarlo, registra el límite. Añade pruebas de comportamientos importantes, no tests que repitan la implementación.

Al cerrar una fase informa qué cambió, qué se probó, qué sigue pendiente y el siguiente paso concreto. Actualiza `docs/ESTADO.md` y `docs/VALIDACION.md`. Distingue mocks, servicios reales y hardware real.
