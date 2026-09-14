from __future__ import annotations

import numpy as np
import pandas as pd


# Normal discount behavior:
# 90% of product lines receive no discount.
# 10% receive a small discount.
DISCOUNT_PROBABILITY = 0.10

# Small normal discount rate.
NORMAL_DISCOUNT_RATE = 0.05

# Natural variation in unit cost.
# 3% standard deviation around the base cost.
COST_NOISE_STD = 0.03


def apply_financial_model(
    df: pd.DataFrame,
    rng: np.random.Generator,
    discount_probability: float = DISCOUNT_PROBABILITY,
    discount_rate: float = NORMAL_DISCOUNT_RATE,
    cost_adjustments: dict[str, float] | None = None,
) -> pd.DataFrame:
    """
    Apply normal financial logic to transactional data.

    Required columns:
        quantity
        unit_price
        base_cost

    Returns:
        DataFrame with:
        - discount
        - revenue
        - cost
        - profit
    """

    required_columns = {
        "quantity",
        "unit_price",
        "base_cost",
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(f"Missing required columns: {sorted(missing_columns)}")

    result = df.copy()

    if cost_adjustments is None:
        cost_adjustments = {}

    # ---------------------------------------------------------
    # 1. Discount
    # ---------------------------------------------------------
    receives_discount = rng.random(len(result)) < discount_probability

    result["discount"] = np.where(
        receives_discount,
        result["quantity"] * result["unit_price"] * discount_rate,
        0.0,
    )

    # ---------------------------------------------------------
    # 2. Revenue
    # ---------------------------------------------------------
    gross_sales = result["quantity"] * result["unit_price"]

    result["revenue"] = gross_sales - result["discount"]

    # ---------------------------------------------------------
    # 3. Actual cost
    # ---------------------------------------------------------
    cost_noise = rng.normal(
        loc=1.0,
        scale=COST_NOISE_STD,
        size=len(result),
    )

    cost_noise = np.maximum(cost_noise, 0.1)

    # Start from the normal base cost.
    result["cost"] = (
        result["quantity"]
        * result["base_cost"]
        * cost_noise
    )

    # Apply event-specific cost adjustments.
    if cost_adjustments:
        for product_name, multiplier in cost_adjustments.items():
            mask = result["product"] == product_name
            result.loc[mask, "cost"] *= multiplier

    # ---------------------------------------------------------
    # 4. Profit
    # ---------------------------------------------------------
    result["profit"] = result["revenue"] - result["cost"]

    # Round financial values for cleaner business data.
    result["discount"] = result["discount"].round(2)
    result["revenue"] = result["revenue"].round(2)
    result["cost"] = result["cost"].round(2)
    result["profit"] = result["profit"].round(2)

    return result


def validate_financial_model(df: pd.DataFrame) -> None:
    """
    Validate mathematical consistency of the financial model.
    """

    required_columns = {
        "quantity",
        "unit_price",
        "base_cost",
        "discount",
        "revenue",
        "cost",
        "profit",
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required financial columns: {sorted(missing_columns)}"
        )

    expected_revenue = df["quantity"] * df["unit_price"] - df["discount"]

    expected_profit = df["revenue"] - df["cost"]

    revenue_is_valid = np.allclose(
        df["revenue"],
        expected_revenue,
        atol=0.01,
    )

    profit_is_valid = np.allclose(
        df["profit"],
        expected_profit,
        atol=0.01,
    )

    if not revenue_is_valid:
        raise ValueError("Revenue validation failed.")

    if not profit_is_valid:
        raise ValueError("Profit validation failed.")

    if (df["discount"] < 0).any():
        raise ValueError("Discount cannot be negative.")

    if (df["cost"] < 0).any():
        raise ValueError("Cost cannot be negative.")


if __name__ == "__main__":
    from datetime import date

    from transaction_generator import (
        generate_transactions_for_day,
    )

    rng = np.random.default_rng(42)

    # Generate one test day.
    df_test = generate_transactions_for_day(
        transaction_date=date(2026, 1, 5),
        transaction_count=138,
        rng=rng,
    )

    # Apply financial model.
    df_test = apply_financial_model(
        df_test,
        rng,
    )

    # Validate.
    validate_financial_model(df_test)

    print("Financial model validation: PASS ✅")

    print("\nFirst 10 rows:")
    print(
        df_test[
            [
                "transaction_id",
                "product",
                "quantity",
                "unit_price",
                "discount",
                "revenue",
                "cost",
                "profit",
            ]
        ]
        .head(10)
        .to_string(index=False)
    )

    print("\nFinancial summary:")
    print(
        df_test[
            [
                "revenue",
                "cost",
                "profit",
            ]
        ].sum()
    )
