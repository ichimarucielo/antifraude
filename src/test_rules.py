import unittest

from rules import build_child_final, classify_dirty


class RulesTest(unittest.TestCase):
    def test_normalization(self):
        for child, product, expected in [
            ("  BANESE1 ", "", "braspag_banese1"),
            ("braspag_3ds20", "", "braspag_3ds20"),
            (" Loja_123 ", "", "braspag_loja"),
            ("loja alelo", "Non-Visa", "braspag_alelo"),
            ("loja alelo", "Enterprise", "braspag_alelo_enterprise"),
            ("loja amway", "", "braspag_amway"),
        ]:
            with self.subTest(child=child, product=product):
                self.assertEqual(build_child_final(child, product), expected)
                self.assertEqual(build_child_final(expected, product), expected)

    def test_invalid_amounts(self):
        for amount in (None, "", "erro", 0, -1, float("nan"), float("inf"), float("-inf")):
            with self.subTest(amount=amount):
                self.assertEqual(classify_dirty("loja", "", amount), (True, "amount_invalido"))

    def test_missing_child_and_stelo(self):
        self.assertEqual(classify_dirty(float("nan"), "loja", 1), (True, "child_ausente"))
        self.assertEqual(classify_dirty("Stelo", "stelo_teste", 1), (True, "stelo_teste"))
        self.assertEqual(classify_dirty("loja", None, 1), (False, ""))
