# Radar Legislativo

Pipeline de engenharia de dados desenvolvido para o Projeto Integrador da Pós-graduação em Engenharia de Dados.

O projeto simula uma solução para a consultoria fictícia **Bússola Pública**, cujo objetivo é transformar dados públicos da Câmara dos Deputados em uma base analítica organizada, automatizada e pronta para geração de inteligência executiva.

Repositório: https://github.com/victormoraisp/radar-legislativo

---

## 1. Objetivo

Construir um pipeline completo para:

1. Extrair dados públicos da API da Câmara dos Deputados.
2. Salvar os retornos brutos em JSON para rastreabilidade.
3. Transformar e modelar os dados com Python e Pandas.
4. Carregar tabelas fato e dimensão no Supabase/PostgreSQL.
5. Criar consultas e views analíticas em SQL.
6. Automatizar a entrega diária com n8n.
7. Aplicar IA Generativa para gerar uma análise executiva no relatório enviado por e-mail.

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

```text
API Câmara dos Deputados
        ↓
Extração com Python requests
        ↓
JSON bruto em data/raw
        ↓
Transformação e validação com Pandas
        ↓
CSV e Parquet em data/processed e data/model
        ↓
Carga no Supabase/PostgreSQL
        ↓
Views SQL analíticas
        ↓
n8n
        ↓
OpenAI gera análise executiva
        ↓
E-mail diário automatizado
```

A camada de IA foi implementada na etapa de entrega executiva, preservando os dados originais no banco.

---

## 4. Estrutura do projeto

```text
radar-legislativo/
├── data/
│   ├── raw/
│   │   └── despesas/
│   ├── processed/
│   └── model/
│
├── n8n/
│   └── workflow_radar_legislativo_resumo_diario.json
│
├── sql/
│   ├── 01_create_schema_tables.sql
│   ├── 02_grants.sql
│   ├── 03_validation_queries.sql
│   └── 04_create_views.sql
│
├── apresentacao/
│   └── radar_legislativo_pitch.pptx
│
├── extract_api_camara.py
├── transform_model.py
├── load_supabase.py
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

| Tabela | Descrição |
|---|---|
| `radar.dim_deputado` | Dados cadastrais dos deputados federais |
| `radar.dim_partido` | Dados dos partidos políticos |
| `radar.dim_tema` | Temas disponíveis para proposições |
| `radar.dim_situacao` | Situações possíveis das proposições |

### 5.2 Fatos

| Tabela | Descrição |
|---|---|
| `radar.fato_proposicao` | Proposições extraídas da API da Câmara |
| `radar.fato_votacao` | Votações extraídas da API da Câmara |
| `radar.fato_despesa` | Despesas parlamentares extraídas da API da Câmara |

### 5.3 Observação sobre despesas

A extração de despesas gerou **36.542 registros locais**. Para manter a carga no Supabase mais leve e controlada, foi carregada uma amostra de **3.000 registros** na tabela `radar.fato_despesa`.

Essa decisão preserva a evidência técnica do endpoint de despesas, reduz o tempo de carga e mantém o banco adequado para demonstração.

---

## 6. Resultado da carga final

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

## 7. Instalação

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

## 8. Variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_SERVICE_ROLE_KEY=sua_service_role_key
```

O arquivo `.env` não deve ser enviado para o GitHub.

---

## 9. Criação do banco no Supabase

Execute os arquivos SQL nesta ordem:

```text
sql/01_create_schema_tables.sql
sql/02_grants.sql
sql/04_create_views.sql
```

Depois, no Supabase, confirme que o schema `radar` está exposto na API:

```text
Project Settings > Data API > Exposed schemas
```

O schema `public` contém views espelho para simplificar o consumo via Supabase REST API e n8n.

---

## 10. Execução do pipeline principal

Para rodar o pipeline principal:

```bash
python main_pipeline.py
```

Esse comando executa:

```text
extract_api_camara.py
transform_model.py
load_supabase.py
```

Esse pipeline cobre:

- Deputados
- Partidos
- Proposições
- Votações
- Temas
- Situações

---

## 11. Execução do pipeline de despesas

A frente de despesas foi separada para manter controle de volume.

### 11.1 Extração completa local

```bash
python extract_despesas.py
```

Gera:

```text
data/model/fato_despesa.csv
data/model/fato_despesa.parquet
```

### 11.2 Redução para amostra

```bash
python reduce_despesas.py
```

Gera:

```text
data/model/fato_despesa_amostra.csv
```

### 11.3 Carga da amostra no Supabase

```bash
python load_despesas_supabase.py
```

Carrega 3.000 registros na tabela:

```text
radar.fato_despesa
```

---

## 12. Validação da carga

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

