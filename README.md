# Preparador TAI AGE

Frontend del preparador TAI. El banco está vacío: **0 preguntas, 0 exámenes y 0 documentos inventariados**. Se conserva la estructura de 33 temas y el diseño de la aplicación para incorporar preguntas después.

## Abrir en local

    npm ci
    npm run dev

## Comprobar y compilar

    npm test
    npm run build

El build y el despliegue de GitHub Pages usan el banco vacío de src/data/bank.json. No ejecutan OCR ni reconstruyen preguntas. Los PDF originales de TAI AGE/ y TAILI.pdf se conservan como material fuente; no forman parte de la web publicada. El procesamiento de fuentes solo se ejecuta expresamente con make build-bank cuando se decida cargar preguntas nuevas.

Al abrir esta versión, se elimina el progreso antiguo almacenado en ese navegador. El proyecto ya no usa Supabase. Cuando haya preguntas, el progreso quedará en el navegador y se podrá exportar e importar como JSON para trasladarlo entre dispositivos. La publicación en GitHub Pages se hace desde main mediante .github/workflows/deploy-pages.yml.
