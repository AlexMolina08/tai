import Dexie, { type EntityTable } from 'dexie'
import type { Answer, AttemptRecord, Question, QuestionProgress } from '../types'

const LOCAL_UPDATED_AT_KEY = 'tai-age-progress-updated-at'

export interface ProgressSnapshot {
  schemaVersion: 1
  exportedAt: string
  attempts: AttemptRecord[]
  progress: QuestionProgress[]
}

export const db = new Dexie('tai-age-preparador') as Dexie & {
  attempts: EntityTable<AttemptRecord, 'id'>
  progress: EntityTable<QuestionProgress, 'questionId'>
}

db.version(1).stores({
  attempts: 'id, finishedAt, mode',
  progress: 'questionId, wrong, favorite, lastSeenAt',
})

export async function saveAttempt(attempt: AttemptRecord): Promise<void> {
  await db.transaction('rw', db.attempts, db.progress, async () => {
    await db.attempts.put(attempt)
    for (const questionId of attempt.questionIds) {
      const previous = await db.progress.get(questionId)
      const answer = attempt.answers[questionId]
      const questionResult = Object.entries(attempt.result.byTopic)
      void questionResult
      await db.progress.put({
        questionId,
        seen: (previous?.seen ?? 0) + 1,
        correct: (previous?.correct ?? 0),
        wrong: (previous?.wrong ?? 0),
        favorite: previous?.favorite ?? false,
        lastSeenAt: attempt.finishedAt,
      })
      void answer
    }
  })
  markLocalProgressChanged()
}

export async function applyQuestionOutcomes(
  questions: Question[],
  answers: Record<string, Answer>,
): Promise<void> {
  await db.transaction('rw', db.progress, async () => {
    for (const question of questions) {
      const previous = await db.progress.get(question.id)
      const answer = answers[question.id]
      await db.progress.put({
        questionId: question.id,
        seen: Math.max(1, previous?.seen ?? 0),
        correct: (previous?.correct ?? 0) + (answer === question.correctAnswer ? 1 : 0),
        wrong: (previous?.wrong ?? 0) + (answer && answer !== question.correctAnswer ? 1 : 0),
        favorite: previous?.favorite ?? false,
        lastSeenAt: new Date().toISOString(),
      })
    }
  })
  markLocalProgressChanged()
}

export async function toggleFavorite(questionId: string): Promise<boolean> {
  const previous = await db.progress.get(questionId)
  const favorite = !(previous?.favorite ?? false)
  await db.progress.put({
    questionId,
    seen: previous?.seen ?? 0,
    correct: previous?.correct ?? 0,
    wrong: previous?.wrong ?? 0,
    favorite,
    lastSeenAt: new Date().toISOString(),
  })
  markLocalProgressChanged()
  return favorite
}

export async function getProgressSnapshot(): Promise<ProgressSnapshot> {
  return {
    schemaVersion: 1,
    exportedAt: new Date().toISOString(),
    attempts: await db.attempts.toArray(),
    progress: await db.progress.toArray(),
  }
}

export async function exportProgress(): Promise<string> {
  return JSON.stringify(await getProgressSnapshot(), null, 2)
}

export async function replaceProgressSnapshot(parsed: ProgressSnapshot, updatedAt = new Date().toISOString()): Promise<void> {
  if (parsed.schemaVersion !== 1 || !Array.isArray(parsed.attempts) || !Array.isArray(parsed.progress)) {
    throw new Error('El archivo no es una copia de progreso compatible.')
  }
  await db.transaction('rw', db.attempts, db.progress, async () => {
    await db.attempts.clear()
    await db.progress.clear()
    await db.attempts.bulkPut(parsed.attempts)
    await db.progress.bulkPut(parsed.progress)
  })
  localStorage.setItem(LOCAL_UPDATED_AT_KEY, updatedAt)
}

export async function importProgress(raw: string): Promise<void> {
  await replaceProgressSnapshot(JSON.parse(raw) as ProgressSnapshot)
}

export function markLocalProgressChanged(at = new Date().toISOString()): void {
  localStorage.setItem(LOCAL_UPDATED_AT_KEY, at)
}

export async function getLocalProgressUpdatedAt(): Promise<string> {
  const stored = localStorage.getItem(LOCAL_UPDATED_AT_KEY)
  if (stored) return stored
  const [attempt, progress] = await Promise.all([
    db.attempts.orderBy('finishedAt').last(),
    db.progress.orderBy('lastSeenAt').last(),
  ])
  return [attempt?.finishedAt, progress?.lastSeenAt].filter(Boolean).sort().at(-1) ?? '1970-01-01T00:00:00.000Z'
}
