# Despliegue

GitHub Pages publica `main` mediante `.github/workflows/deploy-pages.yml`. El banco de 675 preguntas se carga en `tai_catalog` mediante una migración versionada; `src/data/bank.json` es la fuente auditable para generar esa migración. La web lee el banco desde Supabase al abrirse y no ejecuta OCR en Pages.

El progreso vive en las tablas `tai_attempts` y `tai_question_progress` de Supabase (`bjuytltodzdcmnoichgp`). La migración versionada se aplica al proyecto autorizado y habilita RLS: cada usuario autenticado solo lee sus propias filas. Los cambios de test y favoritos se hacen con funciones transaccionales. Las funciones no aceptan un `user_id` del navegador.

Para la publicación se configura en GitHub Actions la variable pública `VITE_SUPABASE_PUBLISHABLE_KEY` del proyecto. La URL ya está fijada en el flujo de compilación. En Supabase Auth hay que permitir `https://alexmolina08.github.io/tai/` como URL de redirección de enlaces por correo. La web muestra un error de configuración si se compila sin clave.

No se guardan contraseñas ni claves de administración en el repositorio. Las copias JSON se pueden exportar o importar de forma excepcional; el uso diario lee y escribe directamente en Postgres.
