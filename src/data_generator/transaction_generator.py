from __future__ import annotations

from datetime import date
from typing import List

import numpy as np
import pandas as pd

from product_catalog import get_product_catalog


# Probability distribution for the number of product lines
# inside a single transaction.
LINE_COUNT_VALUES = np.array([1, 2, 3, 4])
LINE_COUNT_PROBS = np.array([0.65, 0.25, 0.08, 0.02])


# Probability distribution for quantity purchased
# for each product line.
QUANTITY_VALUES = np.array([1, 2, 3, 4])
QUANTITY_PROBS = np.array([0.60, 0.25, 0.10, 0.05])


def generate_transactions_for_day(
    transaction_date: date,
    transaction_count: int,
    rng: np.random.Generator,
    transaction_id_start: int = 1,
    line_count_probs: np.ndarray | None = None,
    quantity_probs: np.ndarray | None = None,
    product_demand_adjustments: dict[str, float] | None = None,
) -> pd.DataFrame:
    """
    Generate flat transactional records for one day.

    Parameters
    ----------
    transaction_date : date
        Date of transactions.

    transaction_count : int
        Number of transactions to generate.

    rng : np.random.Generator
        Random number generator for reproducible results.

    transaction_id_start : int
        Starting numeric ID for the first transaction.

    Returns
    -------
    pd.DataFrame
        Flat transactional dataset for the given day.
    """

    if transaction_count <= 0:
        raise ValueError("transaction_count must be greater than 0.")

    catalog = get_product_catalog()

    if line_count_probs is None:
        line_count_probs = LINE_COUNT_PROBS

    if quantity_probs is None:
        quantity_probs = QUANTITY_PROBS

    if product_demand_adjustments is None:
        product_demand_adjustments = {}

    products = catalog["product"].to_numpy()
    product_weights = catalog["demand_weight"].astype(float).to_numpy()

    # Apply temporary event-specific adjustments.
    for product_name, multiplier in product_demand_adjustments.items():

        if product_name not in products:
            raise ValueError(
                f"Product adjustment references unknown product: "
                f"{product_name}"
          )

        product_index = np.where(
            products == product_name
        )[0][0]

        product_weights[product_index] *= multiplier

    product_probabilities = (
        product_weights
        / product_weights.sum()
    )

    rows: List[dict] = []

    transaction_number = transaction_id_start

    for _ in range(transaction_count):

        transaction_id = f"TRX{transaction_number:06d}"
        transaction_number += 1

        # Determine how many different product lines
        # are included in this transaction.
        line_count = rng.choice(
        LINE_COUNT_VALUES,
        p=line_count_probs,
    )

        # Select distinct products for each transaction.
        selected_products = rng.choice(
            products,
            size=line_count,
            replace=False,
            p=product_probabilities,
        )

        for product_name in selected_products:

            quantity = rng.choice(
                QUANTITY_VALUES,
                p=quantity_probs,
            )

            product_info = catalog.loc[
                catalog["product"] == product_name
            ].iloc[0]

            rows.append(
                {
                    "date": transaction_date,
                    "transaction_id": transaction_id,
                    "product": product_info["product"],
                    "category": product_info["category"],
                    "quantity": int(quantity),
                    "unit_price": int(product_info["base_price"]),
                    "base_cost": float(product_info["base_cost"]),
                }
            )

    return pd.DataFrame(rows)


if __name__ == "__main__":
    rng = np.random.default_rng(42)

    df_test = generate_transactions_for_day(
        transaction_date=date(2026, 1, 5),
        transaction_count=138,
        rng=rng,
    )

    print("Generated rows:", len(df_test))
    print("Unique transactions:", df_test["transaction_id"].nunique())

    print("\nFirst 10 rows:")
    print(df_test.head(10).to_string(index=False))

    print("\nProduct distribution:")
    print(
        df_test["product"]
        .value_counts()
        .to_string()
    )

    print("\nLine items per transaction:")
    print(
        df_test.groupby("transaction_id")
        .size()
        .value_counts()
        .sort_index()
        .to_string()
    )