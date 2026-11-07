-- =============================================================
-- VivAIplus — Fase 4 (contato e interesses) no Supabase
--
-- Rode este arquivo UMA vez no SQL Editor do painel do Supabase,
-- depois do fase3_lgpd.sql. Pode rodar de novo sem problema.
--
-- O agente funciona antes e depois deste SQL: sem ele, só não grava
-- o e-mail e as áreas de interesse marcadas no formulário.
-- =============================================================

-- E-mail do candidato, para o RH retornar contato. Nunca é enviado à IA.
alter table public.candidatos
  add column if not exists email text;

-- Ids dos setores marcados nos chips do formulário (ex.: {rh,ti}).
-- Não influenciam a análise: servem só para o RH.
alter table public.candidatos
  add column if not exists areas_interesse text[] not null default '{}';

-- O RLS e a retenção de 180 dias do fase3_lgpd.sql valem para estas
-- colunas também (a linha inteira é apagada no prazo).

-- Conferência
select column_name, data_type
from information_schema.columns
where table_schema = 'public' and table_name = 'candidatos'
  and column_name in ('email', 'areas_interesse');
