create extension if not exists pgcrypto with schema extensions;

create table if not exists public.tai_progress_snapshots (
  sync_key_hash text primary key,
  payload jsonb not null,
  updated_at timestamptz not null,
  constraint tai_progress_sync_key_hash_length check (length(sync_key_hash) = 64),
  constraint tai_progress_payload_size check (pg_column_size(payload) <= 10485760)
);

alter table public.tai_progress_snapshots enable row level security;
revoke all on public.tai_progress_snapshots from public, anon, authenticated;

comment on table public.tai_progress_snapshots is
  'Copias identificadas por el hash del código de sincronización del preparador TAI.';

create or replace function public.tai_sync_progress(
  p_sync_code text,
  p_payload jsonb,
  p_client_updated_at timestamptz
)
returns table(payload jsonb, updated_at timestamptz, action text)
language plpgsql
security definer
set search_path = public, extensions
as $$
declare
  v_hash text;
  v_current public.tai_progress_snapshots%rowtype;
  v_client_updated_at timestamptz;
begin
  if length(trim(p_sync_code)) < 12 then
    raise exception 'El código de sincronización debe tener al menos 12 caracteres.';
  end if;
  if p_payload is null or jsonb_typeof(p_payload) <> 'object' then
    raise exception 'La copia de progreso no es válida.';
  end if;
  if pg_column_size(p_payload) > 10485760 then
    raise exception 'La copia de progreso supera el máximo permitido.';
  end if;

  v_hash := encode(digest(trim(p_sync_code), 'sha256'), 'hex');
  v_client_updated_at := least(coalesce(p_client_updated_at, '1970-01-01'::timestamptz), now() + interval '5 minutes');

  select * into v_current
  from public.tai_progress_snapshots
  where sync_key_hash = v_hash
  for update;

  if not found then
    insert into public.tai_progress_snapshots(sync_key_hash, payload, updated_at)
    values (v_hash, p_payload, v_client_updated_at)
    returning * into v_current;
    return query select v_current.payload, v_current.updated_at, 'created'::text;
    return;
  end if;

  if v_client_updated_at > v_current.updated_at then
    update public.tai_progress_snapshots
    set payload = p_payload, updated_at = v_client_updated_at
    where sync_key_hash = v_hash
    returning * into v_current;
    return query select v_current.payload, v_current.updated_at, 'uploaded'::text;
  else
    return query select v_current.payload, v_current.updated_at, 'downloaded'::text;
  end if;
end;
$$;

revoke all on function public.tai_sync_progress(text, jsonb, timestamptz) from public;
grant execute on function public.tai_sync_progress(text, jsonb, timestamptz) to anon, authenticated;
