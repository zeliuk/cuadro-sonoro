# Firmware y primera prueba visual

## Referencia visual de conexiones y montaje

![Vista orientativa del montaje interno y sus conexiones](../docs/imagenes/vista-orientativa-montaje.webp)

La ilustración ayuda a imaginar la disposición general del controlador, pantalla, altavoz, rueda y pulsadores. Es un croquis visual preliminar y no representa el cableado propuesto actual ni instrucciones para energizar componentes. La selección, lista de materiales, esquema propuesto y comprobaciones pendientes están en [Hardware del primer prototipo](../docs/HARDWARE.md); el montaje y su validación física siguen pendientes.

La placa y los componentes del primer prototipo están seleccionados, pero el montaje y el pinout propuesto aún no se han validado físicamente. Hay una primera prueba de escritorio en `firmware/simulator/`, hecha con C++, LVGL 9.2.2 y SDL2. La demo tiene una opción de lectura Firebase descrita abajo, pero no es firmware para ESP32: siguen pendientes el Wi-Fi, el audio real, el portal y la integración con la placa.

## Simulador local en macOS Apple Silicon

### Requisitos

- macOS 13 o posterior en Apple Silicon (M1 o más reciente).
- Xcode Command Line Tools: `xcode-select --install`.
- Homebrew para Apple Silicon en `/opt/homebrew`.
- CMake 3.20 o posterior, compilador C/C++ de Apple y SDL2. LVGL 9.2.2 se descarga automáticamente en la primera configuración de CMake; requiere Internet solo al compilar por primera vez.

### Instalar dependencias

Esta demo está dirigida a Apple Silicon. En Terminal, confirma que la sesión es nativa:

```bash
uname -m
brew --prefix
```

