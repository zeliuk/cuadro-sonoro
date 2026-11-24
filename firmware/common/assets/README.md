# Recursos comunes

- `imagen-decorativa.jpg`: ilustración de reposo usada por el simulador.
- `caratula-demo.jpg`: carátula ficticia cuadrada de 320 × 320.
- `NotoSans-Regular.ttf`: Noto Sans bajo SIL OFL 1.1, usada en escritorio para tildes y ajuste de texto.
- `../src/diagnostic_assets.cpp`: conversión derivada de los dos JPEG a píxeles RGB565 compilados como imágenes LVGL; evita dependencia de sistema de archivos y decodificador JPEG en placa. Si se sustituye alguno de los JPEG fuente, regenerar las matrices con Pillow 11.3.0 y revisar dimensiones/color.

Los recursos son pruebas locales ficticias, no pertenecen a una canción o servicio real. El modo Firebase del simulador obtiene imágenes temporalmente desde Storage.
