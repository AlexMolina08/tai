import type { Bank, Question, SavedSource, UploadedQuestion, UploadedSource } from '../types'

const idPattern = /^[a-z0-9][a-z0-9-]{0,79}$/
const answers = new Set(['a', 'b', 'c', 'd'])

function object(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function requiredText(value: unknown, label: string, max: number): string {
  if (typeof value !== 'string' || !value.trim() || value.length > max) {
    throw new Error(`${label}: escribe un texto de 1 a ${max} caracteres.`)
  }
  return value.trim()
}

export function parseUploadedSource(raw: string, program: Bank['program']): UploadedSource {
  let data: unknown
  try { data = JSON.parse(raw) } catch { throw new Error('El archivo no contiene un JSON válido.') }
  if (!object(data) || data.schemaVersion !== 1) throw new Error('El archivo debe usar schemaVersion: 1.')
  const sourceId = requiredText(data.sourceId, 'sourceId', 80)
  if (!idPattern.test(sourceId)) throw new Error('sourceId: usa solo letras minúsculas, números y guiones.')
  const title = requiredText(data.title, 'title', 160)
  if (!Array.isArray(data.questions) || !data.questions.length || data.questions.length > 200) {
    throw new Error('El archivo debe contener entre 1 y 200 preguntas.')
  }
  const topics = new Set(program.flatMap(block => block.topics.map(topic => topic.id)))
  const ids = new Set<string>()
  const questions: UploadedQuestion[] = data.questions.map((item: unknown, index: number) => {
    const label = `Pregunta ${index + 1}`
    if (!object(item)) throw new Error(`${label}: formato incorrecto.`)
    const id = requiredText(item.id, `${label}, id`, 80)
    if (!idPattern.test(id)) throw new Error(`${label}: el id solo admite letras minúsculas, números y guiones.`)
    if (ids.has(id)) throw new Error(`${label}: el id ${id} está repetido.`)
    ids.add(id)
    const topicId = requiredText(item.topicId, `${label}, topicId`, 12)
    if (!topics.has(topicId)) throw new Error(`${label}: ${topicId} no existe en el temario.`)
    const prompt = requiredText(item.prompt, `${label}, prompt`, 3000)
    if (!Array.isArray(item.options) || item.options.length !== 4) {
      throw new Error(`${label}: debe tener cuatro opciones en orden A, B, C y D.`)
    }
    const options = item.options.map((option, optionIndex) => requiredText(option, `${label}, opción ${'ABCD'[optionIndex]}`, 1500)) as UploadedQuestion['options']
    if (!answers.has(item.correctAnswer as string)) throw new Error(`${label}: correctAnswer debe ser a, b, c o d.`)
    const explanation = item.explanation === undefined ? undefined : requiredText(item.explanation, `${label}, explanation`, 3000)
    const sourceNote = item.sourceNote === undefined ? undefined : requiredText(item.sourceNote, `${label}, sourceNote`, 500)
    return { id, topicId, prompt, options, correctAnswer: item.correctAnswer as UploadedQuestion['correctAnswer'], ...(explanation ? { explanation } : {}), ...(sourceNote ? { sourceNote } : {}) }
  })
  return { schemaVersion: 1, sourceId, title, questions }
}

export function sourceQuestions(saved: SavedSource, program: Bank['program']): Question[] {
  const source = saved.source
  const blocks = new Map(program.flatMap(block => block.topics.map(topic => [topic.id, block.id] as const)))
  const year = new Date(saved.uploadedAt).getFullYear()
  return source.questions.map((item, index) => ({
    id: `uploaded:${source.sourceId}:${item.id}`,
    examId: `uploaded:${source.sourceId}`,
    year,
    access: 'libre',
    sitting: 'Fuente añadida',
    exercise: 'practice',
    section: 'uploaded',
    isReserve: false,
    originalNumber: index + 1,
    prompt: item.prompt,
    options: item.options,
    correctAnswer: item.correctAnswer,
    answerStatus: 'respuesta_aportada',
    blockId: blocks.get(item.topicId) ?? '',
    topicId: item.topicId,
    classificationConfidence: 1,
    classificationMethod: 'tema_indicado_en_archivo',
    status: 'valid',
    statusReason: 'Pregunta añadida por el usuario; no pertenece a un examen oficial.',
    active: true,
    duplicateOf: null,
    source: { pdf: source.title, page: 0, answerPdf: null, extraction: 'archivo_json' },
    origin: 'uploaded',
    explanation: item.explanation,
    sourceNote: item.sourceNote,
  }))
}
