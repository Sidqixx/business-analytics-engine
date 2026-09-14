from pathlib import Path
import pandas as pd


# ============================================================
# LOAD DATASET
# ============================================================

DATA_FILE = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "generated"
    / "demo_full.csv"
)

df = pd.read_csv(DATA_FILE)

df["date"] = pd.to_datetime(df["date"])


# ============================================================
# HELPER
# ============================================================

def summarize_period(df, name):
    transactions = df["transaction_id"].nunique()
    quantity = df["quantity"].sum()
    revenue = df["revenue"].sum()
    cost = df["cost"].sum()
    profit = df["profit"].sum()

    aov = revenue / transactions if transactions > 0 else 0
    margin = profit / revenue if revenue > 0 else 0

    print(f"\n{name}")
    print("-" * 60)
    print(f"Transactions : {transactions:,}")
    print(f"Quantity     : {quantity:,}")
    print(f"Revenue      : Rp {revenue:,.2f}")
    print(f"AOV          : Rp {aov:,.2f}")
    print(f"Profit       : Rp {profit:,.2f}")
    print(f"Margin       : {margin:.2%}")


def compare_periods(df_before, df_event, name):
    print("\n" + "=" * 70)
    print(name)
    print("=" * 70)

    summarize_period(df_before, "BEFORE")
    summarize_period(df_event, "EVENT")

    before_tx = df_before["transaction_id"].nunique()
    event_tx = df_event["transaction_id"].nunique()

    before_qty = df_before["quantity"].sum()
    event_qty = df_event["quantity"].sum()

    before_revenue = df_before["revenue"].sum()
    event_revenue = df_event["revenue"].sum()

    before_profit = df_before["profit"].sum()
    event_profit = df_event["profit"].sum()

    before_aov = before_revenue / before_tx
    event_aov = event_revenue / event_tx

    before_margin = before_profit / before_revenue
    event_margin = event_profit / event_revenue

    print("\nCHANGE")
    print("-" * 60)

    print(
        f"Transactions : "
        f"{(event_tx / before_tx - 1):+.2%}"
    )

    print(
        f"Quantity     : "
        f"{(event_qty / before_qty - 1):+.2%}"
    )

    print(
        f"Revenue      : "
        f"{(event_revenue / before_revenue - 1):+.2%}"
    )

    print(
        f"AOV          : "
        f"{(event_aov / before_aov - 1):+.2%}"
    )

    print(
        f"Profit       : "
        f"{(event_profit / before_profit - 1):+.2%}"
    )

    print(
        f"Margin       : "
        f"{(event_margin - before_margin):+.2%}"
        f" points"
    )


# ============================================================
# 1. PROMOTION
# ============================================================

before = df[
    (df["date"] >= "2026-02-01") &
    (df["date"] <= "2026-02-08")
]

event = df[
    (df["date"] >= "2026-02-09") &
    (df["date"] <= "2026-02-15")
]

compare_periods(
    before,
    event,
    "PROMOTION — Feb 9–15"
)


# ============================================================
# 2. PRODUCT DECLINE
# ============================================================

before = df[
    (df["date"] >= "2026-04-06") &
    (df["date"] <= "2026-04-12")
]

event = df[
    (df["date"] >= "2026-04-13") &
    (df["date"] <= "2026-04-19")
]

compare_periods(
    before,
    event,
    "PRODUCT DECLINE — Apr 13–19"
)

print("\n" + "=" * 70)
print("PRODUCT DECLINE — AYAM GEPREK CHECK")
print("=" * 70)

before_product = before[before["product"] == "Ayam Geprek"]
event_product = event[event["product"] == "Ayam Geprek"]

before_qty = before_product["quantity"].sum()
event_qty = event_product["quantity"].sum()

before_revenue = before_product["revenue"].sum()
event_revenue = event_product["revenue"].sum()

print(f"Before quantity : {before_qty:,}")
print(f"Event quantity  : {event_qty:,}")
print(
    f"Quantity change : "
    f"{(event_qty / before_qty - 1):+.2%}"
)

print(f"\nBefore revenue  : Rp {before_revenue:,.2f}")
print(f"Event revenue   : Rp {event_revenue:,.2f}")
print(
    f"Revenue change  : "
    f"{(event_revenue / before_revenue - 1):+.2%}"
)


# ============================================================
# 3. COST PRESSURE
# ============================================================

before = df[
    (df["date"] >= "2026-05-04") &
    (df["date"] <= "2026-05-10")
]

event = df[
    (df["date"] >= "2026-05-11") &
    (df["date"] <= "2026-05-17")
]

compare_periods(
    before,
    event,
    "COST PRESSURE — May 11–17"
)


# ============================================================
# 4. SALES DROP
# ============================================================

before = df[
    (df["date"] >= "2026-06-01") &
    (df["date"] <= "2026-06-07")
]

event = df[
    (df["date"] >= "2026-06-08") &
    (df["date"] <= "2026-06-14")
]

compare_periods(
    before,
    event,
    "SALES DROP — Jun 8–14"
)


# ============================================================
# 5. RECOVERY
# ============================================================

before = df[
    (df["date"] >= "2026-06-08") &
    (df["date"] <= "2026-06-14")
]

event = df[
    (df["date"] >= "2026-06-15") &
    (df["date"] <= "2026-06-21")
]

compare_periods(
    before,
    event,
    "RECOVERY — Jun 15–21"
)