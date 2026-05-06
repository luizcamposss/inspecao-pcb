import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
PROJETOS_DIR = DATA_DIR / "projetos"

KICAD_CLI = os.getenv(
    "KICAD_CLI",
    r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
)

PROJETOS_DIR.mkdir(parents=True, exist_ok=True)


def normalizar_nome_projeto(nome: str) -> str: return nome.strip().lower()


def get_projeto_dir(nome_projeto: str) -> Path:
    return PROJETOS_DIR / normalizar_nome_projeto(nome_projeto)


def get_project_paths(nome_projeto: str):
    projeto_dir = get_projeto_dir(nome_projeto)

    paths = {
        "base": projeto_dir,
        "original": projeto_dir / "original",
        "convert": projeto_dir / "convert",
        "pcb": projeto_dir / "pcb",
        "csv": projeto_dir / "csv",
        "uploads": projeto_dir / "uploads",
        "output": projeto_dir / "output",
        "temp": projeto_dir / "temp",
    }

    for pasta in paths.values():
        pasta.mkdir(parents=True, exist_ok=True)

    return paths