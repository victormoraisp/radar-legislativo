-- Contagem de registros por tabela

select 'dim_deputado' as tabela, count(*) as linhas from radar.dim_deputado
union all
select 'dim_partido' as tabela, count(*) as linhas from radar.dim_partido
union all
select 'dim_tema' as tabela, count(*) as linhas from radar.dim_tema
union all
select 'dim_situacao' as tabela, count(*) as linhas from radar.dim_situacao
union all
select 'fato_proposicao' as tabela, count(*) as linhas from radar.fato_proposicao
union all
select 'fato_votacao' as tabela, count(*) as linhas from radar.fato_votacao
order by tabela;


-- Prévia das proposições

select *
from radar.fato_proposicao
limit 5;


-- Prévia das votações

select *
from radar.fato_votacao
limit 5;


-- Total de proposições por tipo

select 
    sigla_tipo,
    ano,
    count(*) as total_proposicoes
from radar.fato_proposicao
group by sigla_tipo, ano
order by total_proposicoes desc;


-- Total de votações por órgão

select
    sigla_orgao,
    count(*) as total_votacoes
from radar.fato_votacao
group by sigla_orgao
order by total_votacoes desc;


-- Total de deputados por UF

select
    sigla_uf,
    count(*) as total_deputados
from radar.dim_deputado
group by sigla_uf
order by total_deputados desc;


-- Total de deputados por partido

select
    sigla_partido,
    count(*) as total_deputados
from radar.dim_deputado
group by sigla_partido
order by total_deputados desc;


union all
select 'fato_despesa' as tabela, count(*) as linhas from radar.fato_despesa


-- Resumo de despesas parlamentares

select *
from public.vw_resumo_despesas
limit 10;