"""
Camada de IA - Caminho B do desafio.

Gera um resumo executivo por proposição usando a API da OpenAI
e persiste o resultado na coluna resumo_ia de radar.fato_proposicao.

Controle de custo:
- Rode primeiro com LIMITE=10 (padrão) e observe o custo estimado impresso.
- Depois aumente: python enrich_ia_resumo.py 100
- Para processar tudo:  python enrich_ia_resumo.py all
"""

import os
import sys
import time
from datetime import datetime

from dotenv import load_dotenv
from openai import OpenAI
from supabase import create_client


load_dotenv(override=True)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

SCHEMA = "radar"
MODELO = "gpt-4.1-mini"

# Preço de referência do gpt-4.1-mini (USD por 1M tokens). Ajuste se mudar.
PRECO_INPUT_1M = 0.40
PRECO_OUTPUT_1M = 1.60

PROMPT_SISTEMA = (
    "Você é um analista legislativo sênior da consultoria Bússola Pública. "
    "Resuma a proposição a seguir em até 3 linhas, em linguagem clara para um executivo. "
    "Não invente informações. Não use markdown. Responda apenas o resumo."
)


def validar_ambiente() -> None:
    faltando = [
        nome for nome, valor in [
            ("SUPABASE_URL", SUPABASE_URL),
            ("SUPABASE_SERVICE_ROLE_KEY", SUPABASE_SERVICE_ROLE_KEY),
            ("OPENAI_API_KEY", OPENAI_API_KEY),
        ] if not valor
    ]
    if faltando:
        raise ValueError(f"Variáveis ausentes no .env: {', '.join(faltando)}")


def buscar_proposicoes_sem_resumo(supabase, limite: int | None) -> list[dict]:
    """
    Busca proposições que ainda não têm resumo_ia, das mais recentes para as mais antigas.
    """
    consulta = (
        supabase
        .schema(SCHEMA)
        .table("fato_proposicao")
        .select("id_proposicao, sigla_tipo, numero, ano, ementa")
        .is_("resumo_ia", "null")
        .neq("ementa", "")
        .order("data_apresentacao", desc=True)
    )

    if limite:
        consulta = consulta.limit(limite)

    resposta = consulta.execute()
    return resposta.data or []


def gerar_resumo(openai_client: OpenAI, proposicao: dict) -> tuple[str, int, int]:
    """
    Gera o resumo executivo de uma proposição.
    Retorna (resumo, tokens_input, tokens_output).
    """
    identificacao = (
        f"{proposicao.get('sigla_tipo', '')} "
        f"{proposicao.get('numero', '')}/{proposicao.get('ano', '')}"
    )

    resposta = openai_client.chat.completions.create(
        model=MODELO,
        messages=[
            {"role": "system", "content": PROMPT_SISTEMA},
            {"role": "user", "content": f"Proposição {identificacao}.\nEmenta: {proposicao['ementa']}"},
        ],
        temperature=0.2,
        max_tokens=200,
    )

    resumo = resposta.choices[0].message.content.strip()
    uso = resposta.usage

    return resumo, uso.prompt_tokens, uso.completion_tokens


def salvar_resumo(supabase, id_proposicao: int, resumo: str) -> None:
    (
        supabase
        .schema(SCHEMA)
        .table("fato_proposicao")
        .update({
            "resumo_ia": resumo,
            "resumo_ia_gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })
        .eq("id_proposicao", id_proposicao)
        .execute()
    )


def main():
    validar_ambiente()

    argumento = sys.argv[1] if len(sys.argv) > 1 else "10"
    limite = None if argumento.lower() == "all" else int(argumento)

    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    openai_client = OpenAI(api_key=OPENAI_API_KEY)

    proposicoes = buscar_proposicoes_sem_resumo(supabase, limite)

    if not proposicoes:
        print("Nenhuma proposição pendente de resumo.")
        return

    print(f"Proposições a resumir: {len(proposicoes)} (modelo: {MODELO})")

    total_input = 0
    total_output = 0
    sucesso = 0
    falhas = 0

    for indice, proposicao in enumerate(proposicoes, start=1):
        try:
            resumo, tokens_in, tokens_out = gerar_resumo(openai_client, proposicao)
            salvar_resumo(supabase, proposicao["id_proposicao"], resumo)

            total_input += tokens_in
            total_output += tokens_out
            sucesso += 1

            print(f"[{indice}/{len(proposicoes)}] id {proposicao['id_proposicao']} ok")

        except Exception as erro:
            falhas += 1
            print(f"[{indice}/{len(proposicoes)}] id {proposicao['id_proposicao']} FALHOU: {erro}")

        time.sleep(0.2)

    custo = (total_input / 1_000_000) * PRECO_INPUT_1M + (total_output / 1_000_000) * PRECO_OUTPUT_1M

    print("\n" + "=" * 60)
    print(f"Resumos gerados: {sucesso} | Falhas: {falhas}")
    print(f"Tokens input: {total_input} | Tokens output: {total_output}")
    print(f"Custo estimado desta execução: US$ {custo:.4f}")

    if sucesso:
        custo_por_item = custo / sucesso
        print(f"Custo médio por proposição: US$ {custo_por_item:.5f}")
        print(f"Projeção para 1.000 proposições: US$ {custo_por_item * 1000:.2f}")
        print(f"Projeção para 16.082 proposições: US$ {custo_por_item * 16082:.2f}")

    print("=" * 60)


if __name__ == "__main__":
    main()