## 13. Views analíticas

O projeto possui views no schema `radar` e views espelho no schema `public`.

Principais views:

| View | Finalidade |
|---|---|
| `radar.vw_top_ultimas_proposicoes` | Lista as últimas proposições para o relatório |
| `radar.vw_top_ultimas_votacoes` | Lista as últimas votações para o relatório |
| `radar.vw_resumo_proposicoes` | Resume proposições por tipo e ano |
| `radar.vw_resumo_votacoes` | Resume votações por órgão |
| `radar.vw_resumo_despesas` | Resume despesas por ano, mês, partido, UF e tipo |

As views públicas equivalentes permitem consumo via Supabase REST API pelo n8n.

---

## 14. Camada de IA Generativa

A IA foi implementada no workflow do n8n, após a leitura das últimas proposições e votações no Supabase.

A IA recebe um contexto textual com os dados legislativos recentes e gera uma **análise executiva breve**, usada como introdução do e-mail diário.

### Prompt utilizado

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

### Decisão técnica

A IA não altera as tabelas fato/dimensão. Ela atua na camada de entrega, transformando dados recentes em uma leitura executiva para tomada de decisão.

Essa escolha preserva rastreabilidade e reduz risco de misturar dado oficial com dado gerado por modelo.

---

## 15. Automação com n8n

O projeto inclui um workflow no n8n para envio automático de um resumo diário.

Arquivo versionado:

```text
n8n/workflow_radar_legislativo_resumo_diario.json
```

Fluxo do workflow:

```text
Schedule Trigger
        ↓
HTTP Request - Últimas proposições
        ↓
HTTP Request - Últimas votações
        ↓
Code - Preparar contexto para IA
        ↓
OpenAI - Gerar análise executiva
        ↓
Code - Montar HTML final
        ↓
Envio de e-mail
```

O workflow consulta as views públicas criadas no Supabase:

```text
public.vw_top_ultimas_proposicoes
public.vw_top_ultimas_votacoes
```

A chave do Supabase não fica salva diretamente no JSON exportado. O workflow utiliza variável de ambiente no n8n:

```text
SUPABASE_ANON_KEY
```

A credencial da OpenAI também deve ser configurada no ambiente ou credencial nativa do n8n.

---

## 16. Apresentação executiva

A apresentação executiva do projeto está prevista no repositório em:

```text
apresentacao/radar_legislativo_pitch.pptx
```

A apresentação segue o formato pitch de até 6 slides:

1. Problema da Bússola Pública
2. Solução proposta
3. Arquitetura do pipeline
4. Modelo de dados e evidências de carga
5. Automação com n8n e IA Generativa
6. Conclusão e próximos passos

---

## 17. Decisões técnicas

| Decisão | Justificativa |
|---|---|
| Supabase/PostgreSQL | Banco gerenciado, simples de demonstrar e compatível com SQL analítico |
| JSON bruto local | Permite reprocessar dados sem chamar a API novamente |
| Pandas para transformação | Ferramenta adequada para limpeza, tipagem e deduplicação |
| Schema `radar` | Isola os objetos do projeto dentro do Supabase |
| Views públicas | Simplificam o consumo pelo n8n via REST API |
| IA no n8n | Aproxima a IA da camada de entrega e torna a demonstração mais visual |
| Amostra de despesas no Supabase | Evita carga excessiva e mantém evidência do endpoint de despesas |

---

## 18. Segurança

O projeto usa `.env` para credenciais sensíveis.

Não devem ser enviados ao GitHub:

- Chaves do Supabase
- Chaves da OpenAI
- Senhas de banco
- Tokens de autenticação

O `.gitignore` protege arquivos sensíveis e artefatos temporários.

---

## 19. Entregáveis atendidos

| Entregável | Status |
|---|---:|
| Repositório GitHub com pipeline | Concluído |
| PostgreSQL/Supabase populado | Concluído |
| Scripts Python de extração, transformação e carga | Concluído |
| JSON bruto salvo localmente | Concluído |
| Modelo fato/dimensão | Concluído |
| Workflow n8n exportado | Concluído |
| IA Generativa aplicada | Concluído |
| README técnico | Concluído |
| Apresentação executiva | Prevista em `apresentacao/radar_legislativo_pitch.pptx` |

---

## 20. Próximos passos

Evoluções possíveis:

1. Implementar ingestão incremental diária.
2. Persistir classificações temáticas geradas por IA.
3. Criar embeddings com pgvector para busca semântica.
4. Criar dashboard em Power BI conectado ao Supabase.
5. Criar alertas por tema crítico, como tecnologia, tributário ou sistema financeiro.
6. Enriquecer proposições com autores, relatores, temas específicos e situação detalhada.