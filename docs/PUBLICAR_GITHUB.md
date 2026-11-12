# Colocar la base en GitHub

El ZIP incluye una carpeta `cuadro-sonoro/`: esa carpeta es la raíz del repositorio. `EMPEZAR_AQUI.md`, a su lado, es una guía de entrega que no hace falta incluir en GitHub. Las instrucciones para ChatGPT sí se versionan, en `docs/INSTRUCCIONES_CHATGPT.md`. No crear repositorios Git separados dentro de web/backend/firmware.

## Si empiezas en una carpeta nueva

Desde la raíz `cuadro-sonoro/`:

```bash
git init -b main
git add .
git diff --cached --name-only
python3 scripts/check_public_repo.py --staged
git diff --cached --stat
git commit -m "Prepare cuadro-sonoro development base"
```

Después, publica desde Control de código fuente de VS Code en un repositorio público llamado `cuadro-sonoro`, o crea un remoto vacío y usa los comandos que GitHub muestre para tu URL. No precrear otro README remoto si vas a subir este primer commit. No se proporciona una URL inventada de tu cuenta.

Si el repo ya existe, conservar `.git` e historial, trabajar en una rama y revisar el diff al integrar. No ejecutar `git init`, borrar el remoto o forzar push para seguir esta guía. Si había cambios recientes en tu Mac, no sustituirlos ciegamente por este paquete basado en el ZIP anterior.

## Verificar exclusiones y estado

```bash
git check-ignore backend/.env secrets/firebase.json serviceAccountKey.json
git status --short
python3 scripts/check_public_repo.py --tracked
```

`check-ignore` informa reglas para archivos nuevos; un archivo ya versionado requiere tratamiento específico. Ver [SECURITY.md](../SECURITY.md) si hubo secretos. El paquete no contiene `.git`, entornos virtuales, cuentas de servicio ni `.env` reales.

Comprueba README y enlaces en GitHub, que CI pasa y que el estado indica prototipo. No anunciar firmware o importación real verificada que aún no existen. En VS Code abrir la carpeta raíz y usar [PRIMER_PASO_CODEX.md](PRIMER_PASO_CODEX.md).
