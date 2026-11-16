# Despliegue: receta y condiciones previas

Esta entrega no crea proyectos remotos ni despliega servicios. Primero completar las fases de [PLAN.md](PLAN.md), especialmente validar la lectura pública por URL conocida y una importación en Firebase real, además de la ejecución recuperable. El backend ya aísla sus datos por identificador; la receta heredada `render.prototype.yaml` sigue siendo referencia del prototipo, no el blueprint final ni garantía de ejecución fiable.

## Web servida por el ESP32

El enlace del cuadro conserva `http://cuadro-sonoro-<id-dispositivo>.local/#token=<id-cuadro>`. El HTML versionado apunta a `http://127.0.0.1:8000`; la guía [PRUEBA_RAPIDAPI.md](PRUEBA_RAPIDAPI.md) explica cómo configurar RapidAPI en la API local o en Raspberry Pi. `RAPIDAPI_KEY` solo se configura en el backend. No se ha validado móvil ni firmware.

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

## API remota

La integración RapidAPI puede ejecutarse desde una API local o alojada, pero debe configurarse `RAPIDAPI_KEY` como secreto de backend y revisarse el coste/cuota antes de importar. No se ha validado en Render ni se ha hecho un despliegue por este cambio. Consulta [PRUEBA_RAPIDAPI.md](PRUEBA_RAPIDAPI.md) antes de una prueba real.

## Firebase

Consultar [firebase/README.md](../firebase/README.md) para seleccionar proyecto, credenciales y comando de reglas. Firebase Hosting no se usa. La facturación de Storage, región y cuotas deben decidirse antes de activar recursos. No interpretar una cuota gratuita como un límite de gasto.

## Aceptación real

Verificar lectura por URL conocida, separación de registros, listados/escrituras denegados; buscar y procesar una pista de prueba adecuada desde el alojamiento elegido; comprobar MP3, imagen y metadatos; escuchar desde navegador; verificar fallo/cancelación/sustitución sin pérdida; cerrar y reabrir la web; reiniciar el servicio; confirmar limpieza segura. Registrar evidencia redactada y coste observado sin incluir URLs de cuadro ni credenciales. El ESP32 se valida en su propia fase.
