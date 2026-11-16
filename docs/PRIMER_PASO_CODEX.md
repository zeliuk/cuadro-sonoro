# Primer paso con Codex en VS Code

Abre la carpeta completa `cuadro-sonoro`, que contiene `AGENTS.md`. Copia este encargo:

> Vamos a desarrollar cuadro-sonoro. Lee AGENTS.md y sigue este documento. Después lee docs/DEFINICION.md, docs/ESTADO.md, README, arquitectura, configuración y plan. Revisa Git y respeta cambios existentes. El primer paso de fase 1 ya separa backend y medios nuevos por token Bearer de cuadro; conserva los tres huecos y los comportamientos de la definición. Revisa el resultado y sus pruebas, completa la integración necesaria sin alterar el diseño y mantén API/OpenAPI/guías alineados. No uses servicios reales ni credenciales de producción salvo que la fase lo autorice expresamente. Prioriza móvil. Resuelve decisiones rutinarias sin volver a preguntar lo acordado; presenta antes cualquier decisión que cambie materialmente autorización o ejecución. No implementes firmware ni cambies el stack sin indicación. No actives facturación ni despliegues servicios remotos. No muestres secretos. Explica qué está comprobado con mocks, servicios reales o hardware real.

El estado previo de las primeras sesiones y la importación anterior se conserva en [VALIDACION.md](VALIDACION.md). La búsqueda actual usa yt-dlp y RapidAPI prepara el resultado elegido; Carlos comunica que el backend funciona en Render con RapidAPI. Esta comunicación no acredita el despliegue de la web pública, CORS desde ella ni el hardware. La URL decidida para la web es `https://sonoro.zeliuk.xyz`; consulta [ESTADO.md](ESTADO.md), [DEFINICION.md](DEFINICION.md) y [PRUEBA_RAPIDAPI.md](PRUEBA_RAPIDAPI.md).

Para nuevas sesiones usar el estado actual de Git, definición, estado y plan, sin depender de esta conversación. La documentación de endpoints tiene que cambiar junto a su código.
