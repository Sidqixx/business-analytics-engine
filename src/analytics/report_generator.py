from pathlib import Path
import json


# ============================================================
# CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "generated"
    / "analysis_result.json"
)

RECOMMENDATION_FILE = (
    BASE_DIR
    / "data"
    / "generated"
    / "recommendation_result.json"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "generated"
    / "business_report.md"
)


# ============================================================
# LOAD ANALYSIS RESULT
# ============================================================

def load_analysis_result(path: Path) -> dict:
    """
    Load structured analytics result from JSON.
    """

    if not path.exists():
        raise FileNotFoundError(
            f"Analysis result not found: {path}"
        )

    with open(
        path,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


# ============================================================
# REPORT GENERATOR
# ============================================================

def load_recommendation_result(path: Path) -> dict:
    """
    Load structured recommendation result from JSON.
    """

    if not path.exists():
        raise FileNotFoundError(
            f"Recommendation result not found: {path}"
        )

    with open(
        path,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)

def generate_business_report(
    analysis_result: dict,
    recommendation_result: dict,
) -> str:
    """
    Convert structured analysis result into an evidence-based
    business report while respecting available data capabilities.
    """

    current_period = analysis_result["current_period"]
    previous_period = analysis_result["previous_period"]

    comparison = analysis_result["comparison"]
    product_scope = analysis_result.get(
        "product_movement_scope",
        {
            "scope": "NOT_AVAILABLE",
            "declining_products": 0,
            "total_products_analyzed": 0,
        },
    )
    profitability = analysis_result.get(
        "profitability_diagnosis",
        {
            "diagnosis": "NOT_AVAILABLE",
            "margin_change": 0.0,
            "profit_change": 0.0,
            "cost_per_unit_change": 0.0,
            "revenue_per_unit_change": 0.0,
        },
    )
    monitoring = analysis_result["monitoring_result"]

    recommendation_summary = recommendation_result["recommendation_summary"]
    supporting_recommendations = recommendation_result.get(
        "supporting_recommendations", []
    )
    recommendation_evidence = recommendation_result.get("evidence", [])

    # --------------------------------------------------------
    # Helpers
    # --------------------------------------------------------

    def format_date(value) -> str:
        if hasattr(value, "strftime"):
            return value.strftime("%Y-%m-%d")
        return str(value)[:10]

    def percentage(value) -> str:
        return f"{value:+.2f}%"

    def percentage_points(value) -> str:
        return f"{value:+.2f} points"

    # --------------------------------------------------------
    # Core metrics
    # --------------------------------------------------------

    revenue_result = comparison.get("total_revenue")
    revenue_change = (
        revenue_result["percentage_change"]
        if revenue_result
        else None
    )

    transaction_result = comparison.get("total_transactions")
    quantity_result = comparison.get("total_quantity")
    aov_result = comparison.get("aov")

    transaction_change = (
        transaction_result["percentage_change"]
        if transaction_result
        else None
    )
    quantity_change = (
        quantity_result["percentage_change"]
        if quantity_result
        else None
    )
    aov_change = (
        aov_result["percentage_change"]
        if aov_result
        else None
    )

    # --------------------------------------------------------
    # Format dates
    # --------------------------------------------------------

    current_start = format_date(current_period["start"])
    current_end = format_date(current_period["end"])
    previous_start = format_date(previous_period["start"])
    previous_end = format_date(previous_period["end"])

    # --------------------------------------------------------
    # Monitoring signal explanation
    # --------------------------------------------------------

    monitoring_signal = monitoring["monitoring_signal"]

    if monitoring_signal == "ALERT":
        signal_explanation = (
            "The observed movement is unusually large "
            "relative to the monitoring baseline."
        )
    elif monitoring_signal == "WARNING":
        signal_explanation = (
            "The observed movement is larger than "
            "typical baseline variation."
        )
    else:
        signal_explanation = (
            "The observed movement is within the "
            "expected monitoring range."
        )

    # --------------------------------------------------------
    # Business condition / recommendation
    # --------------------------------------------------------

    business_condition = monitoring["business_condition"]
    recommendation_priority = recommendation_summary["priority"]
    primary_focus = recommendation_summary["primary_focus"]
    primary_action = recommendation_summary["primary_action"]

    # --------------------------------------------------------
    # Primary finding
    # --------------------------------------------------------

    if revenue_change is None:
        primary_finding = "Revenue movement was not available from the source data."
    elif revenue_change < 0:
        primary_finding = (
            f"Revenue decreased by {abs(revenue_change):.2%} "
            "compared with the previous period."
        )
    elif revenue_change > 0:
        primary_finding = (
            f"Revenue increased by {revenue_change:.2%} "
            "compared with the previous period."
        )
    else:
        primary_finding = (
            "Revenue remained unchanged compared with the previous period."
        )

    # --------------------------------------------------------
    # Revenue interpretation
    # --------------------------------------------------------

    if (
        transaction_change is not None
        and aov_change is not None
    ):
        revenue_interpretation = (
            f"Revenue changed by {revenue_change:+.2%}, while "
            f"transaction volume changed by {transaction_change:+.2%} "
            f"and AOV changed by {aov_change:+.2%}."
        )
    elif transaction_change is not None:
        revenue_interpretation = (
            f"Revenue changed by {revenue_change:+.2%}, while "
            f"transaction volume changed by {transaction_change:+.2%}. "
            "AOV was not available in the source data."
        )
    elif aov_change is not None:
        revenue_interpretation = (
            f"Revenue changed by {revenue_change:+.2%}, while "
            f"AOV changed by {aov_change:+.2%}. "
            "Transaction volume was not available in the source data."
        )
    elif revenue_change is not None:
        revenue_interpretation = (
            f"Revenue changed by {revenue_change:+.2%}. "
            "Transaction volume and AOV were not available in the source data."
        )
    else:
        revenue_interpretation = (
            "Revenue movement could not be interpreted because the revenue KPI "
            "was not available in the source data."
        )

    # --------------------------------------------------------
    # Product interpretation
    # --------------------------------------------------------

    product_scope_label = product_scope.get("scope", "NOT_AVAILABLE")

    if product_scope_label == "BUSINESS_WIDE_DECLINE":
        product_interpretation = (
            f"Product movement was broad-based, with "
            f"{product_scope.get('declining_products', 0)} of "
            f"{product_scope.get('total_products_analyzed', 0)} "
            "products experiencing material decline."
        )
    elif product_scope_label == "PRODUCT_SPECIFIC_DECLINE":
        product_diagnosis = analysis_result.get("product_diagnosis", [])
        if product_diagnosis:
            top_product = product_diagnosis[0]
            product_interpretation = (
                f"{top_product['product']} showed a "
                f"{top_product['revenue_change']:+.2%} revenue change, "
                "indicating a product-specific movement."
            )
        else:
            product_interpretation = "A product-specific movement was detected."
    elif product_scope_label == "NOT_AVAILABLE":
        product_interpretation = (
            "Product-level analysis was not available because product and "
            "quantity fields were not provided in the source data."
        )
    else:
        product_interpretation = "No material product-level decline was detected."

    # --------------------------------------------------------
    # Profitability interpretation
    # --------------------------------------------------------

    profitability_diagnosis = profitability.get("diagnosis", "NOT_AVAILABLE")
    margin_change = profitability.get("margin_change")
    profit_change = profitability.get("profit_change")
    cost_per_unit_change = profitability.get("cost_per_unit_change")
    revenue_per_unit_change = profitability.get("revenue_per_unit_change")

    if profitability_diagnosis == "NOT_AVAILABLE":
        profitability_interpretation = (
            "Profitability analysis was not available because cost or profit "
            "fields were not provided in the source data."
        )
        profitability_detail_lines = []
    elif (
        margin_change is not None
        and profit_change is not None
        and abs(margin_change) < 0.03
        and revenue_change is not None
        and revenue_change < 0
    ):
        profitability_interpretation = (
            f"Profit declined by {abs(profit_change):.2%} alongside the revenue "
            f"decline, while profit margin remained broadly stable "
            f"({margin_change:+.2%} points)."
        )
        profitability_detail_lines = [
            f"- Cost/unit change: {cost_per_unit_change:+.2%}",
            f"- Revenue/unit change: {revenue_per_unit_change:+.2%}",
        ]
    elif profitability_diagnosis == (
        "Profitability deterioration driven by cost pressure"
    ):
        profitability_interpretation = (
            f"Profitability deteriorated as cost per unit increased by "
            f"{cost_per_unit_change:+.2%}, while profit margin changed by "
            f"{margin_change:+.2%} points."
        )
        profitability_detail_lines = [
            f"- Cost/unit change: {cost_per_unit_change:+.2%}",
            f"- Revenue/unit change: {revenue_per_unit_change:+.2%}",
        ]
    elif profitability_diagnosis == (
        "Margin compression driven by lower realized revenue per unit"
    ):
        profitability_interpretation = (
            f"Profit increased by {profit_change:+.2%}, while margin compressed "
            f"by {abs(margin_change):.2%} points as realized revenue per unit "
            f"changed by {revenue_per_unit_change:+.2%}."
        )
        profitability_detail_lines = [
            f"- Cost/unit change: {cost_per_unit_change:+.2%}",
            f"- Revenue/unit change: {revenue_per_unit_change:+.2%}",
        ]
    elif profitability_diagnosis == "Profitability improvement":
        profitability_interpretation = (
            f"Profitability improved, with profit changing by "
            f"{profit_change:+.2%} and margin changing by "
            f"{margin_change:+.2%} points."
        )
        profitability_detail_lines = [
            f"- Cost/unit change: {cost_per_unit_change:+.2%}",
            f"- Revenue/unit change: {revenue_per_unit_change:+.2%}",
        ]
    else:
        profitability_interpretation = (
            "No material profitability movement was detected."
        )
        profitability_detail_lines = [
            f"- Cost/unit change: {cost_per_unit_change:+.2%}",
            f"- Revenue/unit change: {revenue_per_unit_change:+.2%}",
        ]

    # --------------------------------------------------------
    # KPI table
    # --------------------------------------------------------

    kpi_rows = []

    if "total_revenue" in comparison:
        kpi_rows.append(
        f"| Revenue | {comparison['total_revenue']['percentage_change']:.2%} |"
    )
    if "total_transactions" in comparison:
        kpi_rows.append(
            f"| Transactions | {comparison['total_transactions']['percentage_change']:.2%} |"
        )

    if "total_quantity" in comparison:
        kpi_rows.append(
            f"| Quantity | {comparison['total_quantity']['percentage_change']:.2%} |"
        )

    if "aov" in comparison:
        kpi_rows.append(
            f"| AOV | {comparison['aov']['percentage_change']:.2%} |"
        )

    if kpi_rows:
        kpi_table = "\n".join(
            [
                "| KPI | Change |",
                "|---|---:|",
                *kpi_rows,
            ]
        )
    else:
        kpi_table = (
            "No comparable KPI movement was available from the source data."
        )

    # --------------------------------------------------------
    # Build report
    # --------------------------------------------------------

    report = f"""
# Business Performance Report

## Analysis Period

**Current:** {current_start} → {current_end}  
**Previous:** {previous_start} → {previous_end}

---

## Overall Status

**Monitoring Signal:** `{monitoring_signal}`

{signal_explanation}

**Business Condition:** `{business_condition}`

---

## Recommendation

**Priority:** `{recommendation_priority}`

**Primary Focus:** {primary_focus}

**Recommended Action:** {primary_action}

---

## Primary Finding

**{primary_finding}**

{revenue_interpretation}

---

## KPI Movement

{kpi_table}

---

## Product Performance

**Scope:** `{product_scope_label}`

{product_interpretation}

---

## Profitability

{profitability_interpretation}
"""

    if profitability_detail_lines:
        report += "\n" + "\n".join(profitability_detail_lines) + "\n"

    report += """
---

## Supporting Findings

"""

    supporting_findings = monitoring.get("supporting_findings", [])
    if supporting_findings:
        for finding in supporting_findings:
            report += f"- {finding}\n"
    else:
        report += "No additional supporting findings were identified.\n"

    if supporting_recommendations:
        report += "\n---\n\n## Supporting Recommendations\n\n"
        for item in supporting_recommendations:
            report += (
                f"- **{item['focus']}:** "
                f"{item['action']}\n"
            )

    report += "\n---\n\n## Recommendation Evidence\n\n"

    if recommendation_evidence:
        for item in recommendation_evidence:
            report += f"- {item}\n"
    else:
        report += "No recommendation evidence was provided.\n"

    return report.strip()

# ============================================================
# SAVE REPORT
# ============================================================

def save_report(
    report: str,
    output_path: Path,
) -> None:
    """
    Save generated business report as Markdown.
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
        file.write(report)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    analysis_result = load_analysis_result(
        INPUT_FILE
    )

    recommendation_result = load_recommendation_result(
        RECOMMENDATION_FILE
    )

    report = generate_business_report(
        analysis_result=analysis_result,
        recommendation_result=recommendation_result,
    )

    save_report(
        report=report,
        output_path=OUTPUT_FILE,
    )

    print("\n" + "=" * 70)
    print("BUSINESS REPORT GENERATED")
    print("=" * 70)

    print(
        f"\nSaved to:\n{OUTPUT_FILE}"
    )

    print("=" * 70)