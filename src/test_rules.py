from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent

VF_FILE = (
    BASE_DIR
    / "data"
    / "final_concreto"
    / "Antifraude - Jul26 - VF.xlsx"
)


def main() -> None:
    workbook = pd.read_excel(
        VF_FILE,
        sheet_name=None,
        engine="openpyxl",
    )

    print("\nABAS:")
    for sheet_name, df in workbook.items():
        print(
            f"{sheet_name} | "
            f"linhas={len(df)} | "
            f"colunas={len(df.columns)}"
        )

    print("\n" + "=" * 100)

    for sheet_name, df in workbook.items():
        print(f"\nABA: {sheet_name}")
        print(df.head(5).to_string())


if __name__ == "__main__":
    main()