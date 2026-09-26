# Añadir un examen

1. Guarda el cuestionario y la plantilla en `TAI AGE/` sin cambiar los documentos existentes.
2. Añade una entrada en `scripts/exam_manifest.py` con identificador, año, vía, cuestionarios, secciones, recuentos y plantilla.
3. Si el formato de secciones o la plantilla difiere, crea un importador específico. No adaptes un parser hasta que “parezca funcionar”: valida cantidades y claves exactas.
4. Ejecuta:

```bash
make build-bank
make test
```

5. Comprueba en `reports/final-report.md`:

- número esperado por sección;
- reservas y anuladas;
- relación con la plantilla;
- páginas y procedencia;
- duplicados;
- clasificación y cola de vigencia.

6. Abre la web, filtra por el examen y realiza una prueba completa.

## Contrato mínimo de importación

Una pregunta solo puede entrar en el banco si conserva:

- texto literal y cuatro opciones completas;
- respuesta de plantilla oficial;
- examen, año, vía y convocatoria;
- parte, supuesto o bloque y condición de reserva;
- número original, PDF y página;
- bloque y tema del programa vigente;
- estado de vigencia y motivo si se excluye.

## Escaneos

Ejecuta primero `.venv/bin/python scripts/ocr_sources.py`. El OCR se guarda en `tmp/ocr/`; los PDF originales siguen intactos. Una pregunta con ruido, opciones incompletas o recuento sin cerrar no puede entrar en el banco vigente.

## Recopilaciones temáticas aportadas

Cuando una fuente de terceros no deba publicarse, conserva en `sources/` únicamente la transcripción necesaria, la huella SHA-256, el número de página y la plantilla de respuestas. El importador debe:

- reutilizar las preguntas ya presentes en exámenes oficiales;
- registrar y omitir los duplicados internos;
- añadir solo las preguntas realmente ausentes;
- contrastar la vigencia con fuentes oficiales;
- mantener fuera del banco activo cualquier enunciado temporal u obsoleto;
- inventariar la fuente sin incluir el PDF original en el repositorio público.

No hay recopilaciones temáticas cargadas en la versión vacía del preparador.
