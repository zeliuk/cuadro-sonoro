# Recursos comunes

- `imagen-decorativa.jpg`: ilustración de reposo usada por el simulador.
- `caratula-demo.jpg`: carátula ficticia cuadrada de 320 × 320.
- `NotoSans-Regular.ttf`: Noto Sans bajo SIL OFL 1.1; fuente de origen para las fuentes compactas de LVGL.
- `../src/font_noto_sans_16.c` y `font_noto_sans_20.c`: subconjuntos Noto Sans de 16 y 20 px, Bpp 4; incluyen ASCII y Latin-1 (tildes, ñ, ü, ¿ y ¡) para el simulador y la placa. Se generaron con `lv_font_conv` 1.5.3. Para regenerarlos desde la raíz del repositorio:

  ```bash
  npx --yes lv_font_conv --size 20 --bpp 4 --no-compress --format lvgl --font firmware/common/assets/NotoSans-Regular.ttf -r 0x20-0x7E -r 0xA1-0xFF --output firmware/common/src/font_noto_sans_20.c --lv-font-name sonoro_noto_sans_20 --lv-include lvgl.h
  npx --yes lv_font_conv --size 16 --bpp 4 --no-compress --format lvgl --font firmware/common/assets/NotoSans-Regular.ttf -r 0x20-0x7E -r 0xA1-0xFF --output firmware/common/src/font_noto_sans_16.c --lv-font-name sonoro_noto_sans_16 --lv-include lvgl.h
  ```
- `../src/diagnostic_assets.cpp`: conversión derivada de los dos JPEG a píxeles RGB565 compilados como imágenes LVGL; evita dependencia de sistema de archivos y decodificador JPEG en placa. Si se sustituye alguno de los JPEG fuente, regenerar las matrices con Pillow 11.3.0 y revisar dimensiones/color.

Los recursos son pruebas locales ficticias, no pertenecen a una canción o servicio real. El modo Firebase del simulador obtiene imágenes temporalmente desde Storage.
