Objetivo

Debes crear de forma autónoma una aplicación web local que permita estudiar mediante las preguntas oficiales de los exámenes anteriores.

El proyecto debe:

1. Inventariar todos los PDF y detectar cuáles contienen cuestionarios, respuestas, varios ejercicios o documentos recopilatorios.
2. Extraer literalmente las preguntas, opciones y respuestas oficiales.
3. Relacionar correctamente cada cuestionario con su plantilla.
4. Detectar preguntas anuladas, reservas y duplicados.
5. Clasificar cada pregunta por bloque y tema conforme al programa vigente.
6. Comprobar si cada pregunta sigue siendo válida actualmente.
7. Excluir del banco utilizable las preguntas desactualizadas, fuera del temario, anuladas, duplicadas, ambiguas o cuya respuesta ya no sea correcta.
8. Conservar la procedencia de cada pregunta: examen, año, vía de acceso, ejercicio, número original, PDF y página.
9. Construir una aplicación web completa para practicar.
10. Dejar el proyecto probado, documentado y funcionando en local.

La clasificación temática y la vigencia de las preguntas son especialmente importantes. No fuerces una pregunta dentro de un tema si no corresponde. Cuando exista una duda que no puedas resolver con seguridad, exclúyela del banco activo y regístrala en un informe de revisión.

No reescribas ni modernices silenciosamente las preguntas antiguas. Conserva siempre el texto y la respuesta oficial originales. Si una pregunta ya no es válida hoy, no debe aparecer en los test normales.

Puedes consultar fuentes oficiales como BOE, INAP, EUR-Lex o documentación técnica oficial cuando necesites verificar la vigencia de una pregunta.

Aplicación web

La aplicación debe funcionar en ordenador y móvil y quedar preparada para publicarse más adelante como web estática en GitHub Pages, aunque por ahora solo debe ejecutarse en local.

Debe incluir:

* Panel inicial con estadísticas.
* Explorador de preguntas.
* Filtros por bloque, tema, año, examen, vía libre o promoción interna y texto.
* Generador de test seleccionando bloques, temas y número de preguntas.
* Simulacro conforme al formato de la convocatoria vigente.
* Posibilidad de realizar exámenes históricos.
* Respuestas ocultas hasta finalizar el test.
* Preguntas en blanco y marcadas para revisar.
* Corrección final con aciertos, errores, penalización, nota y resultados por tema.
* Historial local.
* Preguntas falladas, favoritas y nunca vistas.
* Repetición de errores.
* Exportación e importación del progreso.

El progreso puede almacenarse localmente en el navegador. No hace falta implementar cuentas ni sincronización entre dispositivos.

Exportación de exámenes

Desde un test debe poder generarse:

1. Un PDF de simulacro imprimible.
2. Un PDF separado con las soluciones.
3. Un ZIP con ambos.

Utiliza como referencia visual el examen más reciente de TAI AGE/2025, manteniendo un estilo y estructura similares, pero indicando claramente que se trata de un simulacro no oficial y sin copiar logotipos oficiales.

El PDF del examen debe incluir instrucciones, preguntas, reservas cuando corresponda y una hoja de respuestas. El de soluciones debe incluir la plantilla correcta, el tema y la procedencia de cada pregunta.

Tecnología y calidad

Elige una arquitectura razonable. Preferiblemente:

* Python para extracción y construcción del banco.
* JSON/JSONL y SQLite para los datos.
* TypeScript con React y Vite para la web.
* IndexedDB para el progreso.
* Pruebas automáticas para el procesamiento, la puntuación, la aplicación y los PDF.

Crea documentación suficiente para instalar, reconstruir los datos, ejecutar la web y añadir futuros exámenes.

Proporciona comandos sencillos, por ejemplo:

make bootstrap
make build-bank
make dev
make test
make build

Trabaja por fases y continúa de forma autónoma sin pedirme confirmación para decisiones normales. Solo pregunta si aparece un bloqueo externo que realmente impida continuar.

No configures todavía GitHub, un repositorio remoto ni GitHub Pages.

No consideres terminado el trabajo hasta que:

* Todos los PDF hayan sido revisados y tengan un estado.
* El banco de preguntas esté construido y validado.
* Las preguntas activas estén correctamente clasificadas y vigentes.
* Las preguntas excluidas tengan un motivo.
* La web funcione localmente.
* Los test y simulacros funcionen.
* Los dos PDF se generen correctamente.
* Las pruebas pasen.
* Exista un informe final con documentos procesados, preguntas extraídas, preguntas admitidas, preguntas excluidas y distribución por bloque y tema.

Empieza inspeccionando el repositorio, la convocatoria adjunta y la carpeta TAI AGE, planifica internamente el trabajo y procede hasta completar el proyecto.