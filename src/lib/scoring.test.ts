import { describe, expect, it } from 'vitest'
import { scoreTest } from './scoring'
import type { Question } from '../types'

const question = (id: string, answer: 'a' | 'b'): Question => ({
  id, examId: 'x', year: 2025, access: 'libre', sitting: 'ordinario', exercise: 'primera_parte',
  section: 'first', isReserve: false, originalNumber: 1, prompt: id, options: ['1', '2', '3', '4'],
  correctAnswer: answer, answerStatus: 'oficial', blockId: 'I', topicId: 'I.1', classificationConfidence: 1,
  status: 'valid', statusReason: '', active: true, duplicateOf: null,
  source: { pdf: 'a.pdf', page: 1, answerPdf: 'b.pdf' },
})

describe('scoreTest', () => {
  it('aplica un tercio por error y no penaliza blancos', () => {
    const result = scoreTest([question('1', 'a'), question('2', 'b'), question('3', 'a')], { '1': 'a', '2': 'a' })
    expect(result.correct).toBe(1)
    expect(result.wrong).toBe(1)
    expect(result.blank).toBe(1)
    expect(result.rawScore).toBeCloseTo(2 / 3)
  })
})
