-- =============================================================
-- VivAIplus — Fase 3 (LGPD) no Supabase
--
-- Rode este arquivo inteiro UMA vez no painel do Supabase:
-- SQL Editor → New query → cole tudo → Run.
-- Pode rodar de novo sem problema (é idempotente).
--
-- O agente funciona antes e depois deste SQL: sem ele, só não grava
-- a data do consentimento e os registros não são apagados.
-- =============================================================


-- 1. Colunas novas -------------------------------------------------
-- created_at: base do prazo de retenção. Registros que já existem
-- recebem a data de agora (o prazo deles começa a contar hoje).
alter table public.candidatos
  add column if not exists created_at timestamptz not null default now();

-- consentimento_em: quando o candidato marcou o aceite do formulário.
alter table public.candidatos
  add column if not exists consentimento_em timestamptz;


-- 2. Acesso (RLS) --------------------------------------------------
-- Hoje a chave usada pelo agente (publishable/anon) consegue LER todos
-- os currículos. Daqui em diante ela só consegue INSERIR. Você continua
-- vendo tudo pelo Table Editor do painel, que não passa pelo RLS.
--
-- ATENÇÃO: se outro sistema lê esta tabela com a chave publishable,
-- ele vai parar de enxergar os dados. Nesse caso, use nele uma chave
-- secreta (secret / service_role), que ignora o RLS.
alter table public.candidatos enable row level security;

-- Remove as políticas antigas da tabela (eram elas que liberavam a leitura)
do $$
declare
  p record;
begin
  for p in
    select policyname from pg_policies
    where schemaname = 'public' and tablename = 'candidatos'
  loop
    execute format('drop policy %I on public.candidatos', p.policyname);
  end loop;
end $$;

create policy "agente_insere_candidatos"
  on public.candidatos
  for insert
  to anon, authenticated
  with check (true);


-- 3. Retenção ------------------------------------------------------
-- Apaga todo dia, às 03:15 (UTC), os registros com mais de 180 dias.
-- O prazo precisa ser o mesmo da variável RETENCAO_DIAS do agente
-- (padrão 180), que apaga os arquivos correspondentes no B2.
create extension if not exists pg_cron;

select cron.unschedule(jobid)
from cron.job
where jobname = 'retencao-candidatos';

select cron.schedule(
  'retencao-candidatos',
  '15 3 * * *',
  $$delete from public.candidatos where created_at < now() - interval '180 days'$$
);


-- 4. Conferência ---------------------------------------------------
-- Deve listar só a política "agente_insere_candidatos" e o job agendado.
select policyname, cmd, roles from pg_policies
where schemaname = 'public' and tablename = 'candidatos';

select jobname, schedule, command from cron.job
where jobname = 'retencao-candidatos';
