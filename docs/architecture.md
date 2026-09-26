# Arquitectura

`src/data/bank.json` conserva el texto literal, respuesta oficial, procedencia, tema y estado de las 675 preguntas importadas. La migración `20260926160100_seed_tai_catalog.sql` carga esa versión en Postgres; la web consulta `tai_catalog` al iniciar. `src/data/manual-classifications.json` registra 102 decisiones humanas individuales para impedir que una reconstrucción vuelva a asignarlas con el algoritmo.

El progreso personal no se almacena como estado canónico del navegador. Tras entrar por correo con Supabase Auth, la aplicación consulta `tai_attempts` y `tai_question_progress` en Postgres. Un test se guarda de forma transaccional con `tai_record_attempt`; `tai_toggle_favorite` actualiza favoritos sin condiciones de carrera. RLS limita lecturas a la cuenta autenticada. Al volver a enfocar la web se consulta la base de datos para reflejar cambios de otro dispositivo.

Cada resultado usa puntuación directa: aciertos menos errores/3. La transformación oficial depende de los baremos y cortes publicados por la Comisión Permanente de Selección.

`reports/import-examenes-reales.md` contiene cobertura y decisiones de clasificación. Las preguntas duplicadas o desactualizadas permanecen consultables, pero fuera de los tests normales.
