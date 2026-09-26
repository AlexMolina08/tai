# Archivos de preguntas añadidas

En **Fuentes → Elegir archivo JSON** se puede cargar material de estudio que no procede de exámenes oficiales. La página muestra una vista previa y, al pulsar **Guardar fuente en Supabase**, almacena las preguntas en la cuenta. El mismo material aparece al iniciar sesión en otro dispositivo. En **Preguntas** se puede filtrar por «Fuentes añadidas»; en **Nuevo test → Personalizado → Origen**, elegir «Solo mis fuentes». Estas preguntas no entran en los simulacros oficiales ni en los exámenes históricos.

El archivo debe ser UTF-8, terminar en `.json` y ocupar como máximo 1 MB. Admite entre 1 y 200 preguntas. Descarga una plantilla desde la propia página o utiliza este ejemplo:

```json
{
  "schemaVersion": 1,
  "sourceId": "tecnologia-basica-01",
  "title": "Tecnología básica · lote 1",
  "questions": [
    {
      "id": "bits-byte",
      "topicId": "II.1",
      "prompt": "¿Cuántos bits tiene un byte?",
      "options": ["4 bits", "8 bits", "16 bits", "32 bits"],
      "correctAnswer": "b",
      "explanation": "Un byte agrupa ocho bits.",
      "sourceNote": "Apuntes de tecnología básica"
    }
  ]
}
```

`sourceId` identifica el lote y `id` identifica cada pregunta dentro de él. Usa solo minúsculas, números y guiones. Mantén estos identificadores estables cuando corrijas un archivo: al volver a subir el mismo `sourceId`, se reemplaza su contenido y el progreso asociado a los `id` que sigan presentes se conserva. Para un lote nuevo, utiliza otro `sourceId`.

`topicId` debe existir en `src/data/program.json`; **no se clasifica automáticamente**. `options` lleva exactamente cuatro textos en orden A, B, C y D. `correctAnswer` es la letra minúscula `a`, `b`, `c` o `d`. `explanation` y `sourceNote` son opcionales. Antes de guardar, la persona que genera el archivo debe comparar las preguntas con `src/data/bank.json` para evitar repetir exámenes, verificar el tema, la exactitud de la respuesta y la referencia. La validación de la web comprueba la estructura, no la verdad de las afirmaciones ni los duplicados conceptuales.

Los archivos se guardan como fuentes personales en `tai_user_sources`, separados del catálogo oficial `tai_catalog`. La web no almacena un PDF adjunto: conserva el contenido estructurado del JSON en Postgres.
