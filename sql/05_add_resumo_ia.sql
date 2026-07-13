-- Camada de IA (Caminho B): resumo executivo persistido no banco.
-- O script enrich_ia_resumo.py preenche esta coluna via API da OpenAI.

alter table radar.fato_proposicao
    add column if not exists resumo_ia text;

alter table radar.fato_proposicao
    add column if not exists resumo_ia_gerado_em timestamp;

-- Recria a view de últimas proposições incluindo o resumo gerado por IA,
-- para que o resumo apareça no relatório enviado pelo n8n.
-- Drop necessário: create or replace não permite alterar a ordem das colunas.

drop view if exists public.vw_top_ultimas_proposicoes;
drop view if exists radar.vw_top_ultimas_proposicoes;

create view radar.vw_top_ultimas_proposicoes as
select
    id_proposicao,
    sigla_tipo,
    numero,
    ano,
    data_apresentacao,
    ementa,
    resumo_ia,
    uri
from radar.fato_proposicao
where data_apresentacao is not null
order by data_apresentacao desc, id_proposicao desc
limit 10;

create view public.vw_top_ultimas_proposicoes as
select *
from radar.vw_top_ultimas_proposicoes;

grant select on public.vw_top_ultimas_proposicoes to anon, authenticated;
