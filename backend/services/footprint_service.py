import os
import subprocess
from pathlib import Path


def encontrar_python_kicad():
    env_path = os.getenv("KICAD_PYTHON")

    if env_path and Path(env_path).exists():
        return env_path

    candidatos = [
        r"C:\Program Files\KiCad\10.0\bin\python.exe",
        r"C:\Program Files\KiCad\9.0\bin\python.exe",
        r"C:\Program Files\KiCad\8.0\bin\python.exe",
        r"C:\Program Files\KiCad\7.0\bin\python.exe",
        r"e:\aplicativos\bin\python.exe",
    ]

    for caminho in candidatos:
        if Path(caminho).exists():
            return caminho

    raise FileNotFoundError(
        "Python do KiCad não encontrado. Defina a variável KICAD_PYTHON "
        "apontando para o python.exe do KiCad."
    )


def gerar_csv_footprints(caminho_pcb, caminho_csv_saida):
    caminho_pcb = Path(caminho_pcb)
    caminho_csv_saida = Path(caminho_csv_saida)

    python_kicad = encontrar_python_kicad()

    raiz_backend = Path(__file__).resolve().parents[1]
    worker = raiz_backend / "app" / "kicad" / "footprint_worker.py"

    if not worker.exists():
        raise FileNotFoundError(f"Worker de footprints não encontrado: {worker}")

    comando = [
        python_kicad,
        str(worker),
        str(caminho_pcb),
        str(caminho_csv_saida),
    ]

    resultado = subprocess.run(
        comando,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    if resultado.returncode != 0:
        raise RuntimeError(
            "Erro ao gerar CSV de footprints com Python do KiCad.\n\n"
            f"Comando: {comando}\n\n"
            f"STDOUT:\n{resultado.stdout}\n\n"
            f"STDERR:\n{resultado.stderr}"
        )

    return caminho_csv_saida