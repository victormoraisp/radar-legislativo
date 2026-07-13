from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "data" / "model"

ARQUIVO_ORIGINAL = MODEL_DIR / "fato_despesa.csv"
ARQUIVO_REDUZIDO = MODEL_DIR / "fato_despesa_amostra.csv"

LIMITE_REGISTROS = 3000


def main():
    df = pd.read_csv(ARQUIVO_ORIGINAL)

    print(f"Arquivo original: {len(df)} linhas")

    df_amostra = (
        df
        .sort_values(
            by=["ano", "mes", "id_deputado"],
            ascending=[False, False, True]
        )
        .head(LIMITE_REGISTROS)
        .copy()
    )

    df_amostra.to_csv(ARQUIVO_REDUZIDO, index=False, encoding="utf-8")

    print(f"Amostra gerada: {len(df_amostra)} linhas")
    print(f"Salvo em: {ARQUIVO_REDUZIDO}")


if __name__ == "__main__":
    main()