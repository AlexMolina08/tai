import { createClient } from '@supabase/supabase-js'
import type { Answer, AttemptRecord, Bank, Question, QuestionProgress } from '../types'

const url = import.meta.env.VITE_SUPABASE_URL || 'https://bjuytltodzdcmnoichgp.supabase.co'
const key = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY

export const configured = Boolean(key)
export const supabase = configured ? createClient(url, key, {
  auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true },
}) : null

function client() {
  if (!supabase) throw new Error('Falta la clave pública de Supabase en el despliegue.')
  return supabase
}

export interface ProgressSnapshot {
  schemaVersion: 1
  exportedAt: string
  attempts: AttemptRecord[]
  progress: QuestionProgress[]
}

export async function loadBank(): Promise<Bank> {
  const { data, error } = await client().from('tai_catalog').select('payload').eq('id', 'official').single()
  if (error) throw error
  const bank = data?.payload as Bank | undefined
  if (!bank || !Array.isArray(bank.questions) || !Array.isArray(bank.program)) {
    throw new Error('El banco oficial no está cargado en Supabase.')
  }
  return bank
}

export async function loadProgress(): Promise<{ attempts: AttemptRecord[]; progress: QuestionProgress[] }> {
  const api = client()
  const [attemptRows, progressRows] = await Promise.all([
    api.from('tai_attempts').select('payload').order('finished_at', { ascending: false }),
    api.from('tai_question_progress').select('question_id,seen,correct,wrong,favorite,last_seen_at'),
  ])
  if (attemptRows.error) throw attemptRows.error
  if (progressRows.error) throw progressRows.error
  return {
    attempts: (attemptRows.data ?? []).map(row => row.payload as AttemptRecord),
    progress: (progressRows.data ?? []).map(row => ({
      questionId: row.question_id as string,
      seen: row.seen as number,
      correct: row.correct as number,
      wrong: row.wrong as number,
      favorite: row.favorite as boolean,
      lastSeenAt: row.last_seen_at as string | undefined,
    })),
  }
}

export async function recordAttempt(attempt: AttemptRecord, questions: Question[], answers: Record<string, Answer>): Promise<void> {
  const outcomes = questions.map(q => ({
    questionId: q.id,
    outcome: !answers[q.id] ? 'blank' : answers[q.id] === q.correctAnswer ? 'correct' : 'wrong',
  }))
  const { error } = await client().rpc('tai_record_attempt', { p_attempt: attempt, p_outcomes: outcomes })
  if (error) throw error
}

export async function toggleFavorite(questionId: string): Promise<boolean> {
  const { data, error } = await client().rpc('tai_toggle_favorite', { p_question_id: questionId })
  if (error) throw error
  return Boolean(data)
}

export async function exportProgress(): Promise<string> {
  const current = await loadProgress()
  return JSON.stringify({ schemaVersion: 1, exportedAt: new Date().toISOString(), ...current } satisfies ProgressSnapshot, null, 2)
}

export async function importProgress(raw: string): Promise<void> {
  const parsed = JSON.parse(raw) as ProgressSnapshot
  if (parsed.schemaVersion !== 1 || !Array.isArray(parsed.attempts) || !Array.isArray(parsed.progress)) {
    throw new Error('El archivo no es una copia de progreso compatible.')
  }
  const { error } = await client().rpc('tai_import_progress', {
    p_attempts: parsed.attempts, p_progress: parsed.progress,
  })
  if (error) throw error
}
