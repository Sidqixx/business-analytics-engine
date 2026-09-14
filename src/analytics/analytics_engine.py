from pathlib import Path
import json
import pandas as pd


# ============================================================
# CONFIG
# ============================================================

DATA_FILE = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "generated"
    / "demo_full.csv"
)

ANALYSIS_OUTPUT_FILE = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "generated"
    / "analysis_result.json"
)


# ============================================================
# LOAD DATA
# ============================================================

def load_data(path):
    """
    Load raw transactional data.

    Schema validation and column mapping are handled
    separately by schema_mapping.py.
    """

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"Data file not found: {path}"
        )

    df = pd.read_csv(path)

    if df.empty:
        raise ValueError(
            "Input data is empty."
        )

    return df


# ============================================================
# SALES MONITORING
# ============================================================

def calculate_sales_metrics(
    df: pd.DataFrame,
) -> dict:
    """
    Calculate sales metrics based on available fields.

    Metrics are only calculated when their required
    input fields are available.
    """

    metrics = {}

    number_of_days = (
        df["date"].nunique()
        if "date" in df.columns
        else 0
    )

    # --------------------------------------------------------
    # Revenue
    # --------------------------------------------------------

    if "revenue" in df.columns:

        total_revenue = df["revenue"].sum()

        metrics["total_revenue"] = total_revenue

        metrics["revenue_per_day"] = (
            total_revenue / number_of_days
            if number_of_days > 0
            else 0
        )

    # --------------------------------------------------------
    # Transactions
    # --------------------------------------------------------

    if "transaction_id" in df.columns:

        total_transactions = (
            df["transaction_id"].nunique()
        )

        metrics["total_transactions"] = (
            total_transactions
        )

        metrics["transactions_per_day"] = (
            total_transactions / number_of_days
            if number_of_days > 0
            else 0
        )

    # --------------------------------------------------------
    # Quantity
    # --------------------------------------------------------

    if "quantity" in df.columns:

        metrics["total_quantity"] = (
            df["quantity"].sum()
        )

    # --------------------------------------------------------
    # AOV
    # --------------------------------------------------------

    if (
        "revenue" in df.columns
        and "transaction_id" in df.columns
    ):

        total_revenue = metrics["total_revenue"]
        total_transactions = metrics["total_transactions"]

        metrics["aov"] = (
            total_revenue / total_transactions
            if total_transactions > 0
            else 0
        )

    return metrics

# ============================================================
# PERIOD COMPARISON
# ============================================================

def compare_periods(
    current_df: pd.DataFrame,
    previous_df: pd.DataFrame,
) -> dict:
    """
    Compare available sales metrics between two periods.
    """

    current = calculate_sales_metrics(
        current_df
    )

    previous = calculate_sales_metrics(
        previous_df
    )

    comparison = {}

    metrics = [
        "total_revenue",
        "total_transactions",
        "total_quantity",
        "aov",
    ]

    for metric in metrics:

        if (
            metric not in current
            or metric not in previous
        ):
            continue

        current_value = current[metric]
        previous_value = previous[metric]

        absolute_change = (
            current_value - previous_value
        )

        if previous_value != 0:
            percentage_change = (
                absolute_change / previous_value
            )
        else:
            percentage_change = 0

        signal = classify_change(
            percentage_change
        )

        comparison[metric] = {
            "current": current_value,
            "previous": previous_value,
            "absolute_change": absolute_change,
            "percentage_change": percentage_change,
            "signal": signal,
        }

    return comparison

# ============================================================
# REVENUE DRIVER DIAGNOSIS
# ============================================================

