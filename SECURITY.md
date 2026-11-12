# Credenciales y publicación

El repo público no implica datos, importador o archivos públicos. No versionar `.env`, cuentas de servicio, tokens reales, cookies, claves privadas, bases de ejecución o medios personales. Las plantillas contienen privados vacíos.

El backend recibe un identificador público como Bearer solo para derivar el ámbito SHA-256; no autentica ni autoriza usuarios. Cualquier ID válido de 1–128 caracteres ASCII puede leer o cambiar ese ámbito mediante la API. No hay lista de altas, Firebase Auth ni token global. La decisión de Carlos es que la configuración publicada y los medios puedan leerse sin sesión si se conocen sus URLs; SHA-256 separa rutas, no protege esa lectura ni las mutaciones API. No incorporar credenciales Admin a web o ESP32. Las reglas Firebase no permiten escrituras ni listados generales. El firmware sigue pendiente.

Las variables enviadas al navegador son visibles. CORS no autoriza usuarios. Admin SDK se rige por IAM y no por reglas Firebase de clientes. No abrir reglas como solución a un fallo de permisos.

Desde la raíz, antes de commit:

```bash
git diff --cached --name-only
python3 scripts/check_public_repo.py --staged
```

El script muestra rutas/motivos y omite valores; es una comprobación limitada del índice, no una auditoría de historial. Revisar diff y usar protección de secretos del proveedor cuando esté disponible.

Si una credencial real se publica, revocarla o rotarla primero, sin repetir su valor al informar. Retirar un archivo o añadir `.gitignore` no elimina versiones previas. Revisar impacto e historial con el propietario antes de reescribirlo o forzar pushes. No borrar datos de nube como respuesta automática.

Las pruebas reales usarán recursos dedicados, con resultados redactados. No publicar identificadores/enlaces de cuadros ni credenciales Admin. Las URLs de medios son legibles por cualquiera que las conozca; no son firmadas ni temporales. Las subidas e imágenes se validarán con límites y se limpiarán según las referencias activas.
