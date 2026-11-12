# Desarrollo y contribución

Leer [AGENTS.md](AGENTS.md), [definición](docs/DEFINICION.md), [estado](docs/ESTADO.md) y [plan](docs/PLAN.md). Mantener cambios pequeños y conservar el diseño.

Desde la raíz, revisar antes de editar:

```bash
git status --short
git diff
```

Si hay un repo con commit inicial, crear una rama cuando ayude a aislar el trabajo:

```bash
git switch -c feat/nombre-del-cambio
```

Usar documentación/UI en español y código con nombres descriptivos. No añadir comentarios redundantes, framework o infraestructura sin necesidad. Actualizar los ejemplos curl, variables y comandos en el mismo cambio que modifique la implementación. Registrar cambios de alcance en decisiones/definición.

Checks con `.venv` activado:

```bash
env -u FIREBASE_DATABASE_URL -u FIREBASE_STORAGE_BUCKET -u FIREBASE_SERVICE_ACCOUNT_JSON -u GOOGLE_APPLICATION_CREDENTIALS python -m pytest backend/tests scripts/tests -q
python -m compileall -q backend scripts
node --check web/app.js
```

Preparar y revisar el commit:

```bash
git add .
git diff --cached --stat
python3 scripts/check_public_repo.py --staged
git diff --cached
```

No subir `.env`, secretos, medios o bases de ejecución. El control básico no revisa historial ni detecta todos los secretos. No usar producción en tests. Distinguir evidencia simulada, de nube y de hardware. Ver [seguridad](SECURITY.md).

Un cambio termina con comportamiento verificable, checks relevantes, documentación actualizada y límites declarados. No activar facturación/desplegar como efecto lateral de un cambio local. La licencia del código está pendiente de decisión del titular; las dependencias mantienen sus licencias.
