# Arquitectura y decisiones

## Flujo de datos

1. `scripts/ocr_sources.py` detecta cuestionarios históricos complejos y crea copias OCR temporales en español, con coordenadas por palabra.
2. `scripts/build_bank.py` inventaría los PDF sin modificarlos y extrae pregunta, cuatro opciones, sección, reserva, número y página.
3. `scripts/answer_templates.py` lee la plantilla por columnas y la relaciona mediante `(sección, número original)`; los recuentos deben coincidir exactamente.
4. Cada pregunta recibe bloque, tema, confianza, vigencia, motivo y estado activo/inactivo.
5. Se detectan duplicados por texto normalizado.
6. Se generan `bank.json`, `program.json`, `bank.sqlite` y los informes.
7. Vite empaqueta el banco con la web estática. IndexedDB conserva únicamente el progreso del usuario.

## Modelo de examen vigente

- Primera parte: máximo 80 preguntas y 5 reservas.
- Segunda parte: un supuesto a elegir de los bloques III o IV, con 20 preguntas y 5 reservas.
- Duración total: 120 minutos.
- Error: resta un tercio del valor de un acierto.
- Blanco: no penaliza.
- Calificación: cada parte se transforma a 0-50 según los baremos y cortes publicados por la Comisión Permanente de Selección.

Por este último punto la interfaz muestra la puntuación directa exacta y una proporción orientativa, pero no la denomina “nota oficial”.

## Estados de pregunta

- `valid`: utilizable en test normales.
- `classification_review`: clasificación conservada, pero fuera del banco vigente por baja confianza.
- `missing_official_answer`: no existe plantilla en la recopilación.
- `ocr_review`: la transcripción contiene una señal de ruido OCR.
- `outdated`: referencia detectada como derogada u obsoleta.
- `annulled`: anulada por la plantilla oficial.
- `duplicate`: mismo enunciado que otra pregunta conservada.
- `outdated`: contiene una referencia normativa expresamente derogada.

## Privacidad

No hay servidor de aplicación, telemetría, cuentas ni sincronización. La web funciona íntegramente en el navegador. Exportar el progreso crea un JSON que el usuario puede guardar e importar en otro dispositivo.

## Cobertura

`reports/coverage-matrix.json` compara por examen el número esperado, extraído y enlazado. La validación comprueba además que cada página de procedencia exista y que ninguna pregunta activa carezca de respuesta o tema.
