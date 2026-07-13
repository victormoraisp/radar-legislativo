# Radar Legislativo

Pipeline de engenharia de dados desenvolvido para o Projeto Integrador da Pós-graduação em Engenharia de Dados.

O projeto simula uma solução para a consultoria fictícia **Bússola Pública**, cujo objetivo é transformar dados públicos da Câmara dos Deputados em uma base analítica organizada, automatizada e pronta para geração de inteligência executiva.

Repositório: https://github.com/victormoraisp/radar-legislativo

---

## 1. Objetivo

Construir um pipeline completo para:

1. Extrair dados públicos da API da Câmara dos Deputados.
2. Salvar os retornos brutos em JSON para rastreabilidade.
3. Transformar, validar e modelar os dados com Python e Pandas.
4. Carregar tabelas fato e dimensão no Supabase/PostgreSQL.
5. Enriquecer as proposições com resumos executivos gerados por IA, persistidos no banco.
6. Criar consultas e views analíticas em SQL.
7. Automatizar a entrega diária com n8n.

---

## 2. Fonte dos dados

Os dados foram extraídos da API oficial de Dados Abertos da Câmara dos Deputados.

- Portal: https://dadosabertos.camara.leg.br/
- Documentação Swagger: https://dadosabertos.camara.leg.br/swagger/api.html
- API v2: https://dadosabertos.camara.leg.br/api/v2

Principais módulos utilizados:

- Deputados
- Partidos
- Proposições
- Votações
- Despesas parlamentares
- Referências de temas e situações

---

## 3. Arquitetura do pipeline

![Diagrama do pipeline](docs/img/diagrama_pipeline.svg)

```text
API Câmara dos Deputados
        ↓
Extração com Python requests (paginação, try/except, retry)
        ↓
JSON bruto em data/raw
        ↓
Transformação e validação com Pandas
        ↓
CSV e Parquet em data/processed e data/model
        ↓
Carga no Supabase/PostgreSQL
        ↓
IA (OpenAI) gera resumo executivo por proposição → coluna resumo_ia
        ↓
Views SQL analíticas
        ↓
n8n (diário às 06h)
        ↓
OpenAI gera análise executiva do dia
        ↓
E-mail diário automatizado com resumos IA
```

A camada de IA atua em dois pontos: enriquece a tabela `fato_proposicao` com resumos executivos persistidos (coluna `resumo_ia`) e gera a análise executiva do e-mail diário no n8n.

---

## 4. Estrutura do projeto

```text
radar-legislativo/
├── data/
│   ├── raw/            (local, fora do Git)
│   │   └── despesas/
│   ├── processed/      (local, fora do Git)
│   └── model/
│
├── docs/
│   └── img/
│       ├── diagrama_pipeline.svg
│       ├── print_n8n_execucao.png
│       ├── print_supabase_tabelas.png
│       └── print_email_resumo.png
│
├── n8n/
│   └── workflow_radar_legislativo_resumo_diario.json
│
├── sql/
│   ├── 01_create_schema_tables.sql
│   ├── 02_grants.sql
│   ├── 03_validation_queries.sql
│   ├── 04_create_views.sql
│   └── 05_add_resumo_ia.sql
│
├── apresentacao/
│   ├── build_pptx.py
│   └── radar_legislativo_pitch.pptx
│
├── extract_api_camara.py
├── transform_model.py
├── load_supabase.py
├── enrich_ia_resumo.py
├── extract_despesas.py
├── reduce_despesas.py
├── load_despesas_supabase.py
├── test_supabase_connection.py
├── main_pipeline.py
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 5. Modelo de dados

### 5.1 Dimensões

| Tabela | Colunas | Descrição |
|---|---|---|
| `radar.dim_deputado` | `id_deputado` (PK), `nome`, `sigla_partido`, `sigla_uf`, `id_legislatura`, `url_foto`, `email` | Dados cadastrais dos deputados federais |
| `radar.dim_partido` | `id_partido` (PK), `sigla`, `nome`, `uri` | Dados dos partidos políticos |
| `radar.dim_tema` | `cod_tema` (PK), `sigla`, `nome`, `descricao` | Temas disponíveis para proposições |
| `radar.dim_situacao` | `cod_situacao` (PK), `sigla`, `nome`, `descricao` | Situações possíveis das proposições |

### 5.2 Fatos

| Tabela | Colunas | Descrição |
|---|---|---|
| `radar.fato_proposicao` | `id_proposicao` (PK), `sigla_tipo`, `cod_tipo`, `numero`, `ano`, `ementa`, `data_apresentacao`, `uri`, `resumo_ia`, `resumo_ia_gerado_em`, `created_at` | Proposições da Câmara, enriquecidas com resumo executivo gerado por IA |
| `radar.fato_votacao` | `id_votacao` (PK), `uri`, `data`, `data_hora_registro`, `sigla_orgao`, `uri_orgao`, `uri_evento`, `proposicao_objeto`, `uri_proposicao_objeto`, `descricao`, `aprovacao`, `created_at` | Votações da Câmara |
| `radar.fato_despesa` | `id_despesa` (PK), `id_deputado`, `nome_deputado`, `sigla_partido`, `sigla_uf`, `ano`, `mes`, `tipo_despesa`, `cod_documento`, `tipo_documento`, `cod_tipo_documento`, `data_documento`, `num_documento`, `valor_documento`, `valor_glosa`, `valor_liquido`, `nome_fornecedor`, `cnpj_cpf_fornecedor`, `url_documento`, `created_at` | Despesas da cota parlamentar |

### 5.3 Relacionamentos

```text
dim_deputado.id_deputado      1 ──── N  fato_despesa.id_deputado
dim_deputado.sigla_partido    N ──── 1  dim_partido.sigla
fato_proposicao.cod_tipo           →    tipo da proposição (referência da API)
dim_tema / dim_situacao            →    tabelas de referência para classificação
                                        e acompanhamento de status das proposições
