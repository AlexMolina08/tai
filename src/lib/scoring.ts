import type { Answer, Question, TestResult } from '../types'

export function scoreTest(questions: Question[], answers: Record<string, Answer>, penalty = 1 / 3): TestResult {
  let correct = 0
  let wrong = 0
  let blank = 0
  const byTopic: TestResult['byTopic'] = {}

  for (const question of questions) {
    const topic = byTopic[question.topicId] ?? { correct: 0, wrong: 0, blank: 0 }
    const answer = answers[question.id]
    if (!answer) {
      blank += 1
      topic.blank += 1
    } else if (answer === question.correctAnswer) {
      correct += 1
      topic.correct += 1
    } else {
      wrong += 1
      topic.wrong += 1
    }
    byTopic[question.topicId] = topic
  }

  const rawScore = correct - wrong * penalty
  return {
    correct,
    wrong,
    blank,
    rawScore,
    maximumRaw: questions.length,
    percentage: questions.length ? (rawScore / questions.length) * 100 : 0,
    byTopic,
  }
}

export function formatScore(value: number): string {
  return new Intl.NumberFormat('es-ES', { maximumFractionDigits: 2, minimumFractionDigits: 2 }).format(value)
}
