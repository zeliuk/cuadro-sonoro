# Puesta en marcha desde cero

Abre la carpeta **`cuadro-sonoro`** completa en VS Code. Todos los comandos de esta guía parten de esa raíz. Si ya tienes Git inicializado, revisa cambios antes de copiar archivos; no hace falta borrar un repositorio remoto para usar esta base.

## 1. Revisar herramientas

```bash
python3 --version
git --version
python3 scripts/check_project.py
```

Para ver la demo basta Python 3. Para instalar el backend se recomienda Python 3.12; para importar hacen falta también FFmpeg/ffprobe y Deno. Node permite el check JS; Docker es una alternativa de ejecución. Si faltan herramientas en tu Mac, pide a Codex que compruebe las existentes antes de instalar. No instalar paquetes del proyecto en el Python del sistema.

## 2. Ver la web sin API ni credenciales

```bash
python3 -m http.server 5173 --bind 127.0.0.1 --directory web
```

Abre [la web](http://127.0.0.1:5173). Comprueba tres huecos, búsqueda simulada, selección, progreso, cancelación y persistencia al recargar. Se detiene con `Ctrl+C`. La continuidad de una tarea real al cerrar la web no está demostrada por los temporizadores de demo.

## 3. API

Sigue [backend/README.md](../backend/README.md): instalación, preparación de `.env`, arranque nativo o Docker, comprobación HTTP, logs, tests y parada. Sigue [PRUEBA_API.md](PRUEBA_API.md) para comprobar rutas en orden.

## 4. Comenzar con Codex

Lee y envía el encargo actualizado de [PRIMER_PASO_CODEX.md](PRIMER_PASO_CODEX.md). El backend ya separa datos por token; sigue el plan para completar el acceso de web y dispositivo. No presentar la importación real ni el firmware como validados.

## Problemas habituales

| Síntoma | Comprobación |
|---|---|
| `python3.12` no existe | Confirmar la instalación de Python 3.12 y su comando local. |
| No se importan módulos `backend` | Ejecutar Uvicorn desde la raíz, no desde `backend/`. |
| Puerto ocupado | Identificar el proceso antes de detenerlo; si cambias el puerto API, actualizar la URL web y CORS según corresponda. |
| 401 | Falta el Bearer, no tiene al menos 32 caracteres o no está provisionado. Para la revisión local, cargar `LOCAL_FRAME_TOKEN` de `backend/.env` sin imprimirlo. |
| 503 de importación | Firebase no configurado; es normal en la revisión local sin nube. |
| Búsqueda devuelve 502 | Comprobar dependencias, red y logs redactados; una búsqueda fallida no se arregla abriendo reglas Firebase. |
| Fallo al obtener medios | Verificar recurso del hueco, credenciales y capacidad de generar URL firmada. |
