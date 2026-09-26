-- Fuentes de práctica personales. El catálogo de exámenes oficiales no se altera.
create table if not exists public.tai_user_sources (
  user_id uuid not null references auth.users(id) on delete cascade default auth.uid(),
  source_id text not null,
  title text not null,
  payload jsonb not null,
  uploaded_at timestamptz not null default now(),
  primary key (user_id, source_id)
);

alter table public.tai_user_sources enable row level security;
revoke all on public.tai_user_sources from public, anon, authenticated;
grant select on public.tai_user_sources to authenticated;
drop policy if exists "Read own sources" on public.tai_user_sources;
create policy "Read own sources" on public.tai_user_sources
  for select to authenticated using ((select auth.uid()) = user_id);

create or replace function public.tai_save_user_source(p_source jsonb)
returns void language plpgsql security definer set search_path = public
as $$
declare
  v_user uuid := auth.uid();
  v_item jsonb;
  v_id text;
  v_seen text[] := array[]::text[];
  v_topic text;
begin
  if v_user is null then raise exception 'Inicia sesión para añadir preguntas'; end if;
  if jsonb_typeof(p_source) <> 'object' or p_source->'schemaVersion' <> '1'::jsonb
     or octet_length(p_source::text) > 1048576 then
    raise exception 'Archivo JSON no válido o demasiado grande';
  end if;
  if jsonb_typeof(p_source->'sourceId') <> 'string'
     or jsonb_typeof(p_source->'title') <> 'string'
     or coalesce(p_source->>'sourceId', '') !~ '^[a-z0-9][a-z0-9-]{0,79}$'
     or length(trim(coalesce(p_source->>'title', ''))) not between 1 and 160 then
    raise exception 'Identificador o título de la fuente no válido';
  end if;
  if jsonb_typeof(p_source->'questions') <> 'array'
     or jsonb_array_length(p_source->'questions') not between 1 and 200 then
    raise exception 'La fuente debe tener entre 1 y 200 preguntas';
  end if;
  for v_item in select value from jsonb_array_elements(p_source->'questions') as value loop
    v_id := v_item->>'id';
    v_topic := v_item->>'topicId';
    if jsonb_typeof(v_item) <> 'object'
       or jsonb_typeof(v_item->'id') <> 'string'
       or jsonb_typeof(v_item->'topicId') <> 'string'
       or jsonb_typeof(v_item->'prompt') <> 'string'
       or coalesce(v_id, '') !~ '^[a-z0-9][a-z0-9-]{0,79}$'
       or v_id = any(v_seen)
       or length(trim(coalesce(v_item->>'prompt', ''))) not between 1 and 3000
       or jsonb_typeof(v_item->'options') <> 'array'
       or jsonb_array_length(v_item->'options') <> 4
       or jsonb_typeof(v_item->'correctAnswer') <> 'string'
       or coalesce(v_item->>'correctAnswer', '') not in ('a','b','c','d') then
      raise exception 'Pregunta % no válida o repetida', coalesce(v_id, '?');
    end if;
    if exists (
      select 1 from jsonb_array_elements(v_item->'options') as option
      where jsonb_typeof(option.value) <> 'string'
         or length(trim(option.value #>> '{}')) not between 1 and 1500
    ) then raise exception 'La pregunta % debe tener cuatro opciones no vacías', v_id; end if;
    if (v_item ? 'explanation' and (jsonb_typeof(v_item->'explanation') <> 'string'
        or length(trim(v_item->>'explanation')) not between 1 and 3000))
       or (v_item ? 'sourceNote' and (jsonb_typeof(v_item->'sourceNote') <> 'string'
        or length(trim(v_item->>'sourceNote')) not between 1 and 500)) then
      raise exception 'Explicación o referencia no válida en la pregunta %', v_id;
    end if;
    if not exists (
      select 1 from public.tai_catalog c,
        jsonb_array_elements(c.payload->'program') as block,
        jsonb_array_elements(block.value->'topics') as topic
      where c.id = 'official' and topic.value->>'id' = v_topic
    ) then raise exception 'Tema % no válido en la pregunta %', coalesce(v_topic, '?'), v_id; end if;
    v_seen := array_append(v_seen, v_id);
  end loop;

  insert into public.tai_user_sources(user_id, source_id, title, payload)
  values (v_user, p_source->>'sourceId', p_source->>'title', p_source)
  on conflict (user_id, source_id) do update set
    title = excluded.title,
    payload = excluded.payload,
    uploaded_at = now();
end;
$$;
revoke all on function public.tai_save_user_source(jsonb) from public, anon;
grant execute on function public.tai_save_user_source(jsonb) to authenticated;
