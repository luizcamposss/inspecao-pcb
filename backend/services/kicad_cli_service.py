import subprocess
from core.config import KICAD_CLI


class KicadCliError(Exception):
    pass


def executar_comando(comando):
    try:
        resultado = subprocess.run(
            comando,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=True
        )
        return resultado.stdout

    except subprocess.CalledProcessError as erro:
        saida = erro.stdout or ""
        raise KicadCliError(saida.strip() or "Erro ao executar kicad-cli") from erro


def converter_para_kicad(arquivo_entrada, arquivo_saida):
    comando = [
        KICAD_CLI,
        "pcb",
        "import",
        "--format",
        "auto",
        "--output",
        arquivo_saida,
        arquivo_entrada
    ]

    return executar_comando(comando)


def exportar_csv(kicad_pcb_path, csv_saida):
    cmd = [
        KICAD_CLI,
        "pcb",
        "export",
        "pos",

        "--format", "csv",
        "--units", "mm",

        "--use-drill-file-origin",
        "--bottom-negate-x",

        "--side", "both",

        "--output", csv_saida,
        kicad_pcb_path
    ]

    return executar_comando(cmd)