El resultado esperado es `arm64` y `/opt/homebrew`. Si ves `x86_64` y `/usr/local`, abre Terminal con «Abrir usando Rosetta» desactivado o instala Homebrew nativo para Apple Silicon siguiendo [la guía oficial](https://docs.brew.sh/Installation). Desde cualquier carpeta, instala las dependencias con Homebrew nativo:

```bash
/opt/homebrew/bin/brew install cmake sdl2
```

### Compilar

Desde la raíz del repositorio, configura y compila:

```bash
/opt/homebrew/bin/cmake -S firmware/simulator -B firmware/simulator/build -DCMAKE_PREFIX_PATH=/opt/homebrew/opt/sdl2
/opt/homebrew/bin/cmake --build firmware/simulator/build --target cuadro-sonoro --parallel
```

### Abrir y usar

Desde la raíz del repositorio, abre la ventana:

```bash
./firmware/simulator/build/cuadro-sonoro
```

Se abre una ventana SDL de 480 × 480. Al inicio muestra `assets/imagen-decorativa.jpg`. Pulsa y suelta `1` antes de 2 segundos para mostrar `assets/caratula-demo.jpg` (320 × 320) y los metadatos de prueba; pulsa `1` brevemente otra vez para volver al reposo. Mantén `1` durante 2 segundos para el QR local del enlace `https://sonoro.zeliuk.xyz/#token=cuadro-demo`; se oculta a los 20 segundos y regresa a la vista de reposo o canción que estuviera activa. El texto de ejemplo incluye tildes y se ajusta en varias líneas. No se reproduce sonido.

Para salir, cierra la ventana o pulsa `⌘Q`. También puedes detener el proceso desde la Terminal con `Ctrl+C`. Para guardar la salida de diagnóstico al ejecutar:

```bash
./firmware/simulator/build/cuadro-sonoro 2>&1 | tee /tmp/cuadro-sonoro.log
```

El proceso se detiene con `Ctrl+C`; los errores y avisos quedan en `/tmp/cuadro-sonoro.log`.

Para recorrer los estados y tiempos automáticamente (genera capturas BMP de 480 × 480 en `/tmp` y tarda unos 21 s):

```bash
./firmware/simulator/build/cuadro-sonoro --verify-flow /tmp/cuadro-sonoro
```

La salida confirma reposo, inicio/detención simulados, aislamiento del gesto largo y expiración del QR a los 20 segundos. Para convertir la captura de canción a PNG con la herramienta incluida en macOS:

```bash
qlmanage -t -s 480 -o /tmp /tmp/cuadro-sonoro-cancion.bmp
```

### Abrir una canción publicada en Firebase

Además de los recursos locales de prueba, el simulador puede leer los tres huecos publicados directamente desde Firebase RTDB. Para canciones descarga `image_key` desde Storage; para radios obtiene el `favicon` HTTPS guardado en la selección. No llama a Render ni descarga audio. El identificador se solicita de forma oculta; la configuración de conexión contiene únicamente la URL pública de RTDB y el nombre del bucket, no credenciales administrativas. Crea la configuración local una vez desde la raíz del repositorio si aún no existe:

```bash
cp firebase/device-config.example.json firebase/device-config.json
```

Completa `firebase/device-config.json` con la URL RTDB y el bucket públicos del proyecto. Después, desde la raíz, abre la demo conectada:

```bash
python3 firmware/simulator/scripts/launch_firebase.py
```

Requisitos: Python 3 y el simulador compilado en `firmware/simulator/build/cuadro-sonoro`. Pulsa `1`, `2` o `3` para activar la selección del hueco correspondiente; pulsar de nuevo el hueco activo la detiene y pulsar otro cambia a esa selección. Los huecos vacíos no cambian lo que suena. Mantén `1` durante 2 segundos para mostrar el QR del identificador consultado. Las imágenes y el enlace del QR se conservan en archivos temporales mientras la ventana está abierta y se eliminan al cerrarla; el identificador no se pasa como argumento ni se imprime. Las canciones admiten JPEG de 320 × 320 o 480 × 480 (máximo 2 MiB), tanto portadas antiguas como las optimizadas actuales. Los favicons de radios se descargan solo desde HTTPS público, con redirecciones validadas y límite de 2 MiB; las imágenes rasterizadas que no soporte el decodificador o los logos ausentes usan un icono de radio dibujado localmente. No se hacen escrituras en Firebase y no se contacta Render.

Esta es una integración real de lectura para el simulador de escritorio, apoyada en el cliente directo `scripts/device_client.py`; aún no es código de red ejecutable en ESP32. El firmware deberá portar la misma ruta con `esp_http_client`/TLS y el identificador fijo aprovisionado en el dispositivo.

### Arquitectura de esta prueba

`src/sonoro_view.cpp` contiene la vista LVGL independiente de la entrada; `View::showSong()` recibe la carátula, título y artista por separado. `src/main.cpp` inicializa SDL, tamaño/ventana y recursos. `src/key_input.cpp` interpreta la tecla SDL como pulsación corta/larga. Noto Sans (SIL OFL 1.1) con LVGL TinyTTF aporta los caracteres acentuados del texto de prueba. Las imágenes y sus licencias/autoría están en `assets/README.md`. El QR se calcula localmente con la biblioteca C++ MIT Nayuki incluida en `third_party/`; `stb_image` incluido decodifica las imágenes JPEG.

Este límite permite reutilizar la vista LVGL, pero aún habrá que implementar y probar un adaptador de display/input para el controlador de la Waveshare ESP32-S3-Touch-LCD-4B. El montaje, pines y alimentación siguen sin validar; consulta [docs/HARDWARE.md](../docs/HARDWARE.md).

Requisitos acordados: identificador fijo asignado al cuadro; tres botones iluminados; rueda de volumen; pantalla a color; streaming Wi-Fi con búfer, sin microSD; arranque silencioso; una canción termina y se detiene. El ESP32 consulta configuración/medios de Firebase y reproduce MP3 desde Storage o emisoras desde sus streams; no aloja la web musical. El portal local es independiente y configura Wi-Fi sin Internet, Render ni Firebase. En primera instalación, el dispositivo crea un punto de acceso temporal protegido con contraseña propia, muestra un QR de conexión y abre un asistente local; la contraseña doméstica solo se guarda en el ESP32. Distinguir conexión al router de disponibilidad de Internet, sin borrar credenciales por una caída de Internet. Con credenciales guardadas, los fallos temporales no abren solos el asistente.

Pulsaciones cortas controlan los huecos. Mantener botón 1 durante 2 segundos muestra 20 segundos el QR habitual `https://sonoro.zeliuk.xyz/#token=<id-cuadro>` sin afectar a la reproducción; después la pantalla vuelve al estado visual actual. Mantener botones 2 y 3 juntos durante 5 segundos completa una cuenta atrás cancelable soltando cualquiera de ellos; entonces borra únicamente la Wi-Fi y abre el asistente. Se conservan identificador, selecciones, imagen decorativa y volumen. La rueda solo ajusta el volumen y no requiere pulsación. Las acciones largas/combinadas no deben ejecutar acciones cortas; 2+3 tiene prioridad y mantener no repite la acción.

Estos son comportamientos acordados, no implementados en la placa. Los tiempos y dirección local definitiva del portal se validarán con hardware. Los componentes para el primer prototipo y un cableado propuesto están documentados en [docs/HARDWARE.md](../docs/HARDWARE.md), pero montaje, características recibidas, pines, alimentación y funcionamiento todavía requieren comprobación física. LVGL 9.2.2/SDL2 son dependencias de la demo desktop; las librerías del firmware de placa no están elegidas. WiFiManager puede evaluarse como candidato, no es dependencia ni decisión técnica. No hay firmware para cargar ni comandos de compilación/carga de placa.

Cambiar una selección no interrumpe la reproducción activa; la nueva se usa en la siguiente activación. El guardado web no inicia ni detiene audio físico. La web y el cuadro tienen reproducciones y volúmenes independientes. El familiar no instala herramientas ni introduce credenciales técnicas; solo configura su Wi-Fi.

La placa, pantalla, expansor y controles para el primer prototipo ya están seleccionados en la lista de materiales de [docs/HARDWARE.md](../docs/HARDWARE.md). Esta selección no valida las piezas recibidas, el esquema, la alimentación ni el montaje; siguen pendientes la comprobación de banco, la construcción y la validación física. Antes de implementar el firmware, validar también el flujo de la web pública; el reporte de Carlos de backend RapidAPI no valida el dispositivo. Al implementarlo, añadir requisitos/versiones, configuración privada, compilación, USB, monitor serie, prueba de audio/pantalla/botones, recuperación de red y restablecimiento. Nunca incorporar tokens reales, Wi-Fi o credenciales Admin SDK al repositorio.