```

### 5.4 Observação sobre despesas

A extração de despesas gerou **36.542 registros locais**. Para manter a carga no Supabase mais leve e controlada, foi carregada uma amostra de **3.000 registros** na tabela `radar.fato_despesa`.

Essa decisão preserva a evidência técnica do endpoint de despesas, reduz o tempo de carga e mantém o banco adequado para demonstração.

---

## 6. Banco na nuvem (acesso em modo leitura)

O banco está hospedado no Supabase com **30 dias de dados ingeridos** (proposições e votações de abril/2026).

O acesso de leitura é feito pela REST API do Supabase com a chave anônima (`anon`), que possui apenas privilégio `SELECT` (ver `sql/02_grants.sql`). A chave `anon` é pública por design e não permite escrita.

```text
URL:   https://vmktswtylsecsvzqiidd.supabase.co
Chave: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZta3Rzd3R5bHNlY3N2enFpaWRkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODExMjgzNzMsImV4cCI6MjA5NjcwNDM3M30.xi7aFEXgmHOIaMbGAmLIcylHndl9DupDtmhlq3Qm_20
```

Exemplos de consulta (basta colar no terminal):

```bash
# Últimas proposições com resumo gerado por IA
curl "https://vmktswtylsecsvzqiidd.supabase.co/rest/v1/vw_top_ultimas_proposicoes?select=*" \
  -H "apikey: <CHAVE_ANON>"

# Contagem de proposições
curl "https://vmktswtylsecsvzqiidd.supabase.co/rest/v1/fato_proposicao?select=count" \
  -H "apikey: <CHAVE_ANON>" -H "Accept-Profile: radar"

# Proposições com resumo IA preenchido
curl "https://vmktswtylsecsvzqiidd.supabase.co/rest/v1/fato_proposicao?select=id_proposicao,ementa,resumo_ia&resumo_ia=not.is.null&limit=5" \
  -H "apikey: <CHAVE_ANON>" -H "Accept-Profile: radar"
```

Evidências da carga:

![Tabelas no Supabase](docs/img/print_supabase_tabelas.png)

---

## 7. Resultado da carga final

| Tabela | Linhas |
|---|---:|
| `dim_deputado` | 512 |
| `dim_partido` | 21 |
| `dim_situacao` | 99 |
| `dim_tema` | 32 |
| `fato_proposicao` | 16.082 |
| `fato_votacao` | 1.393 |
| `fato_despesa` | 3.000 no Supabase / 36.542 extraídas localmente |

---

## 8. Instalação

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

---

## 9. Variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_SERVICE_ROLE_KEY=sua_service_role_key
OPENAI_API_KEY=sua_chave_openai
```

O arquivo `.env` não deve ser enviado para o GitHub.

---

## 10. Criação do banco no Supabase

Execute os arquivos SQL nesta ordem:

```text
sql/01_create_schema_tables.sql
sql/02_grants.sql
sql/04_create_views.sql
sql/05_add_resumo_ia.sql
```