def diagnose_revenue_driver(
    comparison: dict,
) -> str:
    """
    Diagnose revenue movement using available sales metrics.

    If transaction volume and AOV are unavailable, the function
    reports the revenue movement without inferring its driver.
    """

    revenue_change = comparison[
        "total_revenue"
    ]["percentage_change"]

    transaction_result = comparison.get(
        "total_transactions"
    )

    aov_result = comparison.get(
        "aov"
    )

    # --------------------------------------------------------
    # No transaction / AOV data available
    # --------------------------------------------------------

    if (
        transaction_result is None
        or aov_result is None
    ):

        if revenue_change < 0:

            return (
                "Revenue decline detected, but "
                "transaction volume and AOV drivers "
                "are unavailable"
            )

        elif revenue_change > 0:

            return (
                "Revenue increase detected, but "
                "transaction volume and AOV drivers "
                "are unavailable"
            )

        else:

            return (
                "Revenue remained unchanged; "
                "transaction volume and AOV drivers "
                "are unavailable"
            )

    # --------------------------------------------------------
    # Full revenue diagnosis
    # --------------------------------------------------------

    transaction_change = (
        transaction_result["percentage_change"]
    )

    aov_change = (
        aov_result["percentage_change"]
    )

    material_threshold = 0.10

    transaction_increase = (
        transaction_change >= material_threshold
    )

    transaction_decrease = (
        transaction_change <= -material_threshold
    )

    aov_increase = (
        aov_change >= material_threshold
    )

    aov_decrease = (
        aov_change <= -material_threshold
    )

    if transaction_decrease and aov_decrease:

        return (
            "Both transaction volume and AOV declined"
        )

    elif transaction_increase and aov_increase:

        return (
            "Both transaction volume and AOV increased"
        )

    elif transaction_decrease:

        return "Transaction volume decline"

    elif transaction_increase:

        return "Transaction volume increase"

    elif aov_decrease:

        return "AOV decline"

    elif aov_increase:

        return "AOV increase"

    else:

        return (
            "No material change in transaction "
            "volume or AOV"
        )


# ============================================================
# PRODUCT PERFORMANCE DIAGNOSIS
# ============================================================

def diagnose_product_performance(
    current_df: pd.DataFrame,
    previous_df: pd.DataFrame,
    threshold: float = 0.10,
) -> list:
    """
    Identify products with material performance changes.

    A product is considered relevant when:
    - quantity or revenue changes materially, and
    - the revenue change has meaningful impact on the business.
    """

    current_product = (
        current_df.groupby("product")
        .agg(
            current_quantity=("quantity", "sum"),
            current_revenue=("revenue", "sum"),
        )
    )

    previous_product = (
        previous_df.groupby("product")
        .agg(
            previous_quantity=("quantity", "sum"),
            previous_revenue=("revenue", "sum"),
        )
    )

    product_comparison = (
        previous_product
        .join(current_product, how="outer")
        .fillna(0)
    )

    total_previous_revenue = previous_df["revenue"].sum()

    results = []

    for product, row in product_comparison.iterrows():

        previous_quantity = row["previous_quantity"]
        current_quantity = row["current_quantity"]

        previous_revenue = row["previous_revenue"]
        current_revenue = row["current_revenue"]

        # ----------------------------------------------------
        # Percentage changes
        # ----------------------------------------------------

        if previous_quantity > 0:
            quantity_change = (
                current_quantity - previous_quantity
            ) / previous_quantity
        else:
            quantity_change = 0

        if previous_revenue > 0:
            revenue_change = (
                current_revenue - previous_revenue
            ) / previous_revenue
        else:
            revenue_change = 0

        # ----------------------------------------------------
        # Absolute revenue impact
        # ----------------------------------------------------

        revenue_change_abs = (
            current_revenue - previous_revenue
        )

        # ----------------------------------------------------
        # Revenue contribution
        # ----------------------------------------------------

        if total_previous_revenue > 0:
            revenue_contribution = (
                previous_revenue / total_previous_revenue
            )
        else:
            revenue_contribution = 0

        # ----------------------------------------------------
        # Material movement
        # ----------------------------------------------------

        quantity_moved = abs(quantity_change) >= threshold
        revenue_moved = abs(revenue_change) >= threshold

        if quantity_moved or revenue_moved:

            results.append(
                {
                    "product": product,
                    "quantity_change": quantity_change,
                    "revenue_change": revenue_change,
                    "revenue_change_abs": revenue_change_abs,
                    "revenue_contribution": revenue_contribution,
                }
            )

    # --------------------------------------------------------
    # Sort by absolute revenue impact
    # --------------------------------------------------------

    results = sorted(
        results,
        key=lambda x: abs(x["revenue_change_abs"]),
        reverse=True,
    )

    return results

