from __future__ import annotations
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import pandas as pd
from rules import build_child_final, classify_dirty
import argparse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FOLDER = BASE_DIR / "data" / "original"
WORK_FOLDER = BASE_DIR / "data" / "trabalho"
OUTPUT_FOLDER = BASE_DIR / "data" / "final"

WORK_FOLDER.mkdir(parents=True, exist_ok=True)
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)


UNUSED_COLUMNS = {
    "Payment Volume",
    "Rate - %",
}


@dataclass(slots=True)
class PipelineResult:
    total_rows: int
    valid_rows: int
    dirty_rows: int
    success: bool


def get_input_file() -> Path:
    files = sorted(
        INPUT_FOLDER.glob("*.xlsx")
    )

    if not files:
        raise FileNotFoundError(
            f"Nenhum arquivo encontrado em: {INPUT_FOLDER}"
        )

    logging.info(
        "Arquivo encontrado: %s",
        files[0].name,
    )

    return files[0]


def load_data(
    file_path: Path,
) -> pd.DataFrame:
    logging.info(
        "Lendo arquivo: %s",
        file_path,
    )

    return pd.read_excel(
        file_path,
        engine="openpyxl",
    )


def drop_unused_columns(
    df: pd.DataFrame,
) -> pd.DataFrame:
    return df.drop(
        columns=[
            column
            for column in UNUSED_COLUMNS
            if column in df.columns
        ],
        errors="ignore",
    )


def process_dataframe(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    valid_rows: list[pd.Series] = []
    dirty_rows: list[pd.Series] = []

    for _, row in df.iterrows():
        child = row.get("Child", "")
        mid = row.get("MID", "")
        product_description = row.get(
            "Product Description",
            "",
        )
        amount = row.get(
            "Total Amount Due",
            0,
        )

        is_dirty, reason = classify_dirty(
            child=child,
            mid=mid,
            total_amount_due=amount,
        )

        if is_dirty:
            dirty_row = row.copy()
            dirty_row["motivo_sujeira"] = reason

            dirty_rows.append(
                dirty_row
            )

            continue

        child_final = build_child_final(
            child=child,
            product_description=product_description,
        )

        valid_row = row.copy()

        valid_row["child_original"] = child
        valid_row["mid_original"] = mid

        valid_row["Child"] = child_final
        valid_row["MID"] = child_final

        valid_row["process_date"] = datetime.now()

        valid_rows.append(
            valid_row
        )

    return (
        pd.DataFrame(valid_rows),
        pd.DataFrame(dirty_rows),
    )


def save_workbook(
    treated_df: pd.DataFrame,
    dirty_df: pd.DataFrame,
) -> None:
    output_file = (
        WORK_FOLDER
        / "antifraude_trabalho.xlsx"
    )

    with pd.ExcelWriter(
        output_file,
        engine="openpyxl",
    ) as writer:
        treated_df.to_excel(
            writer,
            sheet_name="TRATADO",
            index=False,
        )

        dirty_df.to_excel(
            writer,
            sheet_name="SUJEIRA",
            index=False,
        )

    logging.info(
        "Workbook trabalho criado: %s",
        output_file,
    )


def save_vf(
    treated_df: pd.DataFrame,
    dirty_df: pd.DataFrame,
) -> None:
    output_file = (
        OUTPUT_FOLDER
        / "antifraude_vf.xlsx"
    )

    with pd.ExcelWriter(
        output_file,
        engine="openpyxl",
    ) as writer:
        treated_df.to_excel(
            writer,
            sheet_name="BASE_COMPLETA",
            index=False,
        )

        pd.DataFrame().to_excel(
            writer,
            sheet_name="CHECK_DUPLICIDADE",
            index=False,
        )

        dirty_df.to_excel(
            writer,
            sheet_name="SUJEIRA",
            index=False,
        )

    logging.info(
        "VF criada: %s",
        output_file,
    )

def get_arguments():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--input-file",
        required=False,
    )

    return parser.parse_args()

def run_pipeline(
    input_file: Path | None = None,
) -> PipelineResult:

    file_path = (
        input_file
        if input_file
        else get_input_file()
    )

    df = load_data(
        file_path
    )

    logging.info(
        "Registros carregados: %s",
        len(df),
    )

    treated_df, dirty_df = process_dataframe(
        df
    )

    treated_df = drop_unused_columns(
        treated_df
    )

    dirty_df = drop_unused_columns(
        dirty_df
    )

    save_workbook(
        treated_df=treated_df,
        dirty_df=dirty_df,
    )

    save_vf(
        treated_df=treated_df,
        dirty_df=dirty_df,
    )

    return PipelineResult(
        total_rows=len(df),
        valid_rows=len(treated_df),
        dirty_rows=len(dirty_df),
        success=True,
    )


def main() -> None:

    args = get_arguments()

    input_file = (
        Path(args.input_file)
        if args.input_file
        else None
    )

    result = run_pipeline(
        input_file=input_file
    )

    logging.info(
        "Pipeline concluída | "
        "Total=%s | "
        "Validos=%s | "
        "Sujeira=%s",
        result.total_rows,
        result.valid_rows,
        result.dirty_rows,
    )


if __name__ == "__main__":
    main()