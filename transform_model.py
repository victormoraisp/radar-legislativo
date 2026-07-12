from pathlib import Path

import pandas as pd


PROCESSED_DIR = Path("data/processed")
MODEL_DIR = Path("data/model")

MODEL_DIR.mkdir(parents=True, exist_ok=True)


def carregar_csv(nome_arquivo: str) -> pd.DataFrame:
    caminho = PROCESSED_DIR / nome_arquivo
    return pd.read_csv(caminho)


def salvar_tabela(df: pd.DataFrame, nome_tabela: str) -> None:
    caminho_csv = MODEL_DIR / f"{nome_tabela}.csv"
    caminho_parquet = MODEL_DIR / f"{nome_tabela}.parquet"

    df.to_csv(caminho_csv, index=False, encoding="utf-8")
    df.to_parquet(caminho_parquet, index=False)

    print(f"Salvo: {caminho_csv}")
    print(f"Salvo: {caminho_parquet}")


def tratar_texto(df: pd.DataFrame, colunas: list[str]) -> pd.DataFrame:
    for coluna in colunas:
        if coluna in df.columns:
            df[coluna] = df[coluna].fillna("").astype(str).str.strip()
    return df


def modelar_dim_deputado() -> pd.DataFrame:
    df = carregar_csv("dim_deputado.csv")

    df = df.rename(columns={
        "id": "id_deputado",
        "siglapartido": "sigla_partido",
        "siglauf": "sigla_uf",
        "idlegislatura": "id_legislatura",
        "urlfoto": "url_foto"
    })

    df = tratar_texto(df, [
        "nome",
        "sigla_partido",
        "sigla_uf",
        "url_foto",
        "email"
    ])

    df["id_deputado"] = pd.to_numeric(df["id_deputado"], errors="coerce").astype("Int64")
    df["id_legislatura"] = pd.to_numeric(df["id_legislatura"], errors="coerce").astype("Int64")

    return df.drop_duplicates(subset=["id_deputado"])


def modelar_dim_partido() -> pd.DataFrame:
    df = carregar_csv("dim_partido.csv")

    df = df.rename(columns={
        "id": "id_partido"
    })

    df = tratar_texto(df, [
        "sigla",
        "nome",
        "uri"
    ])

    df["id_partido"] = pd.to_numeric(df["id_partido"], errors="coerce").astype("Int64")

    return df.drop_duplicates(subset=["id_partido"])


def modelar_dim_tema() -> pd.DataFrame:
    df = carregar_csv("dim_tema.csv")

    df = df.rename(columns={
        "cod": "cod_tema"
    })

    df = tratar_texto(df, [
        "sigla",
        "nome",
        "descricao"
    ])

    df["cod_tema"] = pd.to_numeric(df["cod_tema"], errors="coerce").astype("Int64")

    return df.drop_duplicates(subset=["cod_tema"])


def modelar_dim_situacao() -> pd.DataFrame:
    df = carregar_csv("dim_situacao.csv")

    df = df.rename(columns={
        "cod": "cod_situacao"
    })

    df = tratar_texto(df, [
        "sigla",
        "nome",
        "descricao"
    ])

    df["cod_situacao"] = pd.to_numeric(df["cod_situacao"], errors="coerce").astype("Int64")

    return df.drop_duplicates(subset=["cod_situacao"])


def modelar_fato_proposicao() -> pd.DataFrame:
    df = carregar_csv("fato_proposicao_base.csv")

    df = df.rename(columns={
        "id": "id_proposicao",
        "siglatipo": "sigla_tipo",
        "codtipo": "cod_tipo",
        "dataapresentacao": "data_apresentacao"
    })

    df = tratar_texto(df, [
        "sigla_tipo",
        "ementa",
        "uri"
    ])

    df["id_proposicao"] = pd.to_numeric(df["id_proposicao"], errors="coerce").astype("Int64")
    df["cod_tipo"] = pd.to_numeric(df["cod_tipo"], errors="coerce").astype("Int64")
    df["numero"] = pd.to_numeric(df["numero"], errors="coerce").astype("Int64")
    df["ano"] = pd.to_numeric(df["ano"], errors="coerce").astype("Int64")
    df["data_apresentacao"] = pd.to_datetime(df["data_apresentacao"], errors="coerce").dt.date


    return df.drop_duplicates(subset=["id_proposicao"])


def modelar_fato_votacao() -> pd.DataFrame:
    df = carregar_csv("fato_votacao.csv")

    df = df.rename(columns={
        "id": "id_votacao",
        "datahoraregistro": "data_hora_registro",
        "siglaorgao": "sigla_orgao",
        "uriorgao": "uri_orgao",
        "urievento": "uri_evento",
        "proposicaoobjeto": "proposicao_objeto",
        "uriproposicaoobjeto": "uri_proposicao_objeto"
    })

    df = tratar_texto(df, [
        "id_votacao",
        "uri",
        "sigla_orgao",
        "uri_orgao",
        "uri_evento",
        "proposicao_objeto",
        "uri_proposicao_objeto",
        "descricao",
        "aprovacao"
    ])

    if "data" in df.columns:
        df["data"] = pd.to_datetime(df["data"], errors="coerce").dt.date

    if "data_hora_registro" in df.columns:
        df["data_hora_registro"] = pd.to_datetime(df["data_hora_registro"], errors="coerce")

    return df.drop_duplicates(subset=["id_votacao"])


def main():
    dim_deputado = modelar_dim_deputado()
    dim_partido = modelar_dim_partido()
    dim_tema = modelar_dim_tema()
    dim_situacao = modelar_dim_situacao()
    fato_proposicao = modelar_fato_proposicao()
    fato_votacao = modelar_fato_votacao()

    salvar_tabela(dim_deputado, "dim_deputado")
    salvar_tabela(dim_partido, "dim_partido")
    salvar_tabela(dim_tema, "dim_tema")
    salvar_tabela(dim_situacao, "dim_situacao")
    salvar_tabela(fato_proposicao, "fato_proposicao")
    salvar_tabela(fato_votacao, "fato_votacao")

    resumo = pd.DataFrame({
        "tabela": [
            "dim_deputado",
            "dim_partido",
            "dim_tema",
            "dim_situacao",
            "fato_proposicao",
            "fato_votacao"
        ],
        "linhas": [
            len(dim_deputado),
            len(dim_partido),
            len(dim_tema),
            len(dim_situacao),
            len(fato_proposicao),
            len(fato_votacao)
        ],
        "colunas": [
            len(dim_deputado.columns),
            len(dim_partido.columns),
            len(dim_tema.columns),
            len(dim_situacao.columns),
            len(fato_proposicao.columns),
            len(fato_votacao.columns)
        ]
    })

    print("\nResumo das tabelas modeladas:")
    print(resumo.to_string(index=False))

    print("\nColunas finais:")
    print("dim_deputado:", list(dim_deputado.columns))
    print("dim_partido:", list(dim_partido.columns))
    print("dim_tema:", list(dim_tema.columns))
    print("dim_situacao:", list(dim_situacao.columns))
    print("fato_proposicao:", list(fato_proposicao.columns))
    print("fato_votacao:", list(fato_votacao.columns))


if __name__ == "__main__":
    main()