# ============================================================
# PRODUCT MOVEMENT SCOPE
# ============================================================

def classify_product_movement(
    current_df: pd.DataFrame,
    previous_df: pd.DataFrame,
    product_diagnosis: list,
    negative_threshold: float = -0.10,
    business_wide_ratio: float = 0.50,
    concentration_threshold: float = 0.50,
) -> dict:
    """
    Determine whether product-level decline is
    business-wide or product-specific.
    """

    # --------------------------------------------------------
    # All products in both periods
    # --------------------------------------------------------

    all_products = set(
        current_df["product"].unique()
    ).union(
        set(previous_df["product"].unique())
    )

    total_products = len(all_products)

    # --------------------------------------------------------
    # Count materially declining products
    # --------------------------------------------------------

    declining_products = [
        result
        for result in product_diagnosis
        if result["revenue_change"] <= negative_threshold
    ]

    declining_count = len(declining_products)

    declining_ratio = (
        declining_count / total_products
        if total_products > 0
        else 0
    )

    # --------------------------------------------------------
    # Negative revenue impact concentration
    # --------------------------------------------------------

    total_negative_impact = sum(
        abs(result["revenue_change_abs"])
        for result in declining_products
        if result["revenue_change_abs"] < 0
    )

    if total_negative_impact > 0:

        largest_negative_impact = max(
            abs(result["revenue_change_abs"])
            for result in declining_products
            if result["revenue_change_abs"] < 0
        )

        top_decline_concentration = (
            largest_negative_impact
            / total_negative_impact
        )

    else:

        top_decline_concentration = 0

    # --------------------------------------------------------
    # Classification
    # --------------------------------------------------------

    if declining_count == 0:

        scope = "NO_MATERIAL_PRODUCT_DECLINE"

    elif (
        declining_ratio >= business_wide_ratio
        and top_decline_concentration < concentration_threshold
    ):

        scope = "BUSINESS_WIDE_DECLINE"

    else:

        scope = "PRODUCT_SPECIFIC_DECLINE"

    return {
        "scope": scope,
        "declining_products": declining_count,
        "total_products_analyzed": total_products,
        "declining_ratio": declining_ratio,
        "top_decline_concentration": top_decline_concentration,
    }

# ============================================================
# PROFITABILITY DIAGNOSIS
# ============================================================

