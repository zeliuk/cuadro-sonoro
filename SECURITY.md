# Credenciales y publicación

El repo público no implica datos, importador o archivos públicos. No versionar `.env`, cuentas de servicio, tokens reales, cookies, claves privadas, bases de ejecución o medios personales. Las plantillas contienen privados vacíos.

El token global `IMPORT_API_TOKEN` existe solo en el prototipo de desarrollo; no distribuirlo a invitados ni incorporarlo a la web pública. El producto usa acceso limitado por cuadro, pendiente de implementación. La cuenta de servicio Firebase pertenece al servidor, nunca al navegador o ESP32. El familiar solo configura Wi-Fi; no gestiona administración de nube.

Las variables enviadas al navegador son visibles. CORS no autoriza usuarios. Admin SDK se rige por IAM y no por reglas Firebase de clientes. No abrir reglas como solución a un fallo de permisos.

Desde la raíz, antes de commit:

```bash
git diff --cached --name-only
python3 scripts/check_public_repo.py --staged
```

El script muestra rutas/motivos y omite valores; es una comprobación limitada del índice, no una auditoría de historial. Revisar diff y usar protección de secretos del proveedor cuando esté disponible.

Si una credencial real se publica, revocarla o rotarla primero, sin repetir su valor al informar. Retirar un archivo o añadir `.gitignore` no elimina versiones previas. Revisar impacto e historial con el propietario antes de reescribirlo o forzar pushes. No borrar datos de nube como respuesta automática.

Las pruebas reales usarán recursos dedicados, con resultados redactados. No compartir tokens de cuadros, contraseñas Wi-Fi ni URLs firmadas en capturas o issues públicos. Las subidas e imágenes se validarán con límites y se limpiarán según las referencias activas.
