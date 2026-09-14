from __future__ import annotations

from datetime import date

import numpy as np


# Baseline number of transactions on a normal day.
BASE_DAILY_TRANSACTIONS = 150


# Relative demand by day of week.
# Monday = 0 ... Sunday = 6
DAY_OF_WEEK_FACTORS = {
    0: 0.90,  # Monday
    1: 0.95,  # Tuesday
    2: 1.00,  # Wednesday
    3: 1.00,  # Thursday
    4: 1.10,  # Friday
    5: 1.20,  # Saturday
    6: 1.15,  # Sunday
}


# Natural day-to-day variation.
# 0.08 means roughly +/- 8% around the expected volume.
DAILY_NOISE_STD = 0.08


def calculate_expected_transactions(
    transaction_date: date,
    rng: np.random.Generator,
    demand_multiplier: float = 1.0,
) -> int:
    """
    Generate the expected number of transactions for a single day.

    Parameters
    ----------
    transaction_date : date
        Date being generated.

    rng : np.random.Generator
        Random number generator for reproducible simulation.

    Returns
    -------
    int
        Simulated transaction count for the day.
    """

    day_factor = DAY_OF_WEEK_FACTORS[transaction_date.weekday()]

    # Random variation around the normal daily demand.
    noise_factor = rng.normal(loc=1.0, scale=DAILY_NOISE_STD)

    expected_transactions = (
    BASE_DAILY_TRANSACTIONS
    * day_factor
    * noise_factor
    * demand_multiplier
    )   

    # Prevent unrealistic negative/zero transaction volume.
    expected_transactions = max(1, round(expected_transactions))

    return expected_transactions


if __name__ == "__main__":
    rng = np.random.default_rng(42)

    test_dates = [
        date(2026, 1, 5),  # Monday
        date(2026, 1, 9),  # Friday
        date(2026, 1, 10), # Saturday
        date(2026, 1, 11), # Sunday
    ]

    for test_date in test_dates:
        transactions = calculate_expected_transactions(
            test_date,
            rng,
        )

        print(
            f"{test_date} | "
            f"{test_date.strftime('%A'):>9} | "
            f"{transactions} transactions"
        )