from pathlib import Path
from datetime import datetime
import json
import time

import requests
import pandas as pd


BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")

RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def salvar_json(nome_arquivo: str, conteudo: dict | list) -> None:
    """
    Salva o retorno bruto da API em JSON.
    """
    caminho = RAW_DIR / nome_arquivo

    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(conteudo, arquivo, ensure_ascii=False, indent=2)


def get_api(endpoint: str, params: dict | None = None) -> dict:
    """
    Faz uma requisição GET simples na API da Câmara.
    """
    url = f"{BASE_URL}/{endpoint}"

    headers = {
        "Accept": "application/json"
    }

    response = requests.get(
        url,
        params=params,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


def get_paginated(endpoint: str, params: dict | None = None, itens: int = 100) -> list[dict]:
    """
    Consome endpoints paginados da API da Câmara.
    A API retorna os dados dentro da chave 'dados'.
    """
    todos_registros = []
    pagina = 1

    params_base = params.copy() if params else {}
    params_base["itens"] = itens

    while True:
        params_base["pagina"] = pagina

        print(f"Extraindo {endpoint} | página {pagina}")

        resposta = get_api(endpoint, params=params_base)
        dados = resposta.get("dados", [])

        if not dados:
            break

        todos_registros.extend(dados)

        salvar_json(
            nome_arquivo=f"{endpoint.replace('/', '_')}_pagina_{pagina}.json",
            conteudo=resposta
        )

        if len(dados) < itens:
            break

        pagina += 1
        time.sleep(0.3)

    return todos_registros


def criar_dataframe(registros: list[dict]) -> pd.DataFrame:
    """
    Cria DataFrame padronizado a partir de uma lista de dicionários.
    """
    df = pd.DataFrame(registros)

    if df.empty:
        return df

    df.columns = (
        df.columns
        .str.strip()
        .str.replace(" ", "_")
        .str.replace("-", "_")
        .str.lower()
    )

    return df


def extrair_deputados() -> pd.DataFrame:
    registros = get_paginated("deputados")

    df = criar_dataframe(registros)

    colunas = [
        "id",
        "nome",
        "siglapartido",
        "siglauf",
        "idlegislatura",
        "urlfoto",
        "email"
    ]

    colunas_existentes = [col for col in colunas if col in df.columns]

    return df[colunas_existentes]


def extrair_partidos() -> pd.DataFrame:
    registros = get_paginated("partidos")

    df = criar_dataframe(registros)

    colunas = [
        "id",
        "sigla",
        "nome",
        "uri"
    ]

    colunas_existentes = [col for col in colunas if col in df.columns]

    return df[colunas_existentes]


def extrair_proposicoes(data_inicio: str, data_fim: str) -> pd.DataFrame:
    params = {
        "dataInicio": data_inicio,
        "dataFim": data_fim,
        "ordem": "ASC",
        "ordenarPor": "id"
    }

    registros = get_paginated("proposicoes", params=params)

    df = criar_dataframe(registros)

    colunas = [
        "id",
        "siglatipo",
        "codtipo",
        "numero",
        "ano",
        "ementa",
        "dataapresentacao",
        "uri"
    ]

    colunas_existentes = [col for col in colunas if col in df.columns]

    return df[colunas_existentes]


def extrair_votacoes(data_inicio: str | None = None, data_fim: str | None = None) -> pd.DataFrame:
    params = {
        "ordem": "ASC",
        "ordenarPor": "dataHoraRegistro"
    }

    if data_inicio:
        params["dataInicio"] = data_inicio

    if data_fim:
        params["dataFim"] = data_fim

    registros = get_paginated("votacoes", params=params)

    df = criar_dataframe(registros)

    colunas = [
        "id",
        "uri",
        "data",
        "datahoraregistro",
        "siglaorgao",
        "uriOrgao",
        "descricao",
        "aprovacao"
    ]

    colunas_existentes = [col for col in colunas if col.lower() in df.columns]

    return df


def extrair_temas_proposicoes() -> pd.DataFrame:
    resposta = get_api("referencias/proposicoes/codTema")

    salvar_json(
        nome_arquivo="referencias_proposicoes_codTema.json",
        conteudo=resposta
    )

    return criar_dataframe(resposta.get("dados", []))


def extrair_situacoes_proposicao() -> pd.DataFrame:
    resposta = get_api("referencias/situacoesProposicao")

    salvar_json(
        nome_arquivo="referencias_situacoesProposicao.json",
        conteudo=resposta
    )

    return criar_dataframe(resposta.get("dados", []))


def salvar_dataframe(df: pd.DataFrame, nome_tabela: str) -> None:
    """
    Salva DataFrame em CSV e Parquet.
    """
    caminho_csv = PROCESSED_DIR / f"{nome_tabela}.csv"
    caminho_parquet = PROCESSED_DIR / f"{nome_tabela}.parquet"

    df.to_csv(caminho_csv, index=False, encoding="utf-8")
    df.to_parquet(caminho_parquet, index=False)

    print(f"Salvo: {caminho_csv}")
    print(f"Salvo: {caminho_parquet}")


def main():
    data_inicio = "2026-04-01"
    data_fim = "2026-04-30"

    print("Extraindo deputados...")
    df_deputados = extrair_deputados()

    print("Extraindo partidos...")
    df_partidos = extrair_partidos()

    print("Extraindo proposições...")
    df_proposicoes = extrair_proposicoes(data_inicio, data_fim)

    print("Extraindo votações...")
    df_votacoes = extrair_votacoes(data_inicio, data_fim)

    print("Extraindo temas...")
    df_temas = extrair_temas_proposicoes()

    print("Extraindo situações das proposições...")
    df_situacoes = extrair_situacoes_proposicao()

    salvar_dataframe(df_deputados, "dim_deputado")
    salvar_dataframe(df_partidos, "dim_partido")
    salvar_dataframe(df_proposicoes, "fato_proposicao_base")
    salvar_dataframe(df_votacoes, "fato_votacao")
    salvar_dataframe(df_temas, "dim_tema")
    salvar_dataframe(df_situacoes, "dim_situacao")

    print("\nResumo dos DataFrames:")
    print(f"Deputados: {df_deputados.shape}")
    print(f"Partidos: {df_partidos.shape}")
    print(f"Proposições: {df_proposicoes.shape}")
    print(f"Votações: {df_votacoes.shape}")
    print(f"Temas: {df_temas.shape}")
    print(f"Situações: {df_situacoes.shape}")

    print("\nPrévia de proposições:")
    print("\nResumo dos DataFrames:")
    resumo = pd.DataFrame({
        "tabela": [
            "dim_deputado",
            "dim_partido",
            "fato_proposicao_base",
            "fato_votacao",
            "dim_tema",
            "dim_situacao"
        ],
        "linhas": [
            len(df_deputados),
            len(df_partidos),
            len(df_proposicoes),
            len(df_votacoes),
            len(df_temas),
            len(df_situacoes)
        ],
        "colunas": [
            len(df_deputados.columns),
            len(df_partidos.columns),
            len(df_proposicoes.columns),
            len(df_votacoes.columns),
            len(df_temas.columns),
            len(df_situacoes.columns)
        ]
    })

    print(resumo.to_string(index=False))

    print("\nColunas por DataFrame:")
    print("dim_deputado:", list(df_deputados.columns))
    print("dim_partido:", list(df_partidos.columns))
    print("fato_proposicao_base:", list(df_proposicoes.columns))
    print("fato_votacao:", list(df_votacoes.columns))
    print("dim_tema:", list(df_temas.columns))
    print("dim_situacao:", list(df_situacoes.columns))


if __name__ == "__main__":
    main()