import {
  getLocalProgressUpdatedAt,
  getProgressSnapshot,
  replaceProgressSnapshot,
  type ProgressSnapshot,
} from './storage'

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL?.replace(/\/$/, '')
const SUPABASE_KEY = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY
const SYNC_CODE_KEY = 'tai-age-supabase-sync-code'

export type CloudSyncAction = 'created' | 'uploaded' | 'downloaded'

interface CloudSyncRow {
  payload: ProgressSnapshot
  updated_at: string
  action: CloudSyncAction
}

export function isCloudSyncConfigured(): boolean {
  return Boolean(SUPABASE_URL && SUPABASE_KEY)
}

export function getCloudSyncCode(): string {
  return localStorage.getItem(SYNC_CODE_KEY) ?? ''
}

export function rememberCloudSyncCode(value: string): string {
  const code = value.trim()
  if (code.length < 12) throw new Error('El código debe tener al menos 12 caracteres.')
  localStorage.setItem(SYNC_CODE_KEY, code)
  return code
}

export function forgetCloudSyncCode(): void {
  localStorage.removeItem(SYNC_CODE_KEY)
}

export function createCloudSyncCode(): string {
  return `TAI-${crypto.randomUUID()}`
}

export async function synchronizeProgress(codeInput?: string): Promise<CloudSyncRow> {
  if (!SUPABASE_URL || !SUPABASE_KEY) throw new Error('La sincronización en la nube no está configurada.')
  const code = rememberCloudSyncCode(codeInput ?? getCloudSyncCode())
  const [snapshot, localUpdatedAt] = await Promise.all([getProgressSnapshot(), getLocalProgressUpdatedAt()])
  const response = await fetch(`${SUPABASE_URL}/rest/v1/rpc/tai_sync_progress`, {
    method: 'POST',
    headers: {
      apikey: SUPABASE_KEY,
      Authorization: `Bearer ${SUPABASE_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      p_sync_code: code,
      p_payload: snapshot,
      p_client_updated_at: localUpdatedAt,
    }),
  })
  if (!response.ok) {
    const detail = await response.json().catch(() => null) as { message?: string } | null
    throw new Error(detail?.message ?? `Supabase respondió con el código ${response.status}.`)
  }
  const rows = await response.json() as CloudSyncRow[]
  const row = rows[0]
  if (!row?.payload || !row.updated_at) throw new Error('Supabase devolvió una respuesta incompleta.')
  if (row.action === 'downloaded') await replaceProgressSnapshot(row.payload, row.updated_at)
  return row
}
