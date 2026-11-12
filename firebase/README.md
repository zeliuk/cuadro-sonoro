# Firebase

En la primera revisión local no necesitas crear recursos: la demo funciona sin nube y la API usa SQLite si `FIREBASE_DATABASE_URL` está vacía.

Se usarán Realtime Database para datos y Storage para archivos. No se usa Firebase Hosting; `firebase.json` solo declara reglas de Database y Storage. Las reglas iniciales deniegan acceso directo de clientes y no configuran todavía el acceso por cuadro del ESP32.

## Configuración real, cuando se aborde esa fase

Requiere un proyecto dedicado autorizado por su propietario, región y facturación decididas, y Firebase CLI disponible. No se activa facturación ni se crea un proyecto al ejecutar la demo o los tests.

Desde la raíz del repo, comprobar herramientas y autenticar la CLI si todavía no lo está:

```bash
firebase --version
firebase login
firebase projects:list
firebase use --add
```

Elegir el proyecto dedicado correcto; el alias se guarda en `.firebaserc`, ignorado por Git. Copiar los datos del recurso a `backend/.env` y guardar la cuenta de servicio según [CONFIGURACION.md](../docs/CONFIGURACION.md).

Para desplegar únicamente estas reglas al proyecto seleccionado, cuando forme parte de la tarea autorizada:

```bash
firebase deploy --only database,storage
```

Este comando cambia acceso remoto y no forma parte del arranque local. No ejecutar sobre un proyecto reutilizado sin revisar sus reglas existentes. Las reglas cerradas no bloquean Admin SDK: el backend se autoriza por IAM. Verificar escrituras y lecturas con recursos dedicados antes de dar por probada una importación.

Todavía no hay emuladores configurados ni comandos de seed/limpieza por cuadro. Añadir sus instrucciones cuando existan; no presentar RTDB SQLite como si fuera un emulador Firebase.
