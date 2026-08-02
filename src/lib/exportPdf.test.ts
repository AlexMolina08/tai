import { describe, expect, it } from 'vitest'
import { buildExamPdf, buildSolutionsPdf } from './exportPdf'
import type { Question, TestSpec } from '../types'

const spec: TestSpec = { id: 'test', title: 'Prueba PDF', mode: 'custom', questionIds: ['q1'], createdAt: '2026-08-01' }
const question: Question = {
  id: 'q1', examId: 'e1', year: 2025, access: 'libre', sitting: 'ordinario', exercise: 'primera_parte',
  section: 'first', isReserve: false, originalNumber: 1, prompt: '¿Cuál es la opción correcta?',
  options: ['Opción A', 'Opción B', 'Opción C', 'Opción D'], correctAnswer: 'b', answerStatus: 'oficial',
  blockId: 'I', topicId: 'I.1', classificationConfidence: 1, status: 'valid', statusReason: '', active: true,
  duplicateOf: null, source: { pdf: 'examen.pdf', page: 2, answerPdf: 'respuestas.pdf' },
}

describe('exportación PDF', () => {
  it('crea el simulacro y las soluciones como PDF válidos', () => {
    const exam = buildExamPdf(spec, [question])
    const solutions = buildSolutionsPdf(spec, [question], { q1: 'a' })
    expect(new Uint8Array(exam.output('arraybuffer')).slice(0, 4)).toEqual(new Uint8Array([37, 80, 68, 70]))
    expect(new Uint8Array(solutions.output('arraybuffer')).slice(0, 4)).toEqual(new Uint8Array([37, 80, 68, 70]))
    expect(exam.getNumberOfPages()).toBeGreaterThanOrEqual(2)
    expect(solutions.getNumberOfPages()).toBe(1)
  })
})
