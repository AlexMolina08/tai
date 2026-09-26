-- Progreso canónico en Postgres; cada sesión se identifica con Supabase Auth.
create table if not exists public.tai_catalog (
  id text primary key,
  payload jsonb not null,
  updated_at timestamptz not null default now()
);
alter table public.tai_catalog enable row level security;
revoke all on public.tai_catalog from public, anon, authenticated;
grant select on public.tai_catalog to authenticated;
drop policy if exists "Authenticated users read catalog" on public.tai_catalog;
create policy "Authenticated users read catalog" on public.tai_catalog
  for select to authenticated using (true);

create table if not exists public.tai_attempts (
  user_id uuid not null references auth.users(id) on delete cascade default auth.uid(),
  id uuid not null,
  finished_at timestamptz not null,
  payload jsonb not null,
  primary key (user_id, id)
);

create index if not exists tai_attempts_user_finished_idx
  on public.tai_attempts (user_id, finished_at desc);

create table if not exists public.tai_question_progress (
  user_id uuid not null references auth.users(id) on delete cascade default auth.uid(),
  question_id text not null,
  seen integer not null default 0 check (seen >= 0),
  correct integer not null default 0 check (correct >= 0),
  wrong integer not null default 0 check (wrong >= 0),
  favorite boolean not null default false,
  last_seen_at timestamptz,
  primary key (user_id, question_id)
);

alter table public.tai_attempts enable row level security;
alter table public.tai_question_progress enable row level security;
revoke all on public.tai_attempts, public.tai_question_progress from public, anon, authenticated;
grant select on public.tai_attempts, public.tai_question_progress to authenticated;

drop policy if exists "Read own attempts" on public.tai_attempts;
create policy "Read own attempts" on public.tai_attempts
  for select to authenticated using ((select auth.uid()) = user_id);
drop policy if exists "Read own question progress" on public.tai_question_progress;
create policy "Read own question progress" on public.tai_question_progress
  for select to authenticated using ((select auth.uid()) = user_id);

create or replace function public.tai_record_attempt(p_attempt jsonb, p_outcomes jsonb)
returns void language plpgsql security definer set search_path = public
as $$
declare
  v_user uuid := auth.uid();
  v_item jsonb;
  v_question_id text;
begin
  if v_user is null then raise exception 'Inicia sesión para guardar el test'; end if;
  if jsonb_typeof(p_attempt) <> 'object' or jsonb_typeof(p_outcomes) <> 'array'
    or jsonb_array_length(p_outcomes) > 150 then
    raise exception 'Resultado de test no válido';
  end if;

  insert into public.tai_attempts(user_id, id, finished_at, payload)
  values (v_user, (p_attempt->>'id')::uuid, (p_attempt->>'finishedAt')::timestamptz, p_attempt)
  on conflict (user_id, id) do nothing;
  if not found then return; end if; -- Un reintento no duplica estadísticas.

  for v_item in select value from jsonb_array_elements(p_outcomes) as value loop
    v_question_id := v_item->>'questionId';
    if v_question_id is null or length(v_question_id) > 180 then
      raise exception 'Pregunta no válida';
    end if;
    insert into public.tai_question_progress(user_id, question_id, seen, correct, wrong, last_seen_at)
    values (v_user, v_question_id, 1,
      case when v_item->>'outcome' = 'correct' then 1 else 0 end,
      case when v_item->>'outcome' = 'wrong' then 1 else 0 end,
      (p_attempt->>'finishedAt')::timestamptz)
    on conflict (user_id, question_id) do update set
      seen = tai_question_progress.seen + 1,
      correct = tai_question_progress.correct + excluded.correct,
      wrong = tai_question_progress.wrong + excluded.wrong,
      last_seen_at = greatest(tai_question_progress.last_seen_at, excluded.last_seen_at);
  end loop;
end;
$$;

create or replace function public.tai_toggle_favorite(p_question_id text)
returns boolean language plpgsql security definer set search_path = public
as $$
declare
  v_user uuid := auth.uid();
  v_favorite boolean;
begin
  if v_user is null then raise exception 'Inicia sesión para guardar favoritos'; end if;
  if p_question_id is null or length(p_question_id) > 180 then raise exception 'Pregunta no válida'; end if;
  insert into public.tai_question_progress(user_id, question_id, favorite)
  values (v_user, p_question_id, true)
  on conflict (user_id, question_id) do update set favorite = not tai_question_progress.favorite
  returning favorite into v_favorite;
  return v_favorite;
end;
$$;

revoke all on function public.tai_record_attempt(jsonb,jsonb) from public, anon;
revoke all on function public.tai_toggle_favorite(text) from public, anon;
grant execute on function public.tai_record_attempt(jsonb,jsonb) to authenticated;
grant execute on function public.tai_toggle_favorite(text) to authenticated;

-- Importación única de una copia local anterior, sin fusionar ni pisar datos.
create or replace function public.tai_import_progress(p_attempts jsonb, p_progress jsonb)
returns void language plpgsql security definer set search_path = public
as $$
declare
  v_user uuid := auth.uid();
  v_item jsonb;
begin
  if v_user is null then raise exception 'Inicia sesión para importar'; end if;
  if jsonb_typeof(p_attempts) <> 'array' or jsonb_typeof(p_progress) <> 'array'
     or jsonb_array_length(p_attempts) > 10000 or jsonb_array_length(p_progress) > 10000 then
    raise exception 'Copia de progreso no válida';
  end if;
  if exists(select 1 from public.tai_attempts where user_id = v_user)
     or exists(select 1 from public.tai_question_progress where user_id = v_user) then
    raise exception 'La cuenta ya tiene progreso; no se ha importado la copia';
  end if;
  for v_item in select value from jsonb_array_elements(p_attempts) as value loop
    insert into public.tai_attempts(user_id,id,finished_at,payload)
    values(v_user,(v_item->>'id')::uuid,(v_item->>'finishedAt')::timestamptz,v_item);
  end loop;
  for v_item in select value from jsonb_array_elements(p_progress) as value loop
    insert into public.tai_question_progress(user_id,question_id,seen,correct,wrong,favorite,last_seen_at)
    values(v_user,v_item->>'questionId',(v_item->>'seen')::integer,
      (v_item->>'correct')::integer,(v_item->>'wrong')::integer,
      coalesce((v_item->>'favorite')::boolean,false),(v_item->>'lastSeenAt')::timestamptz);
  end loop;
end;
$$;
revoke all on function public.tai_import_progress(jsonb,jsonb) from public, anon;
grant execute on function public.tai_import_progress(jsonb,jsonb) to authenticated;