def diagnose_profitability(
    current_df: pd.DataFrame,
    previous_df: pd.DataFrame,
    margin_threshold: float = 0.03,
    cost_per_unit_threshold: float = 0.05,
    revenue_per_unit_threshold: float = 0.05,
) -> dict:
    """
    Diagnose profitability changes between two periods.

    The diagnosis distinguishes:
    - cost pressure
    - revenue/pricing/discount pressure
    - other margin deterioration
    - profitability improvement
    - no material profitability change
    """

    # --------------------------------------------------------
    # Revenue
    # --------------------------------------------------------

    current_revenue = current_df["revenue"].sum()
    previous_revenue = previous_df["revenue"].sum()

    # --------------------------------------------------------
    # Cost
    # --------------------------------------------------------

    current_cost = current_df["cost"].sum()
    previous_cost = previous_df["cost"].sum()

    # --------------------------------------------------------
    # Quantity
    # --------------------------------------------------------

    current_quantity = current_df["quantity"].sum()
    previous_quantity = previous_df["quantity"].sum()

    # --------------------------------------------------------
    # Profit
    # --------------------------------------------------------

    current_profit = current_df["profit"].sum()
    previous_profit = previous_df["profit"].sum()

    # --------------------------------------------------------
    # Margin
    # --------------------------------------------------------

    current_margin = (
        current_profit / current_revenue
        if current_revenue > 0
        else 0
    )

    previous_margin = (
        previous_profit / previous_revenue
        if previous_revenue > 0
        else 0
    )

    margin_change = current_margin - previous_margin

    # --------------------------------------------------------
    # Cost per unit
    # --------------------------------------------------------

    current_cost_per_unit = (
        current_cost / current_quantity
        if current_quantity > 0
        else 0
    )

    previous_cost_per_unit = (
        previous_cost / previous_quantity
        if previous_quantity > 0
        else 0
    )

    cost_per_unit_change = (
        (
            current_cost_per_unit
            - previous_cost_per_unit
        )
        / previous_cost_per_unit
        if previous_cost_per_unit > 0
        else 0
    )

    # --------------------------------------------------------
    # Revenue per unit
    # --------------------------------------------------------

    current_revenue_per_unit = (
        current_revenue / current_quantity
        if current_quantity > 0
        else 0
    )

    previous_revenue_per_unit = (
        previous_revenue / previous_quantity
        if previous_quantity > 0
        else 0
    )

    revenue_per_unit_change = (
        (
            current_revenue_per_unit
            - previous_revenue_per_unit
        )
        / previous_revenue_per_unit
        if previous_revenue_per_unit > 0
        else 0
    )

    # --------------------------------------------------------
    # Total cost change
    # --------------------------------------------------------

    cost_change = (
        (current_cost - previous_cost)
        / previous_cost
        if previous_cost > 0
        else 0
    )

    # --------------------------------------------------------
    # Profit change
    # --------------------------------------------------------

    profit_change = (
        (current_profit - previous_profit)
        / previous_profit
        if previous_profit > 0
        else 0
    )

    # --------------------------------------------------------
    # Diagnosis
    # --------------------------------------------------------

    if margin_change <= -margin_threshold:

        if cost_per_unit_change >= cost_per_unit_threshold:

            diagnosis = (
                "Profitability deterioration "
                "driven by cost pressure"
            )

        elif revenue_per_unit_change <= -revenue_per_unit_threshold:

            diagnosis = (
                "Margin compression driven by "
                "lower realized revenue per unit"
            )

        else:

            diagnosis = (
                "Profit margin deterioration "
                "without a clear cost or revenue-per-unit driver"
            )

    elif margin_change >= margin_threshold:

        diagnosis = "Profitability improvement"

    else:

        diagnosis = "No material profitability change"

    return {
        "current_cost": current_cost,
        "previous_cost": previous_cost,
        "cost_change": cost_change,

        "current_quantity": current_quantity,
        "previous_quantity": previous_quantity,

        "current_cost_per_unit": current_cost_per_unit,
        "previous_cost_per_unit": previous_cost_per_unit,
        "cost_per_unit_change": cost_per_unit_change,

        "current_revenue_per_unit": current_revenue_per_unit,
        "previous_revenue_per_unit": previous_revenue_per_unit,
        "revenue_per_unit_change": revenue_per_unit_change,

        "current_profit": current_profit,
        "previous_profit": previous_profit,
        "profit_change": profit_change,

        "current_margin": current_margin,
        "previous_margin": previous_margin,
        "margin_change": margin_change,

        "diagnosis": diagnosis,
    }

# ============================================================
# BUSINESS MONITORING RESULT
# ============================================================

