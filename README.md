# Radar Legislativo

Pipeline de dados desenvolvido para o projeto integrado da Pós-graduação em Engenharia de Dados.

O objetivo do projeto é extrair dados públicos da Câmara dos Deputados, transformar os dados com Python/Pandas e carregar o resultado em um banco analítico no Supabase/PostgreSQL.

## Fonte dos dados

Os dados foram extraídos da API oficial de Dados Abertos da Câmara dos Deputados.

* Portal: https://dadosabertos.camara.leg.br/
* Documentação Swagger: https://dadosabertos.camara.leg.br/swagger/api.html

## Arquitetura do pipeline

Fluxo principal:

```text
API Câmara dos Deputados
        ↓
Extração com Python requests
        ↓
JSON bruto em data/raw
        ↓
Transformação com Pandas
        ↓
CSV e Parquet em data/processed e data/model
        ↓
Carga no Supabase/PostgreSQL
        ↓
Consultas SQL de validação
```

## Estrutura do projeto

```text
radar-legislativo/
├── data/
│   ├── raw/
│   ├── processed/
│   └── model/
│
├── sql/
│   ├── 01_create_schema_tables.sql
│   ├── 02_grants.sql
│   └── 03_validation_queries.sql
│
├── extract_api_camara.py
├── transform_model.py
├── load_supabase.py
├── test_supabase_connection.py
├── main_pipeline.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Tabelas geradas

### Dimensões

| Tabela               | Descrição                               |
| -------------------- | --------------------------------------- |
| `radar.dim_deputado` | Dados cadastrais dos deputados federais |
| `radar.dim_partido`  | Dados dos partidos políticos            |
| `radar.dim_tema`     | Temas disponíveis para proposições      |
| `radar.dim_situacao` | Situações possíveis das proposições     |

### Fatos

| Tabela                  | Descrição                              |
| ----------------------- | -------------------------------------- |
| `radar.fato_proposicao` | Proposições extraídas da API da Câmara |
| `radar.fato_votacao`    | Votações extraídas da API da Câmara    |

## Resultado da carga final

| Tabela            | Linhas |
| ----------------- | -----: |
| `dim_deputado`    |    512 |
| `dim_partido`     |     21 |
| `dim_situacao`    |     99 |
| `dim_tema`        |     32 |
| `fato_proposicao` |  16082 |
| `fato_votacao`    |   1393 |

## Instalação

Crie um ambiente virtual:

```bash
python -m venv .venv
```

Ative o ambiente virtual no Windows:

```bash
.venv\Scripts\activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

## Configuração das variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto com as credenciais do Supabase:

```env
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_SERVICE_ROLE_KEY=sua_service_role_key
```

O arquivo `.env` não deve ser enviado para o GitHub.

## Criação das tabelas no Supabase

Execute os arquivos SQL nesta ordem:

```text
sql/01_create_schema_tables.sql
sql/02_grants.sql
sql/04_create_views.sql
```

Depois, no Supabase, confirme que o schema `radar` está exposto na API em:

```text
Project Settings > Data API > Exposed schemas
```

## Execução do pipeline completo

Para rodar o pipeline completo:

```bash
python main_pipeline.py
```

Esse comando executa:

```text
extract_api_camara.py
transform_model.py
load_supabase.py
```

## Execução por etapas

### 1. Extração

```bash
python extract_api_camara.py
```

Gera arquivos JSON brutos em:

```text
data/raw/
```

e arquivos intermediários em:

```text
data/processed/
```

### 2. Transformação

```bash
python transform_model.py
```

Gera os arquivos modelados em:

```text
data/model/
```

### 3. Carga no Supabase

```bash
python load_supabase.py
```

Carrega os dados no schema:

```text
radar
```

## Validação da carga

Execute o arquivo:

```text
sql/03_validation_queries.sql
```

Consulta principal de conferência:

```sql
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
```

## Observação sobre enriquecimento de dados

Este projeto mantém a carga principal baseada nos dados originais retornados pelos endpoints utilizados da API da Câmara.

Campos como autor, partido vinculado à autoria, tema específico da proposição e situação detalhada podem ser obtidos em endpoints complementares, mas foram tratados como extensão futura para preservar a rastreabilidade da primeira versão do pipeline.

## Automação com n8n

O projeto inclui um workflow no n8n para envio automático de um resumo diário.

Arquivo versionado:

```text
n8n/workflow_radar_legislativo_resumo_diario.json


## Próximos passos

Possíveis evoluções do projeto:

1. Buscar autores das proposições em endpoints complementares.
2. Buscar temas específicos por proposição.
3. Criar etapa de enriquecimento com IA para resumo das ementas.
4. Gerar embeddings com pgvector para busca semântica.
5. Criar automação no n8n para envio diário de resumo.
6. Criar dashboard analítico conectado ao Supabase.
