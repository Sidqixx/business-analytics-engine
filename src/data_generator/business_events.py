from __future__ import annotations

from datetime import date
from typing import Any


NORMAL_CONFIG = {
    "event_name": "normal",
    "demand_multiplier": 1.00,
    "product_demand_adjustments": {},
    "discount_probability": 0.10,
    "discount_rate": 0.05,
    "line_count_probs": [0.65, 0.25, 0.08, 0.02],
    "quantity_probs": [0.60, 0.25, 0.10, 0.05],
    "cost_adjustments": {},
}


def get_business_event(event_date: date) -> dict[str, Any]:
    """
    Return business behavior configuration for a given date.

    Final six-month scenario timeline:
    - Normal
    - Promotion
    - Product Decline
    - Cost Pressure
    - Sales Drop
    - Recovery
    """

    # ========================================================
    # PROMOTION
    # 2026-02-09 → 2026-02-15
    # ========================================================

    if date(2026, 2, 9) <= event_date <= date(2026, 2, 15):

        return {
            **NORMAL_CONFIG,
            "event_name": "promotion",
            "demand_multiplier": 1.25,
            "discount_probability": 0.70,
            "discount_rate": 0.10,

            # Slightly larger baskets during promotion.
            "line_count_probs": [0.55, 0.28, 0.12, 0.05],
            "quantity_probs": [0.45, 0.30, 0.15, 0.10],
        }

    # ========================================================
    # PRODUCT DECLINE
    # 2026-04-13 → 2026-04-19
    # ========================================================

    if date(2026, 4, 13) <= event_date <= date(2026, 4, 19):

        return {
            **NORMAL_CONFIG,
            "event_name": "product_decline",
            "product_demand_adjustments": {
                "Ayam Geprek": 0.65,
            },
        }

    # ========================================================
    # COST PRESSURE
    # 2026-05-11 → 2026-05-17
    # ========================================================

    if date(2026, 5, 11) <= event_date <= date(2026, 5, 17):

        return {
            **NORMAL_CONFIG,
            "event_name": "cost_pressure",
            "cost_adjustments": {
                "Nasi Goreng": 1.15,
                "Mie Goreng": 1.15,
                "Ayam Geprek": 1.15,
                "Ayam Bakar": 1.15,
                "Nasi Ayam": 1.15,
                "Mie Ayam": 1.15,
            },
        }

    # ========================================================
    # SALES DROP
    # 2026-06-08 → 2026-06-14
    # ========================================================

    if date(2026, 6, 8) <= event_date <= date(2026, 6, 14):

        return {
            **NORMAL_CONFIG,
            "event_name": "sales_drop",
            "demand_multiplier": 0.75,
        }

    # ========================================================
    # RECOVERY
    # 2026-06-15 → 2026-06-21
    # ========================================================

    if date(2026, 6, 15) <= event_date <= date(2026, 6, 21):

        return {
            **NORMAL_CONFIG,
            "event_name": "recovery",
            "demand_multiplier": 1.00,
        }

    # ========================================================
    # NORMAL
    # ========================================================

    return NORMAL_CONFIG.copy()