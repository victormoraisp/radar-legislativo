import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from supabase import create_client


load_dotenv(override=True)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "data" / "model"
SCHEMA = "radar"

if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL não encontrada no .env")

if not SUPABASE_SERVICE_ROLE_KEY:
    raise ValueError("SUPABASE_SERVICE_ROLE_KEY não encontrada no .env")


supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def limpar_valores_para_json(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converte valores incompatíveis com JSON/PostgREST:
    - NaN/NaT/pd.NA -> None
    - datas/timestamps -> string ISO
    """
    df = df.copy()

    for coluna in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[coluna]):
            df[coluna] = df[coluna].dt.strftime("%Y-%m-%d %H:%M:%S")

    df = df.astype(object)
    df = df.where(pd.notnull(df), None)

    return df


def carregar_csv(nome_arquivo: str) -> pd.DataFrame:
    caminho = MODEL_DIR / nome_arquivo
    df = pd.read_csv(caminho)

    return limpar_valores_para_json(df)


def inserir_em_lotes(nome_tabela: str, df: pd.DataFrame, lote: int = 500) -> None:
    total = len(df)

    print(f"\nCarregando {nome_tabela}: {total} linhas")

    for inicio in range(0, total, lote):
        fim = min(inicio + lote, total)
        registros = df.iloc[inicio:fim].to_dict(orient="records")

        (
            supabase
            .schema(SCHEMA)
            .table(nome_tabela)
            .upsert(registros)
            .execute()
        )

        print(f"{nome_tabela}: linhas {inicio + 1} até {fim} carregadas")


def limpar_tabelas_supabase() -> None:
    """
    Limpa as tabelas antes da carga para evitar sobras de execuções anteriores.
    Usa filtros nas chaves primárias porque o PostgREST exige um filtro para delete.
    """
    print("\nLimpando tabelas no Supabase...")

    tabelas = [
        {
            "nome": "fato_votacao",
            "pk": "id_votacao",
            "valor_impossivel": "__valor_impossivel__"
        },
        {
            "nome": "fato_proposicao",
            "pk": "id_proposicao",
            "valor_impossivel": -1
        },
        {
            "nome": "dim_situacao",
            "pk": "cod_situacao",
            "valor_impossivel": -1
        },
        {
            "nome": "dim_tema",
            "pk": "cod_tema",
            "valor_impossivel": -1
        },
        {
            "nome": "dim_partido",
            "pk": "id_partido",
            "valor_impossivel": -1
        },
        {
            "nome": "dim_deputado",
            "pk": "id_deputado",
            "valor_impossivel": -1
        },
    ]

    for tabela in tabelas:
        (
            supabase
            .schema(SCHEMA)
            .table(tabela["nome"])
            .delete()
            .neq(tabela["pk"], tabela["valor_impossivel"])
            .execute()
        )

        print(f"Tabela limpa: {tabela['nome']}")


def main():

    limpar_tabelas_supabase()

    ordem_carga = [
        ("dim_deputado", "dim_deputado.csv"),
        ("dim_partido", "dim_partido.csv"),
        ("dim_tema", "dim_tema.csv"),
        ("dim_situacao", "dim_situacao.csv"),
        ("fato_proposicao", "fato_proposicao.csv"),
        ("fato_votacao", "fato_votacao.csv"),
    ]

    for nome_tabela, nome_arquivo in ordem_carga:
        df = carregar_csv(nome_arquivo)
        inserir_em_lotes(nome_tabela, df)

    print("\nCarga finalizada com sucesso.")


if __name__ == "__main__":
    main()