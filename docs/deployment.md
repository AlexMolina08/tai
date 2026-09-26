# Despliegue

GitHub Pages publica la compilación de main mediante .github/workflows/deploy-pages.yml. El build usa src/data/bank.json, que actualmente contiene 0 preguntas, 0 exámenes y 0 documentos inventariados.

No se inyectan variables de Supabase ni se ejecuta la reconstrucción del banco durante el despliegue. GitHub Pages sirve la web estática. Cuando haya preguntas, el progreso se guardará localmente y el usuario podrá exportarlo e importarlo como JSON para usarlo en otro dispositivo.
