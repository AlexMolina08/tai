import Dexie from 'dexie'
import type { AttemptRecord, QuestionProgress } from '../types'
import type { ProgressSnapshot } from './storage'

// Lectura única del formato usado por las versiones anteriores de la web.
// Nunca modifica ni elimina la base local: sirve para trasladar datos a una
// cuenta de Supabase nueva, manteniendo la copia original como respaldo.
export async function readLegacyProgress(): Promise<ProgressSnapshot | null> {
  if (!(await Dexie.exists('tai-age-preparador'))) return null
  const old = new Dexie('tai-age-preparador')
  old.version(1).stores({
    attempts: 'id, finishedAt, mode',
    progress: 'questionId, wrong, favorite, lastSeenAt',
  })
  try {
    const [attempts, progress] = await Promise.all([
      old.table<AttemptRecord>('attempts').toArray(),
      old.table<QuestionProgress>('progress').toArray(),
    ])
    if (!attempts.length && !progress.length) return null
    return { schemaVersion: 1, exportedAt: new Date().toISOString(), attempts, progress }
  } finally {
    old.close()
  }
}