def build_monitoring_result(
    comparison: dict,
    revenue_diagnosis: str,
    product_diagnosis: list,
    product_movement_scope: dict,
    profitability_diagnosis: dict,
) -> dict:
    """
    Combine analytical outputs into one business monitoring result.

    Monitoring signal describes how unusual the observed movement is.
    Business condition describes the likely business implication.
    """

    # --------------------------------------------------------
    # Monitoring signal
    # --------------------------------------------------------

    signal_priority = {
        "NORMAL": 1,
        "WARNING": 2,
        "ALERT": 3,
    }

    signals = [
        result["signal"]
        for result in comparison.values()
    ]

    monitoring_signal = max(
        signals,
        key=lambda signal: signal_priority[signal],
    )

    # --------------------------------------------------------
    # Revenue movement
    # --------------------------------------------------------

    revenue_change = (
        comparison["total_revenue"]["percentage_change"]
    )

    # --------------------------------------------------------
    # Determine business condition
    # --------------------------------------------------------


    profitability_diagnosis_text = (
        profitability_diagnosis["diagnosis"]
    )

    product_scope = (
        product_movement_scope["scope"]
    )

    top_decline_concentration = (
        product_movement_scope["top_decline_concentration"]
    )

    negative_product_changes = [
        item["revenue_change"]
        for item in product_diagnosis
        if item["revenue_change"] < 0
    ]

    max_product_decline = (
        min(negative_product_changes)
        if negative_product_changes
        else 0.0
    )


    # --------------------------------------------------------
    # Business condition priority
    # --------------------------------------------------------

    if "cost pressure" in profitability_diagnosis_text.lower():

        business_condition = "PROFITABILITY RISK"

    elif revenue_change < -0.10:

        business_condition = "NEGATIVE SALES MOVEMENT"

    elif revenue_change > 0.10:

        if "recovery" in revenue_diagnosis.lower():

            business_condition = "POSITIVE RECOVERY"

        else:

            business_condition = "POSITIVE SALES MOVEMENT"

    elif (
        product_scope == "PRODUCT_SPECIFIC_DECLINE"
        and top_decline_concentration >= 0.50
        and max_product_decline <= -0.20
    ):

        business_condition = "PRODUCT-SPECIFIC ISSUE"

    else:

        business_condition = "STABLE"

    # --------------------------------------------------------
    # Primary signal
    # --------------------------------------------------------

    if revenue_change < 0:

        primary_signal = (
            f"Revenue decreased by "
            f"{abs(revenue_change):.2%}"
        )

    elif revenue_change > 0:

        primary_signal = (
            f"Revenue increased by "
            f"{revenue_change:.2%}"
        )

    else:

        primary_signal = "Revenue remained unchanged"

    supporting_findings = []

    # --------------------------------------------------------
    # Transaction finding
    # --------------------------------------------------------

    if "total_transactions" in comparison:
        transaction_change = (
            comparison["total_transactions"]["percentage_change"]
        )

        supporting_findings.append(
            f"Transactions changed by "
            f"{transaction_change:+.2%}"
        )


    # --------------------------------------------------------
    # AOV finding
    # --------------------------------------------------------

    if "aov" in comparison:
        aov_change = (
            comparison["aov"]["percentage_change"]
        )

        supporting_findings.append(
            f"AOV changed by "
            f"{aov_change:+.2%}"
        )

    # --------------------------------------------------------
    # Product finding
    # --------------------------------------------------------

    if product_scope == "BUSINESS_WIDE_DECLINE":

        supporting_findings.append(
            f"Product performance declined broadly across "
            f"{product_movement_scope['declining_products']} of "
            f"{product_movement_scope['total_products_analyzed']} "
            f"products"
        )

    elif product_scope == "PRODUCT_SPECIFIC_DECLINE":

        if product_diagnosis:

            top_product = product_diagnosis[0]

            supporting_findings.append(
                f"{top_product['product']} revenue changed by "
                f"{top_product['revenue_change']:+.2%}"
            )

    # --------------------------------------------------------
    # Profitability finding
    # --------------------------------------------------------

    margin_change = (
        profitability_diagnosis["margin_change"]
    )

    if abs(margin_change) >= 0.03:

        if margin_change < 0:

            supporting_findings.append(
                f"Profit margin decreased by "
                f"{abs(margin_change):.2%}"
            )

        else:

            supporting_findings.append(
                f"Profit margin increased by "
                f"{margin_change:.2%}"
            )

    # --------------------------------------------------------
    # Return result
    # --------------------------------------------------------

    return {
        "monitoring_signal": monitoring_signal,
        "business_condition": business_condition,
        "primary_signal": primary_signal,
        "revenue_driver": revenue_diagnosis,
        "product_scope": product_scope,
        "supporting_findings": supporting_findings,
    }

# ============================================================
# PERIOD SELECTION
# ============================================================

