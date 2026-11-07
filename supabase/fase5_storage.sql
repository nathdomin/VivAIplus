-- =============================================================
-- VivAIplus — Fase 5: currículos no Supabase Storage (sai o Backblaze B2)
--
-- Rode este arquivo UMA vez no SQL Editor do painel do Supabase.
-- Pode rodar de novo sem problema (é idempotente).
--
-- Depois dele, os arquivos ficam em Storage → bucket "curriculos",
-- e o nome de cada arquivo é o da coluna arquivo_salvo da tabela
-- candidatos (para o RH achar o currículo de cada candidato).
-- =============================================================


-- 1. Bucket privado ------------------------------------------------
-- public = false: nenhum arquivo tem link público. O limite de 5 MB e
-- os tipos aceitos repetem a validação do agente, como segunda barreira.
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'curriculos',
  'curriculos',
  false,
  5242880,
  array[
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
  ]
)
on conflict (id) do update set
  public = excluded.public,
  file_size_limit = excluded.file_size_limit,
  allowed_mime_types = excluded.allowed_mime_types;


-- 2. Acesso (RLS) --------------------------------------------------
-- A chave publishable do agente só consegue ENVIAR arquivos novos para
-- este bucket: não lista, não baixa, não sobrescreve e não apaga.
-- Você vê e baixa tudo pelo painel (Storage), que não passa pelo RLS.
-- A limpeza de 180 dias usa a chave secreta (SUPABASE_SERVICE_KEY),
-- que também ignora o RLS.
drop policy if exists "agente_envia_curriculos" on storage.objects;

create policy "agente_envia_curriculos"
  on storage.objects
  for insert
  to anon, authenticated
  with check (bucket_id = 'curriculos');


-- 3. Conferência ---------------------------------------------------
select id, public, file_size_limit, allowed_mime_types
from storage.buckets where id = 'curriculos';

select policyname, cmd, roles from pg_policies
where schemaname = 'storage' and tablename = 'objects'
  and policyname = 'agente_envia_curriculos';
