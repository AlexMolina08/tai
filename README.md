# Preparador TAI AGE

Aplicación para practicar con 675 preguntas de cinco exámenes oficiales de 2019, 2023, 2024 y 2025. Hay 670 preguntas utilizables y 5 conservadas fuera de los tests. Las 102 preguntas que estaban en `classification_review` se revisaron una a una; cada asignación y su motivo figuran en `src/data/manual-classifications.json` y `reports/import-examenes-reales.md`.

## Uso

La web se publica en https://alexmolina08.github.io/tai/. El acceso por correo usa Supabase Auth. La web lee el banco oficial de Postgres; tests, resultados y favoritos también se guardan directamente allí y se muestran en cualquier dispositivo donde se acceda con el mismo correo. La descarga JSON es solo una copia de seguridad; no hace falta sincronizar manualmente.

En **Fuentes** se pueden subir archivos JSON con preguntas de estudio ajenas a los exámenes. Se validan y guardan en la cuenta de Supabase, y se pueden practicar en tests personalizados. El formato y un ejemplo están en [`docs/uploaded-sources.md`](docs/uploaded-sources.md).

## Desarrollo

```sh
npm ci
cp .env.example .env.local
npm run dev
npm test
npm run build
```

La clave pública del proyecto es segura para incluirla en el frontend. Nunca se usa una clave `service_role` en la web. La migración de base de datos está en `supabase/migrations/`. En GitHub Actions, la variable `VITE_SUPABASE_PUBLISHABLE_KEY` permite la compilación de Pages.

Para reconstruir la importación de las cinco convocatorias de `EXAMENES REALES/`, ejecuta `python3 scripts/import_examenes_reales.py`. Las 102 clasificaciones manuales se aplican antes de la clasificación automática. No ejecuta OCR ni modifica los PDF originales.
