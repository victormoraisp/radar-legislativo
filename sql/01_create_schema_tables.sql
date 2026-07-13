create schema if not exists radar;

drop table if exists radar.fato_votacao;
drop table if exists radar.fato_proposicao;
drop table if exists radar.dim_situacao;
drop table if exists radar.dim_tema;
drop table if exists radar.dim_partido;
drop table if exists radar.dim_deputado;

create table radar.dim_deputado (
    id_deputado bigint primary key,
    nome text,
    sigla_partido text,
    sigla_uf text,
    id_legislatura bigint,
    url_foto text,
    email text
);

create table radar.dim_partido (
    id_partido bigint primary key,
    sigla text,
    nome text,
    uri text
);

create table radar.dim_tema (
    cod_tema bigint primary key,
    sigla text,
    nome text,
    descricao text
);

create table radar.dim_situacao (
    cod_situacao bigint primary key,
    sigla text,
    nome text,
    descricao text
);

create table radar.fato_proposicao (
    id_proposicao bigint primary key,
    sigla_tipo text,
    cod_tipo bigint,
    numero bigint,
    ano bigint,
    ementa text,
    data_apresentacao date,
    uri text,
    created_at timestamp default now()
);

create table radar.fato_votacao (
    id_votacao text primary key,
    uri text,
    data date,
    data_hora_registro timestamp,
    sigla_orgao text,
    uri_orgao text,
    uri_evento text,
    proposicao_objeto text,
    uri_proposicao_objeto text,
    descricao text,
    aprovacao text,
    created_at timestamp default now()
);


create table radar.fato_despesa (
    id_despesa text primary key,
    id_deputado bigint,
    nome_deputado text,
    sigla_partido text,
    sigla_uf text,
    ano bigint,
    mes bigint,
    tipo_despesa text,
    cod_documento bigint,
    tipo_documento text,
    cod_tipo_documento bigint,
    data_documento date,
    num_documento text,
    valor_documento numeric,
    valor_glosa numeric,
    valor_liquido numeric,
    nome_fornecedor text,
    cnpj_cpf_fornecedor text,
    url_documento text,
    created_at timestamp default now()
);