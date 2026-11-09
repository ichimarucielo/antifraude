from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import pandas as pd

import main


class ReconciliationTest(unittest.TestCase):
    def test_pipeline_preserves_rows_and_totals(self):
        df = pd.DataFrame({
            "Invoice Number": ["INV"] * 5,
            "Child": ["Loja1", "Loja2", "Outra", "Loja", "123"],
            "MID": ["mid-a", "mid-b", "mid-c", "mid-d", "mid-e"],
            "Product Description": [None] * 5,
            "Total Amount Due": [10, 20, -2, None, 5],
            "Payment Volume": [0] * 5,
        })
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "input.xlsx"
            df.to_excel(source, engine="openpyxl", index=False)
            with patch.multiple(main, WORK_FOLDER=root / "work", OUTPUT_FOLDER=root / "final"):
                result = main.run_pipeline(source)
            work = pd.read_excel(root / "work/antifraude_trabalho.xlsx", sheet_name=None)
            final = pd.read_excel(root / "final/antifraude_vf.xlsx", sheet_name=None)

        self.assertEqual(result, main.PipelineResult(5, 2, 3, True))
        base, candidates, dirty = (final[name] for name in (
            "BASE_COMPLETA", "CHECK_DUPLICIDADE", "SUJEIRA"
        ))
        pd.testing.assert_frame_equal(base, work["TRATADO"])
        pd.testing.assert_frame_equal(dirty, work["SUJEIRA"])
        self.assertEqual(base["MID"].tolist(), ["braspag_loja"] * 2)
        self.assertEqual(base["mid_original"].tolist(), ["mid-a", "mid-b"])
        self.assertEqual(candidates["ocorrencias_chave"].tolist(), [2, 2])
        self.assertEqual(dirty["motivo_sujeira"].tolist(), [
            "amount_invalido", "amount_invalido", "child_invalido"
        ])
        self.assertNotIn("Payment Volume", base.columns)
        self.assertEqual(
            base["Total Amount Due"].sum() + dirty["Total Amount Due"].sum(),
            df["Total Amount Due"].sum(),
        )

    def test_empty_input_retains_headers(self):
        treated, dirty = main.process_dataframe(pd.DataFrame(columns=sorted(main.REQUIRED_COLUMNS)))
        self.assertIn("child_original", treated.columns)
        self.assertIn("motivo_sujeira", dirty.columns)
        self.assertIn("ocorrencias_chave", main.find_duplicate_candidates(treated).columns)

    def test_schema_validation(self):
        with self.assertRaisesRegex(ValueError, "Colunas obrigatórias ausentes"):
            main.process_dataframe(pd.DataFrame({"Child": ["loja"]}))
