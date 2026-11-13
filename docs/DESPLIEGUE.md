# Despliegue: receta y condiciones previas

Esta entrega no crea proyectos remotos ni despliega servicios. Primero completar las fases de [PLAN.md](PLAN.md), especialmente validar la lectura pública por URL conocida y una importación en Firebase real, además de la ejecución recuperable. El backend ya aísla sus datos por identificador; la receta heredada `render.prototype.yaml` sigue siendo referencia del prototipo, no el blueprint final ni garantía de ejecución fiable.

## Web servida por el ESP32

Decisión confirmada: el ESP32 servirá los archivos estáticos de `web/` por HTTP dentro de la red doméstica. El móvil abrirá un hostname local único, preferentemente mDNS, desde QR/NFC; no se usará `localhost` ni una IP fija en el enlace. El navegador del móvil ejecutará la interfaz y llamará directamente a la API HTTPS de Render. Hay que validar la resolución mDNS en Android/iOS y routers, configurar CORS para el origen local, y documentar una alternativa (reserva DHCP o IP local visible) si mDNS no funciona. La integración espera a elegir hardware/firmware; no se han validado comandos de compilación ni despliegue.

## Comprobar el contenedor local

Desde la raíz, con Docker y `.env` local preparado:

```bash
docker compose config --quiet
docker compose build api
docker compose up -d
docker compose ps
docker compose logs --tail=100 api
curl -sS http://127.0.0.1:8000/health
```

Logs pueden contener detalles de operación: redactar cualquier valor sensible antes de compartirlos. Parada y recreación se explican en [backend/README.md](../backend/README.md).

## Render

Cuando esté autorizado, crear un servicio Docker desde el repositorio con contexto raíz y `Dockerfile` raíz. El proceso usa `PORT` y `/health`. En el prototipo se requiere un worker Uvicorn y una instancia. Las variables se inyectan en ejecución; no añadir cuentas de servicio al build. Configurar CORS con el origen exacto de la web propia.

Render Free puede suspender/reiniciar el proceso y su disco es temporal. Antes de elegir plan/worker, validar la continuidad y recuperación de tareas. Un proceso dentro de FastAPI no demuestra por sí solo esa garantía. Descargar desde la IP de Render sigue pendiente; una búsqueda correcta no acredita la descarga. CORS deberá permitir el origen local desde el que se sirva la web en el ESP32; no es una autenticación ni controla quién puede llamar a la API fuera del navegador.

## Firebase

Consultar [firebase/README.md](../firebase/README.md) para seleccionar proyecto, credenciales y comando de reglas. Firebase Hosting no se usa. La facturación de Storage, región y cuotas deben decidirse antes de activar recursos. No interpretar una cuota gratuita como un límite de gasto.

## Aceptación real

Verificar lectura por URL conocida, separación de registros, listados/escrituras denegados; buscar desde Render; procesar una pista de prueba adecuada; comprobar MP3, imagen y metadatos; escuchar desde navegador; verificar fallo/cancelación/sustitución sin pérdida; cerrar y reabrir la web; reiniciar el servicio; confirmar limpieza segura. Registrar evidencia redactada y coste observado sin incluir URLs de cuadro ni credenciales. El ESP32 se valida en su propia fase.
