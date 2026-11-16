# Firmware ESP32 — fase pendiente

Todavía no hay firmware ejecutable, placa elegida ni comandos de compilación/carga. Se documentarán y probarán al elegir el entorno y el hardware; no copiar un pinout genérico como definitivo.

Requisitos acordados: identificador fijo asignado al cuadro; tres botones iluminados; rueda de volumen; pantalla a color; streaming Wi-Fi con búfer, sin microSD; arranque silencioso; una canción termina y se detiene. El ESP32 consulta configuración/medios de Firebase y reproduce MP3 desde Storage o emisoras desde sus streams; no aloja la web musical. El portal local con QR configura/restablece Wi-Fi, separado del QR/NFC musical público. Mantener pulsado cualquier botón restablece solo Wi-Fi, tras cuenta atrás. La contraseña Wi-Fi se conserva en el dispositivo y no se envía a la web ni servicios cloud.

Cambiar una selección no interrumpe la reproducción activa; la nueva se usa en la siguiente activación. El guardado web no inicia ni detiene audio físico. La web y el cuadro tienen reproducciones y volúmenes independientes. El familiar no instala herramientas ni introduce credenciales técnicas; solo configura su Wi-Fi.

La propuesta ESP32-S3 con PSRAM es orientativa. Placa, pantalla, amplificador, alimentación, componentes y pines no están elegidos. Antes de esta fase: validar el flujo de la web pública y escoger el hardware; el reporte de Carlos de backend RapidAPI no valida el dispositivo. Al implementarla, añadir requisitos/versiones, configuración privada, compilación, USB, monitor serie, prueba de audio/pantalla/botones, recuperación de red y restablecimiento. Nunca incorporar tokens reales, Wi-Fi o credenciales Admin SDK al repositorio.
