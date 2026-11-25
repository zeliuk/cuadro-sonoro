# Firmware y simulador

El firmware de placa se desarrolla con ESP-IDF; el simulador conserva SDL2. Las pantallas LVGL, QR, imágenes de diagnóstico y componentes de vista están en `firmware/common/`. El código que lee archivos, Firebase, teclado y ventana vive en `firmware/simulator/`; la inicialización del BSP y el arranque de la placa están en `firmware/esp32/`.

## Versiones fijadas

- ESP-IDF **v5.5.5**, objetivo `esp32s3` (instalación y compilación comprobadas en macOS Intel; Apple Silicon pendiente).
- CMake **3.30.5**, Ninja **1.11.1.1** para el entorno validado.
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

## ESP-IDF en macOS

### 1. Preparar e instalar ESP-IDF 5.5.5

Instala Xcode Command Line Tools y Git. Comprueba `xcode-select -p`, `git --version` y `python3 --version`. ESP-IDF **v5.5.5** admite el objetivo `esp32s3`; no uses herramientas de Arduino para este proyecto.

Instala CMake y Ninja. En el Mac Intel de validación, Homebrew no tenía botellas para esta arquitectura y falló al compilar ambos; se instalaron binarios precompilados con pip:

```bash
python3 -m pip install --user 'cmake==3.30.5' 'ninja==1.11.1.1'
export PATH="$(python3 -m site --user-base)/bin:$PATH"
```

Clona la etiqueta oficial fijada y solo el historial necesario para esta versión. `--depth 1` y `--shallow-submodules` reducen los datos descargados; no se necesita el historial Git completo para compilar:

```bash
mkdir -p ~/esp
git clone --depth 1 --branch v5.5.5 --recursive --shallow-submodules https://github.com/espressif/esp-idf.git ~/esp/esp-idf
cd ~/esp/esp-idf
./install.sh esp32s3
source ./export.sh
```

La instalación coloca el framework en `~/esp/esp-idf`, herramientas como compiladores y OpenOCD en `~/.espressif/tools`, y el entorno Python de IDF en `~/.espressif/python_env/`. Aunque el firmware de diagnóstico es pequeño, esos componentes de desarrollo ocupan varios GB. No se copian al repositorio.

Comprueba las versiones:

```bash
idf.py --version
xtensa-esp-elf-gcc --version
cmake --version
ninja --version
```

En Bash se puede añadir a `~/.bash_profile` el PATH de CMake/Ninja y este alias para activar ESP-IDF cuando se necesite:

```bash
export PATH="$(python3 -m site --user-base)/bin:$PATH"
alias get_idf_5_5_5='source "$HOME/esp/esp-idf/export.sh"'
```

Abre una terminal nueva y ejecuta `get_idf_5_5_5`. No actives ESP-IDF en todas las terminales automáticamente.

### 2. Configurar VS Code

1. En Extensions, instala **ESP-IDF** de Espressif Systems (identificador `espressif.esp-idf-extension`). La instalación usada en macOS Intel fue la extensión 2.3.0.
2. Abre `Preferences: Open User Settings (JSON)` y configura la instalación manual ya existente. La extensión admite `${env:HOME}` en estas rutas:

   ```json
   "idf.customExtraVars": {
     "IDF_PATH": "${env:HOME}/esp/esp-idf",
     "IDF_TOOLS_PATH": "${env:HOME}/.espressif",
     "IDF_PYTHON_ENV_PATH": "${env:HOME}/.espressif/python_env/idf5.5_py3.9_env"
   }
   ```

3. Abre `firmware/esp32/` en VS Code para que la extensión detecte el `CMakeLists.txt` del proyecto. Ejecuta `ESP-IDF: Doctor Command` desde la paleta para revisar la configuración. Para compilar también desde terminal, activa `get_idf_5_5_5` como en el paso anterior.

### 3. Compilar

Desde una terminal con ESP-IDF activado:

```bash
cd firmware/esp32
idf.py set-target esp32s3
idf.py reconfigure
idf.py build
```

La primera compilación descarga el BSP y LVGL desde el Component Registry y crea `dependencies.lock`, que fija las versiones y hashes de las dependencias transitivas; ese archivo sí se versiona. El BSP oficial se distribuye bajo Apache-2.0; no se ha copiado su código fuente al repositorio. `sdkconfig.defaults` selecciona flash QIO de 16 MB, PSRAM octal de 8 MB a 80 MHz, consola USB CDC, LVGL/FreeRTOS y partición de aplicación única. `build/`, `managed_components/`, `sdkconfig` y la configuración local de `.vscode/` no se versionan. El ELF y los binarios aparecen en `firmware/esp32/build/`.

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
