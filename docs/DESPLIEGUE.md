# Despliegue: receta y condiciones previas

Esta entrega no crea proyectos remotos ni despliega servicios. Primero completar las fases de [PLAN.md](PLAN.md), especialmente validar la lectura pública por URL conocida y una importación en Firebase real, además de la ejecución recuperable. El backend ya aísla sus datos por identificador; la receta heredada `render.prototype.yaml` sigue siendo referencia del prototipo, no el blueprint final ni garantía de ejecución fiable.

## Web en el servidor propio

Servir únicamente `web/` con HTTPS. Nunca subir `.env`, backend, cuentas de servicio o el repo completo a una carpeta pública. No hay build obligatorio. El comando exacto de subida dependerá del acceso/proveedor del servidor de Carlos y se añadirá cuando se configure. Mantener la demo hasta integrar el acceso del cuadro en el flujo web.

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

Render Free puede suspender/reiniciar el proceso y su disco es temporal. Antes de elegir plan/worker, validar la continuidad y recuperación de tareas. Un proceso dentro de FastAPI no demuestra por sí solo esa garantía. Descargar desde la IP de Render sigue pendiente; una búsqueda correcta no acredita la descarga.

## Firebase

Consultar [firebase/README.md](../firebase/README.md) para seleccionar proyecto, credenciales y comando de reglas. Firebase Hosting no se usa. La facturación de Storage, región y cuotas deben decidirse antes de activar recursos. No interpretar una cuota gratuita como un límite de gasto.

## Aceptación real

Verificar lectura por URL conocida, separación de registros, listados/escrituras denegados; buscar desde Render; procesar una pista de prueba adecuada; comprobar MP3, imagen y metadatos; escuchar desde navegador; verificar fallo/cancelación/sustitución sin pérdida; cerrar y reabrir la web; reiniciar el servicio; confirmar limpieza segura. Registrar evidencia redactada y coste observado sin incluir URLs de cuadro ni credenciales. El ESP32 se valida en su propia fase.
