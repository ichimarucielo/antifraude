from __future__ import annotations

import math
import re

import pandas as pd


ALLOWED_NUMERIC_SUFFIXES = {"braspag_banese1", "braspag_3ds20"}


def normalize_text(value: object) -> str:
    return "" if pd.isna(value) else str(value).strip().lower()


def is_invalid_amount(amount: object) -> bool:
    try:
        value = float(amount)
    except (TypeError, ValueError, OverflowError):
        return True
    return not math.isfinite(value) or value <= 0


def classify_dirty(child: object, mid: object, total_amount_due: object) -> tuple[bool, str]:
    if is_invalid_amount(total_amount_due):
        return True, "amount_invalido"

    child = normalize_text(child)
    if not child:
        return True, "child_ausente"

    if "stelo" in child and "stelo" in normalize_text(mid):
        return True, "stelo_teste"

    return False, ""


def build_child_final(child: object, product_description: object) -> str:
    value = normalize_text(child)

    if "alelo" in value:
        product = normalize_text(product_description)
        return "braspag_alelo" if "visa" in product else "braspag_alelo_enterprise"

    if "amway" in value:
        return "braspag_amway"

    if not value.startswith("braspag_"):
        value = f"braspag_{value}"

    if value in ALLOWED_NUMERIC_SUFFIXES:
        return value

    return re.sub(r"\d+$", "", value).rstrip("_")
