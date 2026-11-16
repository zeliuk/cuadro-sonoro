# Despliegue: receta y condiciones previas

Esta entrega no crea proyectos remotos ni despliega servicios. Primero completar las fases de [PLAN.md](PLAN.md), especialmente validar la lectura pública por URL conocida y una importación en Firebase real, además de la ejecución recuperable. El backend ya aísla sus datos por identificador; la receta heredada `render.prototype.yaml` sigue siendo referencia del prototipo, no el blueprint final ni garantía de ejecución fiable.

## Web servida por el ESP32

El enlace del cuadro conserva `http://cuadro-sonoro-<id-dispositivo>.local/#token=<id-cuadro>`. Para la prueba actual, sirve `web/` local y llama a `https://cuadro-sonoro.onrender.com`; configuración, límites, logs y rollback están en [PRUEBA_APIFY_RENDER.md](PRUEBA_APIFY_RENDER.md). La integración Apify/Render no está validada hasta la prueba real. Esto no valida firmware ni acceso móvil desde el hostname doméstico.

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

## Prueba de API en Render con Apify

`web/index.html` apunta a `https://cuadro-sonoro.onrender.com` para la prueba autorizada. Apify sustituye el acceso a YouTube desde Render, pero esta integración no está validada hasta ejecutar la prueba manual. Sigue [PRUEBA_APIFY_RENDER.md](PRUEBA_APIFY_RENDER.md) para variables, límites, despliegue, logs, prueba con proveedores reales y rollback. No despliegues ni generes consumo automáticamente.

## Firebase

Consultar [firebase/README.md](../firebase/README.md) para seleccionar proyecto, credenciales y comando de reglas. Firebase Hosting no se usa. La facturación de Storage, región y cuotas deben decidirse antes de activar recursos. No interpretar una cuota gratuita como un límite de gasto.

## Aceptación real

Verificar lectura por URL conocida, separación de registros, listados/escrituras denegados; buscar y procesar una pista de prueba adecuada desde el alojamiento elegido; comprobar MP3, imagen y metadatos; escuchar desde navegador; verificar fallo/cancelación/sustitución sin pérdida; cerrar y reabrir la web; reiniciar el servicio; confirmar limpieza segura. Registrar evidencia redactada y coste observado sin incluir URLs de cuadro ni credenciales. El ESP32 se valida en su propia fase.
