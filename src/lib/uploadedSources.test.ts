import { describe, expect, it } from 'vitest'
import type { Bank } from '../types'
import { parseUploadedSource, sourceQuestions } from './uploadedSources'

const program: Bank['program'] = [{ id: 'II', name: 'Tecnología básica', topics: [{ id: 'II.1', name: 'Informática básica' }] }]
const valid = {
  schemaVersion: 1,
  sourceId: 'lote-01',
  title: 'Preguntas nuevas',
  questions: [{ id: 'byte', topicId: 'II.1', prompt: '¿Cuántos bits tiene un byte?', options: ['4', '8', '16', '32'], correctAnswer: 'b' }],
}

describe('archivos de fuentes añadidas', () => {
  it('valida y convierte preguntas sin presentarlas como examen oficial', () => {
    const source = parseUploadedSource(JSON.stringify(valid), program)
    const [question] = sourceQuestions({ source, uploadedAt: '2026-09-26T12:00:00Z' }, program)
    expect(question.id).toBe('uploaded:lote-01:byte')
    expect(question.blockId).toBe('II')
    expect(question.correctAnswer).toBe('b')
    expect(question.origin).toBe('uploaded')
    expect(question.section).toBe('uploaded')
    expect(question.active).toBe(true)
  })

  it('rechaza temas desconocidos, opciones incompletas e identificadores repetidos', () => {
    expect(() => parseUploadedSource(JSON.stringify({ ...valid, questions: [{ ...valid.questions[0], topicId: 'V.9' }] }), program)).toThrow('no existe')
    expect(() => parseUploadedSource(JSON.stringify({ ...valid, questions: [{ ...valid.questions[0], options: ['1', '2', '3'] }] }), program)).toThrow('cuatro opciones')
    expect(() => parseUploadedSource(JSON.stringify({ ...valid, questions: [valid.questions[0], valid.questions[0]] }), program)).toThrow('repetido')
  })
})
