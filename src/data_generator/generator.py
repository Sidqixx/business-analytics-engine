from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from demand_model import calculate_expected_transactions
from financial_model import apply_financial_model, validate_financial_model
from transaction_generator import generate_transactions_for_day
from business_events import get_business_event


# ============================================================
# CONFIG
# ============================================================

START_DATE = date(2026, 1, 1)
END_DATE = date(2026, 6, 30)

RANDOM_SEED = 42

OUTPUT_DIR = Path(__file__).resolve().parents[2] / "data" / "generated"
OUTPUT_FILE = OUTPUT_DIR / "demo_full.csv"



# ============================================================
# GENERATOR
# ============================================================

def generate_date_range(
    start_date: date,
    end_date: date,
):
    """
    Yield every date between start_date and end_date, inclusive.
    """

    if end_date < start_date:
        raise ValueError("end_date cannot be earlier than start_date.")

    current_date = start_date

    while current_date <= end_date:
        yield current_date
        current_date += timedelta(days=1)


def generate_prototype_dataset(
    start_date: date,
    end_date: date,
    seed: int = RANDOM_SEED,
) -> pd.DataFrame:
    """
    Generate a complete synthetic transactional dataset
    for the requested date range,
    including configured business events.
    """

    rng = np.random.default_rng(seed)

    daily_frames = []

    next_transaction_id = 1

    for current_date in generate_date_range(start_date, end_date):

        event = get_business_event(current_date)

        transaction_count = calculate_expected_transactions(
            transaction_date=current_date,
            rng=rng,
            demand_multiplier=event["demand_multiplier"],
        )

        df_day = generate_transactions_for_day(
            transaction_date=current_date,
            transaction_count=transaction_count,
            rng=rng,
            transaction_id_start=next_transaction_id,
            line_count_probs=np.array(event["line_count_probs"]),
            quantity_probs=np.array(event["quantity_probs"]),
            product_demand_adjustments=event[
                "product_demand_adjustments"
            ],
        )

        next_transaction_id += transaction_count

        df_day = apply_financial_model(
            df=df_day,
            rng=rng,
            discount_probability=event["discount_probability"],
            discount_rate=event["discount_rate"],
            cost_adjustments=event["cost_adjustments"],
        )

        daily_frames.append(df_day)


    if not daily_frames:
        raise ValueError("No transactional data was generated.")


    df = pd.concat(
        daily_frames,
        ignore_index=True,
    )

    validate_financial_model(df)

    return df


# ============================================================
# SUMMARY
# ============================================================

def print_dataset_summary(df: pd.DataFrame) -> None:
    """
    Print a concise summary of the generated prototype.
    """

    print("\n" + "=" * 70)
    print("KEDAI RASA KITA — SYNTHETIC DATASET")
    print("=" * 70)

    print(f"Date range         : {df['date'].min()} → {df['date'].max()}")
    print(f"Total rows         : {len(df):,}")
    print(
        f"Unique transactions: "
        f"{df['transaction_id'].nunique():,}"
    )

    daily_transactions = (
        df.groupby("date")["transaction_id"]
        .nunique()
    )

    print(
        f"Avg transactions/day: "
        f"{daily_transactions.mean():.2f}"
    )

    print(
        f"Min transactions/day: "
        f"{daily_transactions.min():,}"
    )

    print(
        f"Max transactions/day: "
        f"{daily_transactions.max():,}"
    )

    print("\nRevenue:")
    print(f"  Total : Rp {df['revenue'].sum():,.2f}")
    print(f"  Mean  : Rp {df['revenue'].mean():,.2f}")

    print("\nCost:")
    print(f"  Total : Rp {df['cost'].sum():,.2f}")

    print("\nProfit:")
    print(f"  Total : Rp {df['profit'].sum():,.2f}")

    total_revenue = df["revenue"].sum()
    total_profit = df["profit"].sum()

    if total_revenue > 0:
        margin = total_profit / total_revenue
        print(f"  Margin: {margin:.2%}")

    print("\nDiscount:")
    discounted_rows = (df["discount"] > 0).sum()
    discount_rate = discounted_rows / len(df)

    print(f"  Discounted rows: {discounted_rows:,}")
    print(f"  Discount rate  : {discount_rate:.2%}")

    print("\nTop products:")
    print(
        df["product"]
        .value_counts()
        .head(10)
        .to_string()
    )

    print("=" * 70)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("Generating Kedai Rasa Kita synthetic dataset...")

    df_prototype = generate_prototype_dataset(
        start_date=START_DATE,
        end_date=END_DATE,
        seed=RANDOM_SEED,
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    df_prototype.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print_dataset_summary(df_prototype)

    print(
        f"\nSaved to:\n{OUTPUT_FILE}"
    )

    print("\nFinancial validation: PASS ✅")