# Firmware y simulador

El firmware de placa se desarrolla con ESP-IDF; el simulador conserva SDL2. Las pantallas LVGL, QR, imágenes de diagnóstico y componentes de vista están en `firmware/common/`. El código que lee archivos, Firebase, teclado y ventana vive en `firmware/simulator/`; la inicialización del BSP y el arranque de la placa están en `firmware/esp32/`.

## Versiones fijadas

- ESP-IDF **v5.5.5**, objetivo `esp32s3` (macOS arm64).
- Waveshare BSP `waveshare/esp32_s3_touch_lcd_4b` **2.0.0**.
- LVGL **9.5.0** en simulador y firmware.
- C++17 para las vistas compartidas.
- SDL2 **2.32.10 exacto** para escritorio.
- QR Code generator de Nayuki incluido con licencia MIT; `stb_image` se usa únicamente en el simulador y conserva su licencia upstream.

La placa incorpora ESP32-S3-WROOM-1-N16R8, 16 MB Flash, 8 MB PSRAM OPI, LCD RGB 480 × 480 con ST7701 y táctil GT911. El BSP oficial realiza la inicialización eléctrica y del bus; esta fase no usa el táctil. LVGL y BSP se fijan en el manifiesto de componentes, y ESP-IDF en esta guía. OTA no está configurado. El firmware diagnóstico usa una tabla de particiones de aplicación única.

## Simulador SDL2

Requisitos: CMake 3.20+, Xcode Command Line Tools (macOS), compilador C/C++17 y conexión a Internet la primera vez. CMake descarga SDL2 2.32.10 y LVGL 9.5.0 desde tags fijados; no hace falta instalar SDL2 por separado. En macOS con Homebrew:

```bash
brew install cmake
cmake -S firmware/simulator -B firmware/simulator/build-lvgl95
cmake --build firmware/simulator/build-lvgl95 --target cuadro-sonoro --parallel
firmware/simulator/build-lvgl95/cuadro-sonoro
```

Usa un directorio de compilación nuevo si tienes una caché anterior configurada con otra versión de LVGL o SDL2.

Se abre una ventana 480 × 480. Las teclas `1`–`3` simulan pulsaciones; el modo local mantiene la canción de demostración en el primer hueco. No se conecta a Firebase en ese modo.

Para la lectura Firebase (usa RTDB/Storage reales configurados localmente y no escribe):

```bash
python3 firmware/simulator/scripts/launch_firebase.py
```

El programa solicita el identificador sin mostrarlo. Necesita la configuración pública local `firebase/device-config.json` y conectividad a Firebase. Para detener, cierra la ventana o pulsa Ctrl+C. Logs y errores salen por la terminal. La lectura remota de medios y el SSE son servicios reales, no mocks; se deben usar solo con un identificador elegido por el propietario. No hay variables de secretos para el modo local.

## ESP-IDF en macOS Apple Silicon

### 1. Instalar ESP-IDF