def select_periods(
    df: pd.DataFrame,
    current_start: str,
    current_end: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Select the current period and its previous equivalent period.

    The previous period has the same duration as the current period
    and ends immediately before it.
    """

    current_start = pd.Timestamp(current_start)
    current_end = pd.Timestamp(current_end)

    if current_end < current_start:
        raise ValueError(
            "current_end cannot be earlier than current_start."
        )

    period_length = (
        current_end - current_start
    ).days + 1

    previous_end = current_start - pd.Timedelta(days=1)

    previous_start = (
        previous_end
        - pd.Timedelta(days=period_length - 1)
    )

    current_period = df[
        (df["date"] >= current_start) &
        (df["date"] <= current_end)
    ].copy()

    previous_period = df[
        (df["date"] >= previous_start) &
        (df["date"] <= previous_end)
    ].copy()

    if current_period.empty:
        raise ValueError(
            "Current period contains no data."
        )

    if previous_period.empty:
        raise ValueError(
            "Previous period contains no data."
        )

    return previous_period, current_period

def prepare_financial_fields(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Derive missing financial fields when sufficient
    information is available.
    """

    df = df.copy()

    if "cost" not in df.columns and "profit" in df.columns:
        df["cost"] = df["revenue"] - df["profit"]

    if "profit" not in df.columns and "cost" in df.columns:
        df["profit"] = df["revenue"] - df["cost"]

    return df

# ============================================================
# ANALYSIS PIPELINE
# ============================================================

def run_analysis(
    df: pd.DataFrame,
    current_start: str,
    current_end: str,
    capabilities: list[str] | None = None,
) -> dict:
    """
    Run the complete analytics pipeline for a selected
    current period.

    The previous equivalent period is selected automatically.
    """

    if capabilities is None:
        capabilities = [
        "sales_monitoring",
        "period_comparison",
        "change_monitoring",
        "product_performance",
        "profitability",
    ]

    # --------------------------------------------------------
    # Select periods
    # --------------------------------------------------------

    previous_period, current_period = select_periods(
        df=df,
        current_start=current_start,
        current_end=current_end,
    )

    # --------------------------------------------------------
    # Period comparison
    # --------------------------------------------------------

    comparison = compare_periods(
        current_df=current_period,
        previous_df=previous_period,
    )

    # --------------------------------------------------------
    # Revenue diagnosis
    # --------------------------------------------------------

    revenue_diagnosis = diagnose_revenue_driver(
        comparison
    )

    # --------------------------------------------------------
    # Product diagnosis
    # --------------------------------------------------------

    if "product_performance" in capabilities:

        product_diagnosis = diagnose_product_performance(
            current_df=current_period,
            previous_df=previous_period,
        )

        product_movement_scope = classify_product_movement(
            current_df=current_period,
            previous_df=previous_period,
            product_diagnosis=product_diagnosis,
        )

    else:
        product_diagnosis = []
        product_movement_scope = {
            "scope": "NOT_AVAILABLE",
            "declining_products": 0,
            "total_products_analyzed": 0,
            "declining_ratio": 0.0,
            "top_decline_concentration": 0.0,
        }

    # --------------------------------------------------------
    # Profitability diagnosis
    # --------------------------------------------------------

    if "profitability" in capabilities:
        profitability_diagnosis = diagnose_profitability(
        current_df=current_period,
        previous_df=previous_period,
    )

    else:
        profitability_diagnosis = {
        "diagnosis": "NOT_AVAILABLE",
        "margin_change": 0.0,
        "profit_change": 0.0,
        "cost_per_unit_change": 0.0,
        "revenue_per_unit_change": 0.0,
        }

    # --------------------------------------------------------
    # Final monitoring result
    # --------------------------------------------------------

    monitoring_result = build_monitoring_result(
        comparison=comparison,
        revenue_diagnosis=revenue_diagnosis,
        product_diagnosis=product_diagnosis,
        product_movement_scope=product_movement_scope,
        profitability_diagnosis=profitability_diagnosis,
    )

    # --------------------------------------------------------
    # Return structured result
    # --------------------------------------------------------

    return {
        "current_period": {
            "start": current_period["date"].min(),
            "end": current_period["date"].max(),
        },

        "previous_period": {
            "start": previous_period["date"].min(),
            "end": previous_period["date"].max(),
        },

        "comparison": comparison,

        "revenue_diagnosis": revenue_diagnosis,

        "product_diagnosis": product_diagnosis,

        "product_movement_scope": product_movement_scope,

        "profitability_diagnosis": profitability_diagnosis,

        "monitoring_result": monitoring_result,
    }

# ============================================================
# EXPORT ANALYSIS RESULT
# ============================================================

def json_serializer(obj):
    """
    Convert Pandas / NumPy objects into JSON-compatible types.
    """

    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()

    if hasattr(obj, "item"):
        return obj.item()

    raise TypeError(
        f"Object of type {type(obj).__name__} "
        f"is not JSON serializable"
    )


def export_analysis_result(
    analysis_result: dict,
    output_path: Path,
) -> None:
    """
    Export the analysis result into a clean JSON file.
    """

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            analysis_result,
            file,
            indent=4,
            ensure_ascii=False,
            default=json_serializer,
        )