Depois, no Supabase, confirme que o schema `radar` está exposto na API:

```text
Project Settings > Data API > Exposed schemas
```

O schema `public` contém views espelho para simplificar o consumo via Supabase REST API e n8n.

---

## 11. Execução do pipeline principal

Para rodar o pipeline principal:

```bash
python main_pipeline.py
```

Esse comando executa:

```text
extract_api_camara.py   (paginação, try/except e retry com backoff)
transform_model.py      (validações, tipagem e deduplicação)
load_supabase.py        (carga em lotes via upsert)
```

Validações aplicadas com Pandas na transformação:

- Campos obrigatórios não nulos (chaves primárias e ementa)
- Datas dentro de range plausível (1988 até hoje)
- Valores monetários negativos removidos (`df[df['valor_liquido'] < 0]`)
- Deduplicação por chave primária

---

## 12. Camada de IA: resumo executivo persistido no banco

Após a carga, o script `enrich_ia_resumo.py` gera um resumo executivo por proposição (Caminho B do desafio) e salva na coluna `resumo_ia` de `radar.fato_proposicao`.

### 12.1 Execução com controle de custo

Teste primeiro com 10 proposições (padrão) e observe o custo estimado impresso ao final:

```bash
python enrich_ia_resumo.py
```

Depois amplie de forma consciente:

```bash
python enrich_ia_resumo.py 100
python enrich_ia_resumo.py all
```

O script imprime tokens consumidos, custo da execução, custo médio por proposição e projeção para 1.000 e para as 16.082 proposições da base.

### 12.2 Prompt utilizado (resumo por proposição)

```text
Você é um analista legislativo sênior da consultoria Bússola Pública.
Resuma a proposição a seguir em até 3 linhas, em linguagem clara para um executivo.
Não invente informações. Não use markdown. Responda apenas o resumo.
```

### 12.3 Prompt utilizado (análise executiva diária no n8n)

```text
Você é um analista legislativo sênior da consultoria Bússola Pública.

Sua tarefa é gerar uma análise executiva breve a partir de dados públicos da Câmara dos Deputados.

A resposta será usada como introdução de um e-mail enviado para diretores.

Regras:
- Escreva em português do Brasil.
- Seja objetivo.
- Não invente informações.
- Use apenas os dados fornecidos.
- Destaque temas recorrentes, possíveis impactos e pontos de atenção.
- Não use markdown.
- Não use lista longa.
- Escreva no máximo 3 parágrafos curtos.
```

### 12.4 Decisão técnica

O resumo por proposição fica **persistido no banco** (coluna `resumo_ia`), garantindo que a IA enriqueça o dado e não apenas a entrega. A ementa original é preservada, mantendo rastreabilidade entre dado oficial e dado gerado por modelo. O resumo aparece no relatório diário enviado por e-mail, na coluna "Resumo IA".

---

## 13. Execução do pipeline de despesas

A frente de despesas foi separada para manter controle de volume.

### 13.1 Extração completa local

```bash
python extract_despesas.py
```

Gera:

```text
data/model/fato_despesa.csv
data/model/fato_despesa.parquet
```

### 13.2 Redução para amostra

```bash
python reduce_despesas.py
```

Gera:

```text
data/model/fato_despesa_amostra.csv
```

### 13.3 Carga da amostra no Supabase

```bash
python load_despesas_supabase.py
```

Carrega 3.000 registros na tabela:

```text
radar.fato_despesa
```

---

## 14. Validação da carga

Execute:

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
union all
select 'fato_despesa' as tabela, count(*) as linhas from radar.fato_despesa
order by tabela;
```

---

## 15. Views analíticas

O projeto possui views no schema `radar` e views espelho no schema `public`.

| View | Finalidade |
|---|---|
| `radar.vw_top_ultimas_proposicoes` | Últimas proposições com resumo IA para o relatório |
| `radar.vw_top_ultimas_votacoes` | Últimas votações para o relatório |
| `radar.vw_resumo_proposicoes` | Resume proposições por tipo e ano |
| `radar.vw_resumo_votacoes` | Resume votações por órgão |
| `radar.vw_resumo_despesas` | Resume despesas por ano, mês, partido, UF e tipo |

As views públicas equivalentes permitem consumo via Supabase REST API pelo n8n.

---

## 16. Automação com n8n

O projeto inclui um workflow no n8n para envio automático de um resumo diário às 06h.

Arquivo versionado:

```text
n8n/workflow_radar_legislativo_resumo_diario.json
```

Fluxo do workflow:

```text
Schedule Trigger (06h)
        ↓
