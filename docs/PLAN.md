# Plan de trabajo

## Fase 0 — Revisar la base

Leer definición y estado; revisar Git; ejecutar demo, API local, tests, checks y comandos documentados; registrar límites reales del entorno. No requiere servicios de nube ni hardware.

## Fase 1 — Acceso y datos por cuadro (en curso)

Completado: la API deriva ámbitos del identificador sin alta previa; IDs válidos crean o recuperan estado y se aíslan mediante SHA-256. La web recibe `#token=...`, lo mantiene en `sessionStorage`, limpia la URL y cambia de cuadro cancelando solicitudes anteriores. Las reglas Firebase permiten lecturas públicas por URL conocida en las rutas acordadas; listados y escrituras directas siguen cerrados. La conexión Admin, una importación anterior y la reproducción web en Chrome Headless están registradas en VALIDACION. La web pública queda decidida en `https://sonoro.zeliuk.xyz`; publicación, HTTPS, CORS desde ese origen y recorrido integrado están pendientes de comprobar. Los datos antiguos no se migran automáticamente. Se documentó el recorrido de instalación Wi-Fi y los gestos físicos acordados; el firmware de producto y la validación en hardware siguen pendientes.

## Fase 2 — Importación real fiable

Comprobación inicial completada en Docker local: búsqueda de YouTube, selección explícita, descarga y conversión, subida de MP3/portada a Firebase real, publicación RTDB y reproducción en Chrome Headless. Implementado localmente: recuperación acotada tras reinicio, cancelación durable, publicación atómica, conservación de selección previa y persistencia SQLite Docker. La búsqueda usa yt-dlp y la descarga usa RapidAPI. Carlos comunica que el backend funciona en Render con RapidAPI. Ese reporte manual no trae resultados detallados de búsqueda, importación, recuperación o estabilidad y no se verificó durante esta fase; quedan pendientes de validación documentada esos aspectos y escucha humana. Mantener una instancia/worker. Codex no desplegó servicios ni consumió cuota en esta actualización documental.

## Fase 3 — Completar la configuración web

Herramientas de desarrollo ya existentes: servidor local de `web/`, publicación Bonjour y QR ficticio. Se conservan para desarrollo/pruebas y no son el acceso de producción. Trabajo pendiente: publicar `web/` en el hosting HTTPS de Carlos y verificarlo; configurar y comprobar CORS desde el origen acordado en Render; completar QR/NFC físico; validar Radio Browser y streams en navegador/ESP32; completar procesamiento de imagen y limpieza segura incluyendo reproducciones activas; terminar demo publicable. No añadir control remoto del sonido. La interfaz y el acceso público no requieren que el móvil comparta Wi-Fi con el cuadro.

## Fase 4 — Hardware y firmware

Código común iniciado: vista LVGL y QR en `firmware/common/`; adaptadores SDL2/Firebase y teclado en `firmware/simulator/`; proyecto ESP-IDF en `firmware/esp32/`. Versiones seleccionadas: ESP-IDF 5.5.5, BSP Waveshare 2.0.0, LVGL 9.5.0 y `espressif/esp_jpeg` 1.3.2 para la nueva fase. El firmware v0.3 con SoftAP, portal móvil y lectura RTDB quedó probado físicamente; Carlos confirmó la conexión desde un móvil, consulta a Firebase para `charlie` y reconexión tras reiniciar. La v0.4 añade una lectura de una portada JPEG publicada en Storage, sin audio ni escrituras.

Carlos cargó v0.3 y confirmó que configuró Wi-Fi desde un móvil, la placa cargó Firebase para `charlie` y reconectó tras reiniciar sin repetir la configuración. El sistema operativo del móvil no quedó registrado, así que la compatibilidad de iPhone y Android por separado sigue pendiente. Carlos cargó v0.4 y reportó colores rotos; después confirmó que v0.4.1 corrigió físicamente el orden RGB565. v0.4.2 añadió cambio visual entre huecos 1 y 2 con BOOT/GPIO0 y PWR/TCA9554 EXIO4 integrados. v0.4.3 añadió un spinner inmediato durante la descarga de portada. La foto de una actualización descolocada coincide con tearing: la configuración anterior usaba un framebuffer. v0.4.4 habilitó doble framebuffer con `FULL_REFRESH`, pero Carlos reportó que el parpadeo seguía, especialmente en el loader. v0.4.5 cambió a `DIRECT_MODE` y quitó el fundido del loader, pero la transición aún podía mostrar actualizaciones intermedias porque se construía en la pantalla activa. v0.4.6 prepara cada vista en un screen LVGL separado y lo activa al completarlo, con eliminación de la vista previa en el mismo cambio; compiló con ESP-IDF 5.5.5 y falta probarlo en Waveshare; no se conecta AW9523 externo. Después integrar audio en una etapa separada, cuando se prepare y verifique la ruta de salida de sonido; controles externos, AW9523B, encoder y OTA quedan fuera por ahora. La guía está en `firmware/README.md`; hardware y límites en `docs/HARDWARE.md`.

## Fase 5 — Montaje y despliegue final

Resolver estructura física, montaje y pruebas para un familiar. Verificar hosting web, conexión a Render y Firebase, CORS, costes observados y diagnóstico; documentar el portal Wi-Fi del dispositivo por separado. Revisar recursos de demo y licencia antes de anunciar reutilización del código.

Cada fase acaba con documentación operativa, verificaciones relevantes y `ESTADO.md`/`VALIDACION.md` actualizados. La definición es destino del producto, no checklist ya completado.
