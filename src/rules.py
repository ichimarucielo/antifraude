from __future__ import annotations

import re


ALLOWED_NUMERIC_SUFFIXES = {
    "banese1",
    "3ds20",
}


DIRTY_REASON_AMOUNT = "amount_invalido"
DIRTY_REASON_STELO = "stelo_teste"


def normalize_text(value: str | None) -> str:
    if value is None:
        return ""

    return str(value).strip().lower()


def is_invalid_amount(amount: float) -> bool:
    try:
        return float(amount) <= 0
    except Exception:
        return True


def is_stelo_test(
    child: str,
    mid: str,
) -> bool:
    child = normalize_text(child)
    mid = normalize_text(mid)

    return (
        "stelo" in child
        and "stelo" in mid
    )


def apply_alelo_rule(
    child: str,
    product_description: str,
) -> str:
    child = normalize_text(child)

    if "alelo" not in child:
        return child

    product = normalize_text(product_description)

    if (
        "visa" in product
        or "nonvisa" in product
        or "non-visa" in product
    ):
        return "braspag_alelo"

    return "braspag_alelo_enterprise"


def apply_amway_rule(
    child: str,
) -> str:
    child = normalize_text(child)

    if "amway" in child:
        return "braspag_amway"

    return child


def remove_trailing_numbers(
    value: str,
) -> str:
    value = normalize_text(value)

    if value in ALLOWED_NUMERIC_SUFFIXES:
        return value

    return re.sub(
        r"\d+$",
        "",
        value,
    ).rstrip("_")


def ensure_braspag_prefix(
    value: str,
) -> str:
    value = normalize_text(value)

    if value.startswith("braspag_"):
        return value

    return f"braspag_{value}"


def build_child_final(
    child: str,
    product_description: str,
) -> str:
    child = apply_alelo_rule(
        child=child,
        product_description=product_description,
    )

    child = apply_amway_rule(
        child
    )

    child = ensure_braspag_prefix(
        child
    )

    child = remove_trailing_numbers(
        child
    )

    return normalize_text(
        child
    )


def classify_dirty(
    child: str,
    mid: str,
    total_amount_due: float,
) -> tuple[bool, str]:
    if is_invalid_amount(
        total_amount_due
    ):
        return (
            True,
            DIRTY_REASON_AMOUNT,
        )

    if is_stelo_test(
        child,
        mid,
    ):
        return (
            True,
            DIRTY_REASON_STELO,
        )

    return False, ""