HTTP Request - Últimas proposições (com resumo_ia)
        ↓
HTTP Request - Últimas votações
        ↓
Code - Preparar contexto para IA
        ↓
OpenAI - Gerar análise executiva do dia
        ↓
Code - Montar HTML final (tabela com coluna Resumo IA)
        ↓
Envio de e-mail
```

Execução bem-sucedida:

![Execução do workflow n8n](docs/img/print_n8n_execucao.png)

E-mail recebido:

![E-mail com resumo diário](docs/img/print_email_resumo.png)

O workflow consulta as views públicas criadas no Supabase:

```text
public.vw_top_ultimas_proposicoes
public.vw_top_ultimas_votacoes
```

A chave do Supabase não fica salva diretamente no JSON exportado. O workflow utiliza variável de ambiente no n8n (`SUPABASE_ANON_KEY`). A credencial da OpenAI é configurada como credencial nativa do n8n.

---

## 17. Apresentação executiva

A apresentação executiva do projeto está no repositório em:

```text
apresentacao/radar_legislativo_pitch.pptx
```

Para regenerar a apresentação:

```bash
python apresentacao/build_pptx.py
```

Estrutura do pitch (6 slides):

1. O problema da Bússola Pública
2. A solução: pipeline automatizado com IA
3. Arquitetura e stack
4. Demo: banco populado e modelo de dados
5. Demo: automação n8n + IA no produto
6. Próximos passos

---

## 18. Decisões técnicas

| Decisão | Justificativa |
|---|---|
| Supabase/PostgreSQL | Banco gerenciado, simples de demonstrar e compatível com SQL analítico |
| JSON bruto local | Permite reprocessar dados sem chamar a API novamente |
| Pandas para transformação | Ferramenta adequada para limpeza, validação, tipagem e deduplicação |
| Schema `radar` | Isola os objetos do projeto dentro do Supabase |
| Views públicas | Simplificam o consumo pelo n8n via REST API |
| Resumo IA persistido (Caminho B) | A IA enriquece o dado no banco, não apenas a entrega; o resumo aparece no relatório diário |
| Escolha do Caminho B em vez de embeddings | O resumo executivo entrega valor direto ao cliente final do relatório; a classificação por embeddings ficou como evolução com pgvector |
| Controle de custo de IA | Execução começa com 10 registros, imprime custo real e projeta o custo total antes de escalar |
| Amostra de despesas no Supabase | Evita carga excessiva e mantém evidência do endpoint de despesas |
| `data/raw` fora do Git | ~790 arquivos JSON são regeneráveis pela API; o repositório fica leve |

---

## 19. Segurança

O projeto usa `.env` para credenciais sensíveis.

Não devem ser enviados ao GitHub:

- Chaves do Supabase
- Chaves da OpenAI
- Senhas de banco
- Tokens de autenticação

O `.gitignore` protege arquivos sensíveis e artefatos temporários.

---

## 20. Entregáveis atendidos

| Entregável | Status |
|---|---|
| Repositório GitHub com pipeline completo e README | Concluído |
| Banco PostgreSQL/Supabase populado com 30 dias de dados | Concluído |
| Link do projeto em modo leitura no README | Concluído (seção 6) |
| Workflow n8n exportado (.json) com print de execução | Concluído (seção 16) |
| Diagrama do pipeline | Concluído (seção 3) |
| Modelo das tabelas com colunas e relacionamentos | Concluído (seção 5) |
| Decisões técnicas documentadas | Concluído (seção 18) |
| Prompts da camada de IA documentados | Concluído (seção 12) |
| IA com valor real: resumo persistido no banco e visível no relatório | Concluído (seções 12 e 16) |
| Apresentação executiva (6 slides) | Concluído (seção 17) |

---

## 21. Próximos passos

Evoluções possíveis:

1. Implementar ingestão incremental diária.
2. Classificação temática com embeddings e pgvector (Caminho A) para busca semântica.
3. Criar dashboard em Power BI conectado ao Supabase.
4. Criar alertas por tema crítico, como tecnologia, tributário ou sistema financeiro.
5. Enriquecer proposições com autores, relatores, temas específicos e situação detalhada.
6. Multi-cliente: relatórios segmentados por setor de interesse.
