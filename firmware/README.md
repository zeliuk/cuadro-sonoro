# Firmware ESP32 — fase pendiente

Todavía no hay firmware ejecutable, placa elegida ni comandos de compilación/carga. Se documentarán y probarán al elegir el entorno y el hardware; no copiar un pinout genérico como definitivo.

Requisitos acordados: token fijo preparado por el desarrollador; tres botones iluminados; rueda de volumen; pantalla a color; streaming Wi-Fi con búfer, sin microSD; arranque silencioso; una canción termina y se detiene; portal local con QR para Wi-Fi. Mantener pulsado cualquier botón restablece solo Wi-Fi, tras cuenta atrás. La imagen decorativa procede de la web.

Cambiar una selección no interrumpe la reproducción activa. El audio llega directamente de Storage o de la emisora. El familiar no instala herramientas ni introduce credenciales técnicas; solo configura su Wi-Fi.

Antes de esta fase: validar API, importación real y reproducción en navegador. Al implementarla, añadir requisitos/versiones, configuración privada, compilación, USB, monitor serie, prueba de audio/pantalla/botones, recuperación de red y restablecimiento. Nunca incorporar tokens reales, Wi-Fi o credenciales Admin SDK al repositorio.
