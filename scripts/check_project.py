"""Local preflight: prints availability, never credential values."""
import importlib.util
import shutil
import sys

print(f'Python: {sys.version_info.major}.{sys.version_info.minor}')
for command in ('ffmpeg', 'ffprobe', 'deno', 'docker', 'git', 'node'):
    print(f'{command}: {"disponible" if shutil.which(command) else "no encontrado"}')
for module in ('fastapi', 'yt_dlp', 'firebase_admin'):
    print(f'{module}: {"disponible" if importlib.util.find_spec(module) else "no instalado en este Python"}')
print('Esto comprueba herramientas locales, no una descarga, los permisos de Firebase ni un despliegue.')
