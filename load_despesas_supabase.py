import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from supabase import create_client


BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env", override=True)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

MODEL_DIR = BASE_DIR / "data" / "model"
SCHEMA = "radar"

if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL não encontrada no .env")

if not SUPABASE_SERVICE_ROLE_KEY:
    raise ValueError("SUPABASE_SERVICE_ROLE_KEY não encontrada no .env")


supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def limpar_valores_para_json(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    for coluna in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[coluna]):
            df[coluna] = df[coluna].dt.strftime("%Y-%m-%d")

    df = df.astype(object)
    df = df.where(pd.notnull(df), None)

    return df


def carregar_csv() -> pd.DataFrame:
    caminho = MODEL_DIR / "fato_despesa_amostra.csv"

    df = pd.read_csv(caminho)

    colunas_bigint = [
        "id_deputado",
        "ano",
        "mes",
        "cod_documento",
        "cod_tipo_documento"
    ]

    for coluna in colunas_bigint:
        if coluna in df.columns:
            df[coluna] = (
                pd.to_numeric(df[coluna], errors="coerce")
                .astype("Int64")
            )

    colunas_numeric = [
        "valor_documento",
        "valor_glosa",
        "valor_liquido"
    ]

    for coluna in colunas_numeric:
        if coluna in df.columns:
            df[coluna] = pd.to_numeric(df[coluna], errors="coerce")

    if "data_documento" in df.columns:
        df["data_documento"] = (
            pd.to_datetime(df["data_documento"], errors="coerce")
            .dt.strftime("%Y-%m-%d")
        )

    return limpar_valores_para_json(df)


def limpar_tabela() -> None:
    print("Limpando radar.fato_despesa...")

    (
        supabase
        .schema(SCHEMA)
        .table("fato_despesa")
        .delete()
        .neq("id_despesa", "__valor_impossivel__")
        .execute()
    )

    print("Tabela fato_despesa limpa.")


def inserir_em_lotes(df: pd.DataFrame, lote: int = 500) -> None:
    total = len(df)

    print(f"Carregando fato_despesa: {total} linhas")

    for inicio in range(0, total, lote):
        fim = min(inicio + lote, total)

        registros = df.iloc[inicio:fim].to_dict(orient="records")

        (
            supabase
            .schema(SCHEMA)
            .table("fato_despesa")
            .upsert(registros)
            .execute()
        )

        print(f"fato_despesa: linhas {inicio + 1} até {fim} carregadas")


def main():
    df = carregar_csv()

    limpar_tabela()
    inserir_em_lotes(df)

    print("Carga de despesas finalizada com sucesso.")


if __name__ == "__main__":
    main()