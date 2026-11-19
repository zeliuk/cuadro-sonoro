# Plan de trabajo

## Fase 0 — Revisar la base

Leer definición y estado; revisar Git; ejecutar demo, API local, tests, checks y comandos documentados; registrar límites reales del entorno. No requiere servicios de nube ni hardware.

## Fase 1 — Acceso y datos por cuadro (en curso)

Completado: la API deriva ámbitos del identificador sin alta previa; IDs válidos crean o recuperan estado y se aíslan mediante SHA-256. La web recibe `#token=...`, lo mantiene en `sessionStorage`, limpia la URL y cambia de cuadro cancelando solicitudes anteriores. Las reglas Firebase permiten lecturas públicas por URL conocida en las rutas acordadas; listados y escrituras directas siguen cerrados. La conexión Admin, una importación anterior y la reproducción web en Chrome Headless están registradas en VALIDACION. La web pública queda decidida en `https://sonoro.zeliuk.xyz`; publicación, HTTPS, CORS desde ese origen y recorrido integrado están pendientes de comprobar. Los datos antiguos no se migran automáticamente. Se documentó el recorrido de instalación Wi-Fi y los gestos físicos acordados; todavía no hay firmware ni hardware que los implemente.

## Fase 2 — Importación real fiable

Comprobación inicial completada en Docker local: búsqueda de YouTube, selección explícita, descarga y conversión, subida de MP3/portada a Firebase real, publicación RTDB y reproducción en Chrome Headless. Implementado localmente: recuperación acotada tras reinicio, cancelación durable, publicación atómica, conservación de selección previa y persistencia SQLite Docker. La búsqueda usa yt-dlp y la descarga usa RapidAPI. Carlos comunica que el backend funciona en Render con RapidAPI. Ese reporte manual no trae resultados detallados de búsqueda, importación, recuperación o estabilidad y no se verificó durante esta fase; quedan pendientes de validación documentada esos aspectos y escucha humana. Mantener una instancia/worker. Codex no desplegó servicios ni consumió cuota en esta actualización documental.

## Fase 3 — Completar la configuración web

Herramientas de desarrollo ya existentes: servidor local de `web/`, publicación Bonjour y QR ficticio. Se conservan para desarrollo/pruebas y no son el acceso de producción. Trabajo pendiente: publicar `web/` en el hosting HTTPS de Carlos y verificarlo; configurar y comprobar CORS desde el origen acordado en Render; completar QR/NFC físico; validar Radio Browser y streams en navegador/ESP32; completar procesamiento de imagen y limpieza segura incluyendo reproducciones activas; terminar demo publicable. No añadir control remoto del sonido. La interfaz y el acceso público no requieren que el móvil comparta Wi-Fi con el cuadro.

## Fase 4 — Hardware y firmware

Componentes seleccionados para el primer prototipo: Waveshare ESP32-S3-Touch-LCD-4B, AW9523B, pulsadores RGB 5 V y encoder EC11. La lista, cableado propuesto y pasos de comprobación están en `docs/HARDWARE.md`; falta recibir/comprobar piezas, medir la alimentación, validar las señales y montar el circuito. Implementar después consulta de configuración, streaming sin SD, botones y luces, rueda de volumen, imagen en reposo y portal local de Wi-Fi. Implementar primera instalación offline con punto de acceso protegido por contraseña del dispositivo; QR musical con botón 1 (2 s/20 s); restablecimiento Wi-Fi solo con 2+3 (5 s, cuenta atrás cancelable); reconexión sin borrado automático al perder Internet; aislamiento correcto de gestos largos/combinados. Comprobar cambios durante reproducción, pérdidas de red y arranque silencioso. Añadir compilación/carga y monitor serie cuando se elija el entorno. El ESP32 no sirve la web musical. WiFiManager puede evaluarse, pero no es una dependencia decidida.

## Fase 5 — Montaje y despliegue final

Resolver estructura física, montaje y pruebas para un familiar. Verificar hosting web, conexión a Render y Firebase, CORS, costes observados y diagnóstico; documentar el portal Wi-Fi del dispositivo por separado. Revisar recursos de demo y licencia antes de anunciar reutilización del código.

Cada fase acaba con documentación operativa, verificaciones relevantes y `ESTADO.md`/`VALIDACION.md` actualizados. La definición es destino del producto, no checklist ya completado.
