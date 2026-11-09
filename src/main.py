from __future__ import annotations

import argparse
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from rules import build_child_final, classify_dirty


BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_FOLDER = BASE_DIR / "data" / "original"
WORK_FOLDER = BASE_DIR / "data" / "trabalho"
OUTPUT_FOLDER = BASE_DIR / "data" / "final"

UNUSED_COLUMNS = ["Payment Volume", "Rate - %"]
DUPLICATE_KEY = ["Invoice Number", "Child", "Product Description"]
REQUIRED_COLUMNS = {*DUPLICATE_KEY, "MID", "Total Amount Due"}
AUDIT_COLUMNS = ["child_original", "mid_original", "process_date"]


@dataclass(slots=True)
class PipelineResult:
    total_rows: int
    valid_rows: int
    dirty_rows: int
    success: bool


def get_input_file() -> Path:
    files = sorted(path for path in INPUT_FOLDER.glob("*.xlsx") if not path.name.startswith("~$"))
    if not files:
        raise FileNotFoundError(f"Nenhum arquivo .xlsx encontrado em {INPUT_FOLDER}")
    if len(files) > 1:
        raise ValueError(f"Há mais de um arquivo em {INPUT_FOLDER}. Informe --input-file.")
    return files[0]


def process_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    missing = REQUIRED_COLUMNS.difference(df.columns)
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes: {', '.join(sorted(missing))}")

    df = df.drop(columns=UNUSED_COLUMNS, errors="ignore")
    treated_rows = []
    dirty_rows = []
    process_date = datetime.now()

    for row in df.to_dict(orient="records"):
        child = row["Child"]
        mid = row["MID"]
        is_dirty, reason = classify_dirty(child, mid, row["Total Amount Due"])
        if not is_dirty:
            child_final = build_child_final(child, row["Product Description"])
            if child_final in {"braspag", "braspag_"}:
                is_dirty, reason = True, "child_invalido"

        if is_dirty:
            dirty_rows.append({**row, "motivo_sujeira": reason})
            continue

        treated_rows.append({
            **row,
            "Child": child_final,
            "MID": child_final,
            "child_original": child,
            "mid_original": mid,
            "process_date": process_date,
        })

    return (
        pd.DataFrame(treated_rows, columns=[*df.columns, *AUDIT_COLUMNS]),
        pd.DataFrame(dirty_rows, columns=[*df.columns, "motivo_sujeira"]),
    )


def find_duplicate_candidates(treated: pd.DataFrame) -> pd.DataFrame:
    candidates = treated.loc[treated.duplicated(DUPLICATE_KEY, keep=False)].copy()
    candidates["ocorrencias_chave"] = candidates.groupby(
        DUPLICATE_KEY, dropna=False
    )["Child"].transform("size")
    return candidates


def write_workbook(path: Path, sheets: dict[str, pd.DataFrame]) -> None:
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, sheet in sheets.items():
            sheet.to_excel(writer, sheet_name=name, index=False)


def run_pipeline(input_file: Path | None = None) -> PipelineResult:
    input_file = input_file if input_file is not None else get_input_file()
    work_file = WORK_FOLDER / "antifraude_trabalho.xlsx"
    final_file = OUTPUT_FOLDER / "antifraude_vf.xlsx"
    if input_file.resolve() in {work_file.resolve(), final_file.resolve()}:
        raise ValueError("O arquivo de entrada deve ser diferente dos arquivos de saída.")

    logging.info("Lendo %s", input_file)
    df = pd.read_excel(input_file, engine="openpyxl")
    treated, dirty = process_dataframe(df)
    duplicates = find_duplicate_candidates(treated)

    WORK_FOLDER.mkdir(parents=True, exist_ok=True)
    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
    # Grava ambos os arquivos antes de substituir as saídas existentes.
    with TemporaryDirectory(dir=WORK_FOLDER) as work_dir, TemporaryDirectory(dir=OUTPUT_FOLDER) as final_dir:
        work_tmp = Path(work_dir) / work_file.name
        final_tmp = Path(final_dir) / final_file.name
        write_workbook(work_tmp, {"TRATADO": treated, "SUJEIRA": dirty})
        write_workbook(final_tmp, {
            "BASE_COMPLETA": treated,
            "CHECK_DUPLICIDADE": duplicates,
            "SUJEIRA": dirty,
        })
        work_tmp.replace(work_file)
        final_tmp.replace(final_file)

    logging.info("Linhas em CHECK_DUPLICIDADE: %s", len(duplicates))
    return PipelineResult(len(df), len(treated), len(dirty), True)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    parser = argparse.ArgumentParser(description="Prepara a base mensal de faturamento antifraude.")
    parser.add_argument("--input-file", type=Path, help="Arquivo Excel de origem.")
    args = parser.parse_args()
    try:
        result = run_pipeline(args.input_file)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Erro: {exc}\n")

    logging.info(
        "Pipeline concluído | Total=%s | Válidos=%s | Sujeira=%s",
        result.total_rows,
        result.valid_rows,
        result.dirty_rows,
    )


if __name__ == "__main__":
    main()