Instala Xcode Command Line Tools y Git: `xcode-select --install`. Descarga ESP-IDF Installation Manager (EIM) desde la [página oficial de Espressif](https://docs.espressif.com/projects/esp-idf/en/v5.5.5/esp32/get-started/macos-setup.html). En el instalador selecciona ESP-IDF **v5.5.5** y la instalación de herramientas para macOS arm64. Mantén la ruta que propone EIM. EIM instala Python, CMake, Ninja y el toolchain Xtensa; no uses herramientas de Arduino para este proyecto.

Abre la terminal ESP-IDF creada por EIM o carga el entorno instalado. Verifica antes de compilar:

```bash
idf.py --version
python3 --version
xtensa-esp32s3-elf-gcc --version
```

La ruta de instalación depende de la elección hecha en EIM. Si usas una terminal normal, activa el `export.sh` de esa instalación, por ejemplo `source ~/esp/esp-idf/export.sh` si EIM instaló ESP-IDF en `~/esp/esp-idf`.

### 2. Configurar VS Code

1. Instala Visual Studio Code para Apple Silicon desde el sitio oficial.
2. En Extensions, instala **ESP-IDF** de Espressif Systems (identificador `espressif.esp-idf-extension`).
3. Ejecuta `ESP-IDF: Configure ESP-IDF extension` desde la paleta de comandos. Si EIM instaló ESP-IDF, elige **Use Existing Setup** y selecciona esa instalación y sus herramientas.
4. Abre la carpeta raíz `cuadro-sonoro`, no solo `firmware/esp32`. La extensión permite invocar Build, Flash y Monitor desde `firmware/esp32`; la terminal ESP-IDF equivalente es la referencia reproducible.

### 3. Compilar

Desde una terminal con ESP-IDF activado:

```bash
cd firmware/esp32
idf.py set-target esp32s3
idf.py reconfigure
idf.py build
```

La primera compilación descarga el BSP y LVGL desde el Component Registry. El BSP oficial se distribuye bajo Apache-2.0; no se ha copiado su código fuente al repositorio. `sdkconfig.defaults` selecciona flash QIO de 16 MB, PSRAM octal de 8 MB a 80 MHz, consola USB CDC, LVGL/FreeRTOS y partición de aplicación única. `build/` y `managed_components/` son generados y no se versionan. El ELF y los binarios aparecen en `firmware/esp32/build/`.

### 4. Encontrar el puerto USB y transferir

Conecta el USB-C de datos de la placa (un cable solo de carga no funciona). Antes y después de conectarla, compara:

```bash
ls /dev/cu.usb* /dev/cu.wchusbserial* 2>/dev/null
```

En macOS los nombres comunes para esta placa son `/dev/cu.usbmodem*` o `/dev/cu.wchusbserial*`; la ruta concreta varía según el cable, el puente USB y la enumeración. También puede consultarse en **ESP-IDF: Select Port to Use** de VS Code. No publiques el identificador de serie.

Con el puerto identificado (sustituye `PORT`):

```bash
idf.py -p PORT flash
idf.py -p PORT monitor
```

O abre de una vez el monitor después de transferir:

```bash
idf.py -p PORT flash monitor
```

El monitor usa la velocidad configurada por ESP-IDF (115200 baudios por defecto). Sal con `Ctrl+]`. El firmware imprime arranque, estado de BSP, vista actual, heap libre, bloque libre mayor y PSRAM libre. La versión actual es de diagnóstico: recorre diagnóstico, imagen decorativa, carátula local con título/artista y QR local de prueba cada 5 segundos. No conecta Wi-Fi/Firebase, no reproduce audio y no activa controles externos.

### 5. Si no conecta o no entra al bootloader

- Comprueba que el cable USB transmita datos, prueba otro cable/puerto y cierra el monitor serie antes de volver a flashear: dos procesos no pueden abrir el mismo puerto.
- Si el puerto no aparece, desconecta/conecta la placa, revisa `System Information > USB` y prueba el conector USB de datos de la placa. No instales un driver CH340/CP210x salvo que la revisión conectada use ese puente; el USB nativo CDC no lo necesita.
- Si `idf.py flash` no sincroniza, mantén pulsado **BOOT**, pulsa y suelta **RESET**, y suelta **BOOT**; vuelve a ejecutar el flash. Si esa revisión no expone RESET separado, mantén BOOT mientras conectas USB y suéltalo al iniciar la transferencia. Waveshare indica mantener BOOT mientras se reinicia o se conecta la placa para entrar en download mode; consulta [Firmware Flashing and Erasing](https://docs.waveshare.com/ESP32-S3-Touch-LCD-4B/Firmware-Flashing).
- Si la transferencia se corta, conecta directamente al Mac sin hub, vuelve a seleccionar el puerto y repite `idf.py -p PORT flash`. No borres toda la flash como primer recurso.
- Si el monitor muestra caracteres corruptos, selecciona 115200 baudios. Usa `Ctrl+]` para cerrarlo.
- Si la compilación SDL dice que no encuentra headers C++ como `algorithm` o `string`, verifica Xcode Command Line Tools con `xcode-select -p`. En el host de validación fue necesario pasar el SDK explícitamente: `SDK=$(xcrun --sdk macosx --show-sdk-path); cmake -S firmware/simulator -B firmware/simulator/build-lvgl95 -DCMAKE_OSX_SYSROOT="$SDK" -DCMAKE_CXX_FLAGS="-stdlib=libc++ -isystem $SDK/usr/include/c++/v1"`.
- La compilación no prueba pantalla, alimentación, USB ni arranque físico. No alimentar todavía accesorios externos; en esta fase solo se conecta la placa por USB.

## Primeras pruebas al recibir la placa

1. Inspecciona la revisión serigrafiada y compara la placa con la documentación y el pinout de [HARDWARE.md](../docs/HARDWARE.md). No conectes todavía AW9523B, botones, encoder, fuente externa ni altavoz.
2. Con USB de datos, identifica el puerto, transfiere `firmware/esp32/build/cuadro_sonoro_diagnostic.bin` mediante `idf.py -p PORT flash` y abre `idf.py -p PORT monitor`.
3. Confirma por el monitor que arranca `0.1.0-diagnostico`, muestra resolución 480 × 480 y no registra error BSP.
4. Observa el ciclo de 5 s y confirma visualmente diagnóstico, ilustración decorativa, portada con metadatos y QR. Escanea el QR con una cámara; es el valor ficticio `cuadro-demo`, no corresponde a un dispositivo asignado.
5. Registra versión de placa, salida serie redactada, legibilidad, colores, orientación, estabilidad durante 10 minutos y fallos de memoria. No atribuyas problemas al panel sin repetir con un cable USB fiable y alimentación estable.
6. Apaga y desconecta antes de empezar las verificaciones eléctricas y los periféricos de la siguiente fase de [HARDWARE.md](../docs/HARDWARE.md).

## Límites de esta fase

El modo de diagnóstico está seleccionado explícitamente por el proyecto ESP-IDF y separado del modo de producto futuro. El simulador conserva su modo Firebase: el acceso a RTDB/Storage, descargas temporales, teclado y reinicio de ventana son específicos de escritorio. La vista LVGL y las imágenes decorativas/de prueba están compartidas; acceso a archivos, red y temporización de entrada no se comparte. La pantalla común no implica que la inicialización o el render en hardware estén verificados. No se han implementado Wi-Fi en firmware, Firebase en firmware, audio, portal, botones, AW9523B, encoder ni OTA.
