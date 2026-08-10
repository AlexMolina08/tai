# Preparador local TAI AGE

Aplicación web local para estudiar preguntas oficiales del Cuerpo de Técnicos Auxiliares de Informática de la AGE. El temario y el formato vigente proceden de `TAILI.pdf`, indicado como referencia oficial del proyecto.

## Puesta en marcha

Requisitos: macOS o Linux, Python 3.11 o posterior, Node.js 20.19 o posterior y Poppler (`pdftotext`, `pdfinfo`).

```bash
make bootstrap
make build-bank
make dev
```

La aplicación queda disponible en `http://localhost:5173`.

## Comandos

```bash
make bootstrap    # crea .venv e instala dependencias Python y web
make build-bank   # reconstruye JSON, SQLite e informes desde los PDF
make dev          # abre inmediatamente el servidor local
make test         # pruebas del pipeline, puntuación y web
make build        # genera la web estática en dist/
```

`make build-bank` solo es necesario cuando se añaden o cambian PDF. El banco generado está incluido en el proyecto, por lo que el arranque diario no repite el OCR.

## Qué incluye

- Panel de actividad y estadísticas.
- Explorador con filtros por bloque, tema, año, vía, estado y texto.
- Test personalizados, nunca vistas, falladas y favoritas.
- Simulacro vigente de 80 + 5 y 20 + 5 preguntas, con 120 minutos.
- Exámenes históricos desde 2005, incluidos ingreso libre, promoción interna, supuestos, reservas y anulaciones cuando constan en la recopilación.
- Respuestas ocultas, blancos, marcas de revisión y corrección por tema.
- Puntuación directa `aciertos - errores/3`; la aplicación no inventa la transformación oficial de la CPS.
- Historial y progreso en IndexedDB, con exportación e importación JSON.
- Sincronización opcional del progreso entre dispositivos mediante Supabase y un código personal.
- Exportación del simulacro PDF, soluciones PDF y ZIP con ambos.
- Inventario de todos los documentos, cola de revisión y banco SQLite.

## Estado del banco (10 de agosto de 2026)

- 3.520 preguntas localizadas y trazadas: 3.500 proceden de los 24 exámenes lógicos y 20 son preguntas únicas añadidas desde una recopilación temática aportada.
- 2.129 preguntas en el banco activo, con respuesta enlazada, clasificación suficientemente sólida y extracción sin señales de mezcla.
- La recopilación del Tema I.9 contiene 35 preguntas: 13 ya estaban en el banco, 20 eran nuevas y 2 repetían literalmente otras preguntas del mismo PDF.
- 895 clasificaciones conservadas en revisión y 169 extracciones OCR aisladas para control humano. No entran en tests ni simulacros.
- 66 preguntas del segundo ejercicio de 2017 se conservan sin activar porque la recopilación no incluye su plantilla oficial.

Una pregunta pendiente sigue teniendo un tema candidato y su procedencia, pero la aplicación no lo presenta como validado. La cola completa está en `reports/review-queue.json`.

## Política de datos

`TAI AGE/` está ignorada por Git y se utiliza únicamente como fuente. El pipeline calcula huellas SHA-256, pero no escribe, mueve ni renombra ningún PDF.

El banco vigente solo usa preguntas con cuatro opciones, respuesta enlazada, clasificación suficiente y ninguna señal expresa de obsolescencia. Las anuladas, duplicadas, desactualizadas o pendientes no se borran: quedan visibles en el explorador y en `reports/review-queue.json` con su motivo. Los exámenes históricos ejecutables usan únicamente el subconjunto validado.

Los escaneos se procesan en una copia temporal bajo `tmp/ocr/`, nunca sobre la fuente. El pipeline combina OCR en español, posición de líneas y cotejo de recuentos con la plantilla. `reports/coverage-matrix.json` identifica cualquier número que no se haya podido cerrar.

## Estructura

```text
scripts/              extracción, clasificación y validación
src/data/             banco JSON, programa y SQLite generados
src/lib/              puntuación, IndexedDB y exportación PDF/ZIP
reports/              inventario, cola de revisión e informe final
output/pdf/           muestras verificadas de simulacro y soluciones
output/zip/           muestra verificada del paquete ZIP
docs/                 arquitectura y guía para nuevos exámenes
```

Consulta [docs/architecture.md](docs/architecture.md) y [docs/adding-exams.md](docs/adding-exams.md) para ampliar el proyecto.

La publicación en GitHub Pages y la sincronización con Supabase se documentan en [docs/deployment.md](docs/deployment.md).
