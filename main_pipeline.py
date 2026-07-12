import subprocess
import sys
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


def executar_script(nome_script: str) -> None:
    caminho_script = BASE_DIR / nome_script

    print("\n" + "=" * 80)
    print(f"Executando: {caminho_script}")
    print("=" * 80)

    if not caminho_script.exists():
        raise FileNotFoundError(f"Script não encontrado: {caminho_script}")

    resultado = subprocess.run(
        [sys.executable, str(caminho_script)],
        cwd=BASE_DIR,
        capture_output=False,
        text=True
    )

    if resultado.returncode != 0:
        raise RuntimeError(f"Erro ao executar {nome_script}")

    print(f"Finalizado: {nome_script}")


def main():
    inicio = datetime.now()

    print("=" * 80)
    print("PIPELINE RADAR LEGISLATIVO")
    print(f"Início: {inicio.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Pasta base: {BASE_DIR}")
    print("=" * 80)

    executar_script("extract_api_camara.py")
    executar_script("transform_model.py")
    executar_script("load_supabase.py")

    fim = datetime.now()
    duracao = fim - inicio

    print("\n" + "=" * 80)
    print("Pipeline finalizado com sucesso.")
    print(f"Fim: {fim.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Duração: {duracao}")
    print("=" * 80)


if __name__ == "__main__":
    main()