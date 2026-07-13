from pathlib import Path
import json
import time
import hashlib

import requests
import pandas as pd


BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "data" / "raw" / "despesas"
MODEL_DIR = BASE_DIR / "data" / "model"

RAW_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR.mkdir(parents=True, exist_ok=True)


def salvar_json(nome_arquivo: str, conteudo: dict) -> None:
    caminho = RAW_DIR / nome_arquivo

    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(conteudo, arquivo, ensure_ascii=False, indent=2)


def get_api(endpoint: str, params: dict | None = None) -> dict:
    url = f"{BASE_URL}/{endpoint}"

    response = requests.get(
        url,
        params=params,
        headers={"Accept": "application/json"},
        timeout=30
    )

    response.raise_for_status()
    return response.json()


def get_paginated(endpoint: str, params: dict | None = None, itens: int = 100) -> list[dict]:
    todos_registros = []
    pagina = 1

    params_base = params.copy() if params else {}
    params_base["itens"] = itens

    while True:
        params_base["pagina"] = pagina

        resposta = get_api(endpoint, params=params_base)
        dados = resposta.get("dados", [])

        if not dados:
            break

        todos_registros.extend(dados)

        nome_arquivo = f"{endpoint.replace('/', '_')}_pagina_{pagina}.json"
        salvar_json(nome_arquivo, resposta)

        if len(dados) < itens:
            break

        pagina += 1
        time.sleep(0.2)

    return todos_registros


def carregar_deputados() -> pd.DataFrame:
    caminho = MODEL_DIR / "dim_deputado.csv"
    return pd.read_csv(caminho)


def gerar_id_despesa(linha: pd.Series) -> str:
    texto = "|".join([
        str(linha.get("id_deputado", "")),
        str(linha.get("ano", "")),
        str(linha.get("mes", "")),
        str(linha.get("cod_documento", "")),
        str(linha.get("num_documento", "")),
        str(linha.get("tipo_despesa", "")),
        str(linha.get("valor_liquido", "")),
    ])

    return hashlib.md5(texto.encode("utf-8")).hexdigest()


def extrair_despesas_deputado(id_deputado: int, ano: int, meses: list[int]) -> list[dict]:
    registros = []

    for mes in meses:
        print(f"Extraindo despesas deputado {id_deputado} | ano {ano} | mês {mes}")

        params = {
            "ano": ano,
            "mes": mes,
            "ordem": "ASC",
            "ordenarPor": "ano"
        }

        try:
            dados = get_paginated(
                endpoint=f"deputados/{id_deputado}/despesas",
                params=params,
                itens=100
            )

            registros.extend(dados)

        except Exception as erro:
            print(f"Erro ao extrair deputado {id_deputado}, mês {mes}: {erro}")

    return registros


def main():
    ano = 2026
    meses = [4, 5]

    deputados = carregar_deputados()

    todos = []

    for _, deputado in deputados.iterrows():
        id_deputado = int(deputado["id_deputado"])

        despesas = extrair_despesas_deputado(
            id_deputado=id_deputado,
            ano=ano,
            meses=meses
        )

        for despesa in despesas:
            despesa["id_deputado"] = id_deputado
            despesa["nome_deputado"] = deputado.get("nome")
            despesa["sigla_partido"] = deputado.get("sigla_partido")
            despesa["sigla_uf"] = deputado.get("sigla_uf")

        todos.extend(despesas)

    df = pd.DataFrame(todos)

    if df.empty:
        print("Nenhuma despesa encontrada.")
        return

    df = df.rename(columns={
        "ano": "ano",
        "mes": "mes",
        "tipoDespesa": "tipo_despesa",
        "codDocumento": "cod_documento",
        "tipoDocumento": "tipo_documento",
        "codTipoDocumento": "cod_tipo_documento",
        "dataDocumento": "data_documento",
        "numDocumento": "num_documento",
        "valorDocumento": "valor_documento",
        "valorGlosa": "valor_glosa",
        "valorLiquido": "valor_liquido",
        "nomeFornecedor": "nome_fornecedor",
        "cnpjCpfFornecedor": "cnpj_cpf_fornecedor",
        "urlDocumento": "url_documento"
    })

    colunas_finais = [
        "id_deputado",
        "nome_deputado",
        "sigla_partido",
        "sigla_uf",
        "ano",
        "mes",
        "tipo_despesa",
        "cod_documento",
        "tipo_documento",
        "cod_tipo_documento",
        "data_documento",
        "num_documento",
        "valor_documento",
        "valor_glosa",
        "valor_liquido",
        "nome_fornecedor",
        "cnpj_cpf_fornecedor",
        "url_documento"
    ]

    for coluna in colunas_finais:
        if coluna not in df.columns:
            df[coluna] = None

    df = df[colunas_finais].copy()

    df["ano"] = pd.to_numeric(df["ano"], errors="coerce").astype("Int64")
    df["mes"] = pd.to_numeric(df["mes"], errors="coerce").astype("Int64")
    df["cod_documento"] = pd.to_numeric(df["cod_documento"], errors="coerce").astype("Int64")
    df["cod_tipo_documento"] = pd.to_numeric(df["cod_tipo_documento"], errors="coerce").astype("Int64")
    df["data_documento"] = pd.to_datetime(df["data_documento"], errors="coerce").dt.date

    for coluna in ["valor_documento", "valor_glosa", "valor_liquido"]:
        df[coluna] = pd.to_numeric(df[coluna], errors="coerce")

    df["id_despesa"] = df.apply(gerar_id_despesa, axis=1)

    df = df[
        [
            "id_despesa",
            "id_deputado",
            "nome_deputado",
            "sigla_partido",
            "sigla_uf",
            "ano",
            "mes",
            "tipo_despesa",
            "cod_documento",
            "tipo_documento",
            "cod_tipo_documento",
            "data_documento",
            "num_documento",
            "valor_documento",
            "valor_glosa",
            "valor_liquido",
            "nome_fornecedor",
            "cnpj_cpf_fornecedor",
            "url_documento"
        ]
    ]

    df = df.drop_duplicates(subset=["id_despesa"])

    caminho_csv = MODEL_DIR / "fato_despesa.csv"
    caminho_parquet = MODEL_DIR / "fato_despesa.parquet"

    df.to_csv(caminho_csv, index=False, encoding="utf-8")
    df.to_parquet(caminho_parquet, index=False)

    print("\nDespesas extraídas com sucesso.")
    print(f"Linhas: {len(df)}")
    print(f"Colunas: {len(df.columns)}")
    print(f"Salvo: {caminho_csv}")
    print(f"Salvo: {caminho_parquet}")


if __name__ == "__main__":
    main()