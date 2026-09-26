# Contexto de trabajo: Preparador TAI AGE

## Estado actual

- Repositorio: `AlexMolina08/tai`. Web publicada: <https://alexmolina08.github.io/tai/>. La rama `main` se despliega con `.github/workflows/deploy-pages.yml`.
- Aplicación React, TypeScript y Vite. Los scripts Python importan y verifican las preguntas. Consulta `README.md` y `docs/` para los detalles de uso.
- Supabase autorizado por el usuario: proyecto `bjuytltodzdcmnoichgp` en `eu-central-1`. La web requiere acceso por correo mediante Supabase Auth.
- A 2026-09-26, la importación de cinco exámenes oficiales de 2019, 2023, 2024 y 2025 contiene 675 preguntas: 670 activas y 5 excluidas. Son cifras de referencia, no objetivos fijos; vuelve a calcularlas cuando cambie el banco.

## Fuentes y clasificación

- Las transcripciones de los exámenes reales están fuera del repositorio, en `~/Desktop/TAI — Temas y tests/EXAMENES REALES/`. El importador correspondiente es `scripts/import_examenes_reales.py`; el banco auditable resultante es `src/data/bank.json`.
- El programa de bloques y temas está en `src/data/program.json`. La convocatoria de referencia está en `TAILI.pdf`; los PDF de `TAI AGE/` son fuentes originales locales y no se publican.
- `src/data/manual-classifications.json` registra las 102 preguntas de `classification_review` revisadas individualmente en 2026-09-26, con tema y motivo. El importador aplica esas decisiones antes de su clasificador automático. No sustituyas una decisión humana por la salida del algoritmo.
- Para nuevas preguntas dudosas, lee enunciado, cuatro opciones, respuesta y convocatoria. Contrasta el programa y la fuente oficial pertinente. No fuerces un tema ni actives una pregunta cuya clasificación, respuesta o vigencia no esté clara: déjala en revisión con un motivo concreto.
- Conserva literalmente el enunciado, las opciones, la respuesta oficial y la procedencia. No modernices preguntas antiguas en silencio. Mantén anuladas, duplicadas, desactualizadas y ambiguas fuera de los tests normales, pero trazables en los informes.
- Antes de aceptar una importación, verifica recuentos por sección, cuatro opciones no vacías, correspondencia literal con la plantilla y estados de exclusión. Revisa `reports/import-examenes-reales.md` y `reports/excluded-examenes-reales.json`.

## Datos y Supabase

- La base de datos es la fuente de verdad tanto del banco como del progreso. `src/lib/storage.ts` lee `tai_catalog` y las tablas personales `tai_attempts` y `tai_question_progress`; los tests y favoritos se escriben mediante las funciones SQL del proyecto. No reintroduzcas un progreso canónico en IndexedDB ni una sincronización manual.
- `src/lib/legacyProgress.ts` solo lee el progreso local antiguo para una posible importación única a una cuenta vacía. No borra esa copia local. El antiguo `tai_progress_snapshots`/`tai_sync_progress` permanece por compatibilidad histórica, pero ya no es el flujo de uso.
- Las migraciones versionadas están en `supabase/migrations/`: esquema/RLS en `20260926160000_tai_account_progress.sql` y catálogo en `20260926160100_seed_tai_catalog.sql`. Si cambias `src/data/bank.json`, actualiza también la carga SQL del catálogo; un cambio local del JSON por sí solo no llega a la web publicada.
- Aplica cambios remotos **solo** al proyecto autorizado, conserva las migraciones en Git y verifica el resultado en la base remota. Comprueba las políticas RLS y que cada cuenta solo pueda leer su progreso. No uses una clave `service_role` en el cliente ni guardes secretos en el repositorio.
- `.env.local` contiene configuración local ignorada por Git. GitHub Actions usa la variable pública `VITE_SUPABASE_PUBLISHABLE_KEY`; la URL del proyecto está en el flujo de despliegue. Supabase Auth permite redirigir a la URL publicada.
- La cuenta CLI de Supabase de este Mac ha apuntado antes a otra cuenta. Confirma el proyecto y la autenticación antes de cualquier operación CLI remota. Las migraciones de septiembre de 2026 se aplicaron mediante el editor SQL del proyecto; no des por hecho que su tabla de historial de migraciones esté registrada.

## Trabajo y comprobaciones

- Inicio rápido: `npm ci`, configura `.env.local` a partir de `.env.example` y ejecuta `make dev`.
- Ejecuta `make test` y `make build` tras cambios en la app o los datos. `make test` incluye pruebas Python y Vitest.
- Para reconstruir **solo** los cinco exámenes reales, usa `python3 scripts/import_examenes_reales.py` y revisa el informe generado. Para el banco de PDF/OCR de `TAI AGE/`, usa `make build-bank` solo si han cambiado esas fuentes: es un proceso más costoso y distinto del importador de exámenes reales.
- Antes de publicar, verifica que el banco local, la carga `tai_catalog`, las migraciones y la aplicación desplegada coinciden. El despliegue de Pages se activa al enviar cambios a `main`; comprueba su resultado y una lectura real desde la web.
- `project_instructions.md` documenta el encargo inicial, cuando la aplicación era local y aún no se había configurado GitHub ni Supabase. Para el estado actual prevalecen las peticiones posteriores del usuario, este archivo y el código comprobado.
