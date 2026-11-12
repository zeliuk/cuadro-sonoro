# Primer paso con Codex en VS Code

Abre la carpeta completa `cuadro-sonoro`, que contiene `AGENTS.md`. Copia este encargo:

> Vamos a desarrollar cuadro-sonoro. Lee AGENTS.md y sigue este documento. Después lee docs/DEFINICION.md, docs/ESTADO.md, README, arquitectura, configuración y plan. Revisa Git y respeta cambios existentes. El primer paso de fase 1 ya separa backend y medios nuevos por token Bearer de cuadro; conserva los tres huecos y los comportamientos de la definición. Revisa el resultado y sus pruebas, completa la integración necesaria sin alterar el diseño y mantén API/OpenAPI/guías alineados. No uses servicios reales ni credenciales de producción salvo que la fase lo autorice expresamente. Prioriza móvil. Resuelve decisiones rutinarias sin volver a preguntar lo acordado; presenta antes cualquier decisión que cambie materialmente autorización o ejecución. No implementes firmware ni cambies el stack sin indicación. No actives facturación ni despliegues servicios remotos. No muestres secretos. Explica qué está comprobado con mocks, servicios reales o hardware real.

Objetivo de la primera sesión completado: entorno local revisado y primer avance de aislamiento por cuadro. Las reglas públicas se aplicaron manualmente en Firebase real y se validó una importación desde búsqueda de YouTube hasta reproducción en Chrome Headless con Docker local. La lectura es pública por URL según decisión expresa de Carlos; las escrituras siguen mediadas por API. Aún falta validar Render y llevar el cliente al firmware.

Para nuevas sesiones usar el estado actual de Git, definición, estado y plan, sin depender de esta conversación. La documentación de endpoints tiene que cambiar junto a su código.
