create or replace view radar.vw_resumo_proposicoes as
select
    sigla_tipo,
    ano,
    count(*) as total_proposicoes
from radar.fato_proposicao
group by sigla_tipo, ano
order by total_proposicoes desc;


create or replace view radar.vw_resumo_votacoes as
select
    sigla_orgao,
    count(*) as total_votacoes
from radar.fato_votacao
group by sigla_orgao
order by total_votacoes desc;


create or replace view radar.vw_top_ultimas_proposicoes as
select
    id_proposicao,
    sigla_tipo,
    numero,
    ano,
    data_apresentacao,
    ementa,
    uri
from radar.fato_proposicao
where data_apresentacao is not null
order by data_apresentacao desc, id_proposicao desc
limit 10;


create or replace view radar.vw_top_ultimas_votacoes as
select
    id_votacao,
    data,
    data_hora_registro,
    sigla_orgao,
    descricao,
    aprovacao,
    uri
from radar.fato_votacao
where data is not null
order by data desc, data_hora_registro desc
limit 10;