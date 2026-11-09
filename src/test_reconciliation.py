from __future__ import annotations

from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent

VF_FILE = (
    BASE_DIR
    / "data"
    / "final_concreto"
    / "Antifraude - Jul26 - VF.xlsx"
)


def load_sheets() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    workbook = pd.read_excel(
        VF_FILE,
        sheet_name=None,
        engine="openpyxl",
    )

    base_df = workbook["Base completa - Jul26"]

    ajustes_df = workbook["Ajustes Jul26"]

    sujeira_df = workbook["Sujeira  - avaliar"]

    return base_df, ajustes_df, sujeira_df


def build_key(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()

    result["_key"] = (
        result["Invoice Number"].astype(str)
        + "|"
        + result["Child"].astype(str)
        + "|"
        + result["Product Description"].astype(str)
    )

    return result


def analyze_counts(
    base_df: pd.DataFrame,
    ajustes_df: pd.DataFrame,
    sujeira_df: pd.DataFrame,
) -> None:
    print("\n" + "=" * 100)
    print("CONTAGENS")
    print("=" * 100)

    print(f"Base Completa : {len(base_df):,}")
    print(f"Ajustes       : {len(ajustes_df):,}")
    print(f"Sujeira       : {len(sujeira_df):,}")

    print(
        f"\nDiferença Ajustes -> Base: "
        f"{len(ajustes_df) - len(base_df):,}"
    )


def analyze_nulls(
    ajustes_df: pd.DataFrame,
) -> None:
    print("\n" + "=" * 100)
    print("NULLS")
    print("=" * 100)

    if "MID" in ajustes_df.columns:
        print(
            f"MID nulo: "
            f"{ajustes_df['MID'].isna().sum():,}"
        )

    if "Child" in ajustes_df.columns:
        print(
            f"Child nulo: "
            f"{ajustes_df['Child'].isna().sum():,}"
        )


def analyze_removed_rows(
    base_df: pd.DataFrame,
    ajustes_df: pd.DataFrame,
) -> None:
    print("\n" + "=" * 100)
    print("REGISTROS REMOVIDOS")
    print("=" * 100)

    base_df = build_key(base_df)
    ajustes_df = build_key(ajustes_df)

    removed_df = ajustes_df[
        ~ajustes_df["_key"].isin(base_df["_key"])
    ].copy()

    print(
        f"Registros removidos: "
        f"{len(removed_df):,}"
    )

    if removed_df.empty:
        return

    print("\nTOP 20 REMOVIDOS\n")

    cols = [
        col
        for col in [
            "Child",
            "MID",
            "Product Description",
            "Total Amount Due",
            "Análise - Etapa 1",
            "Análise - Etapa 2",
            "Ajustes mês anterior",
            "Ajustes mês atual",
        ]
        if col in removed_df.columns
    ]

    print(
        removed_df[cols]
        .head(20)
        .to_string(index=False)
    )

    if "Product Description" in removed_df.columns:
        print("\nTOP PRODUTOS REMOVIDOS\n")

        print(
            removed_df["Product Description"]
            .value_counts()
            .head(30)
            .to_string()
        )

    if "Child" in removed_df.columns:
        print("\nTOP CHILDS REMOVIDOS\n")

        print(
            removed_df["Child"]
            .value_counts()
            .head(30)
            .to_string()
        )


def analyze_sujeira(
    sujeira_df: pd.DataFrame,
) -> None:
    print("\n" + "=" * 100)
    print("SUJEIRA")
    print("=" * 100)

    print(
        f"Linhas sujeira: "
        f"{len(sujeira_df):,}"
    )

    print("\nPrimeiras 20 linhas:\n")

    print(
        sujeira_df.head(20).to_string(index=False)
    )


def main() -> None:
    base_df, ajustes_df, sujeira_df = load_sheets()

    analyze_counts(
        base_df,
        ajustes_df,
        sujeira_df,
    )

    analyze_nulls(
        ajustes_df,
    )

    analyze_removed_rows(
        base_df,
        ajustes_df,
    )

    analyze_sujeira(
        sujeira_df,
    )


if __name__ == "__main__":
    main()