# ============================================================
# CHANGE MONITORING
# ============================================================

def classify_change(change_pct: float) -> str:
    """
    Classify a percentage change based on
    observed baseline variability.
    """

    if change_pct <= -0.1781:
        return "ALERT"

    if change_pct < -0.0994:
        return "WARNING"

    if change_pct <= 0.0835:
        return "NORMAL"

    if change_pct < 0.2313:
        return "WARNING"

    return "ALERT"

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    df = load_data(DATA_FILE)


    # ========================================================
    # RUN ANALYSIS PIPELINE
    # ========================================================

    analysis_result = run_analysis(
        df=df,
        current_start="2026-06-15",
        current_end="2026-06-21",
    )

    export_analysis_result(
        analysis_result=analysis_result,
        output_path=ANALYSIS_OUTPUT_FILE,
    )

    # ========================================================
    # SALES MONITORING
    # ========================================================

    metrics = calculate_sales_metrics(df)

    print("\n" + "=" * 70)
    print("SALES MONITORING")
    print("=" * 70)

    print(
        f"Date range           : "
        f"{df['date'].min().date()} → {df['date'].max().date()}"
    )

    print(
        f"Total revenue        : "
        f"Rp {metrics['total_revenue']:,.2f}"
    )

    print(
        f"Total transactions   : "
        f"{metrics['total_transactions']:,}"
    )

    print(
        f"Total quantity       : "
        f"{metrics['total_quantity']:,}"
    )

    print(
        f"AOV                  : "
        f"Rp {metrics['aov']:,.2f}"
    )

    print(
        f"Revenue per day      : "
        f"Rp {metrics['revenue_per_day']:,.2f}"
    )

    print(
        f"Transactions per day : "
        f"{metrics['transactions_per_day']:.2f}"
    )

    print("=" * 70)

    # ========================================================
    # PERIOD COMPARISON
    # ========================================================

    comparison = analysis_result["comparison"]

    print("\n" + "=" * 70)
    print("PERIOD COMPARISON")
    print("=" * 70)

    for metric, result in comparison.items():

        print(f"\n{metric}")

        print(
            f"  Previous : "
            f"{result['previous']:,.2f}"
        )

        print(
            f"  Current  : "
            f"{result['current']:,.2f}"
        )

        print(
            f"  Change   : "
            f"{result['absolute_change']:+,.2f}"
        )

        print(
            f"  Change % : "
            f"{result['percentage_change']:+.2%}"
        )

        print(
            f"  Signal   : "
            f"{result['signal']}"
        )

    print("=" * 70)

    # ========================================================
    # REVENUE DRIVER DIAGNOSIS
    # ========================================================

    print("\n" + "=" * 70)
    print("REVENUE DRIVER DIAGNOSIS")
    print("=" * 70)

    print(
        f"Primary driver : "
        f"{analysis_result['revenue_diagnosis']}"
    )

    print("=" * 70)

    # ========================================================
    # PRODUCT MOVEMENT SCOPE
    # ========================================================

    product_scope = analysis_result["product_movement_scope"]

    print("\n" + "=" * 70)
    print("PRODUCT MOVEMENT SCOPE")
    print("=" * 70)

    print(
        f"Scope                    : "
        f"{product_scope['scope']}"
    )

    print(
        f"Declining products       : "
        f"{product_scope['declining_products']}/"
        f"{product_scope['total_products_analyzed']}"
    )

    print(
        f"Declining ratio          : "
        f"{product_scope['declining_ratio']:.2%}"
    )

    print(
        f"Top decline concentration: "
        f"{product_scope['top_decline_concentration']:.2%}"
    )

    print("=" * 70)

    # ========================================================
    # PROFITABILITY DIAGNOSIS
    # ========================================================

    profitability = analysis_result["profitability_diagnosis"]

    print("\n" + "=" * 70)
    print("PROFITABILITY DIAGNOSIS")
    print("=" * 70)

    print(
        f"Previous cost        : "
        f"Rp {profitability['previous_cost']:,.2f}"
    )

    print(
        f"Current cost         : "
        f"Rp {profitability['current_cost']:,.2f}"
    )

    print(
        f"Cost change          : "
        f"{profitability['cost_change']:+.2%}"
    )

    print(
        f"Previous cost/unit   : "
        f"Rp {profitability['previous_cost_per_unit']:,.2f}"
    )

    print(
        f"Current cost/unit    : "
        f"Rp {profitability['current_cost_per_unit']:,.2f}"
    )

    print(
        f"Cost/unit change     : "
        f"{profitability['cost_per_unit_change']:+.2%}"
    )

    print(
        f"Previous revenue/unit: "
        f"Rp {profitability['previous_revenue_per_unit']:,.2f}"
    )

    print(
        f"Current revenue/unit : "
        f"Rp {profitability['current_revenue_per_unit']:,.2f}"
    )

    print(
        f"Revenue/unit change  : "
        f"{profitability['revenue_per_unit_change']:+.2%}"
    )

    print(
        f"Previous profit      : "
        f"Rp {profitability['previous_profit']:,.2f}"
    )

    print(
        f"Current profit       : "
        f"Rp {profitability['current_profit']:,.2f}"
    )

    print(
        f"Profit change        : "
        f"{profitability['profit_change']:+.2%}"
    )

    print(
        f"Previous margin      : "
        f"{profitability['previous_margin']:.2%}"
    )

    print(
        f"Current margin       : "
        f"{profitability['current_margin']:.2%}"
    )

    print(
        f"Margin change        : "
        f"{profitability['margin_change']:+.2%}"
    )

    print(
        f"\nDiagnosis            : "
        f"{profitability['diagnosis']}"
    )

    print("=" * 70)

    # ========================================================
    # BUSINESS MONITORING RESULT
    # ========================================================

    monitoring_result = analysis_result["monitoring_result"]

    print("\n" + "=" * 70)
    print("BUSINESS MONITORING RESULT")
    print("=" * 70)

    print(
        f"\nMonitoring signal : "
        f"{monitoring_result['monitoring_signal']}"
    )

    print(
        f"Business condition: "
        f"{monitoring_result['business_condition']}"
    )

    print(
        f"\nPrimary signal:\n"
        f"{monitoring_result['primary_signal']}"
    )

    print(
        f"\nPrimary driver:\n"
        f"{monitoring_result['revenue_driver']}"
    )

    print(
        f"\nProduct scope:\n"
        f"{monitoring_result['product_scope']}"
    )

    print("\nSupporting findings:")

    for finding in monitoring_result["supporting_findings"]:
        print(f"- {finding}")

    print("=" * 70)

    print(
        f"Previous period : "
        f"{analysis_result['previous_period']['start'].date()} → "
        f"{analysis_result['previous_period']['end'].date()}"
    )

    print(
        f"Current period  : "
        f"{analysis_result['current_period']['start'].date()} → "
            f"{analysis_result['current_period']['end'].date()}"
        )

