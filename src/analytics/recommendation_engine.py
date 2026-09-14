"""
Recommendation Engine
---------------------
Transforms analytics diagnosis into evidence-based
business follow-up recommendations.

This module does NOT recompute analytics.
It only interprets the structured output produced
by analytics_engine.py.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# ============================================================
# PATH CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "generated"
    / "analysis_result.json"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "generated"
    / "recommendation_result.json"
)

# ============================================================
# LOAD INPUT
# ============================================================

def load_analysis_result(path: str | Path) -> dict[str, Any]:
    """
    Load analysis_result.json and validate basic structure.
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Analysis result not found: {path}")

    with open(path, "r", encoding="utf-8") as file:
        result = json.load(file)

    if not isinstance(result, dict):
        raise ValueError("Analysis result must be a JSON object.")

    required_keys = [
        "comparison",
        "revenue_diagnosis",
        "product_movement_scope",
        "profitability_diagnosis",
        "monitoring_result",
    ]

    missing_keys = [key for key in required_keys if key not in result]

    if missing_keys:
        raise ValueError(
            f"Analysis result is missing required keys: {missing_keys}"
        )

    return result


# ============================================================
# HELPERS
# ============================================================

def pct(value: float) -> float:
    """Convert decimal percentage change into display percentage."""
    return value * 100


def get_comparison_value(
    analysis_result: dict[str, Any],
    metric: str,
    field: str = "percentage_change",
) -> float:
    """
    Safely retrieve a comparison metric.
    """
    return float(
        analysis_result["comparison"][metric][field]
    )


# ============================================================
# PRIORITY
# ============================================================

def assign_priority(
    analysis_result: dict[str, Any],
    primary_focus: str,
) -> str:
    """
    Assign follow-up priority.

    Priority reflects business follow-up urgency,
    not the unusualness of the observed movement.
    """

    business_condition = analysis_result[
        "monitoring_result"
    ]["business_condition"]

    # --------------------------------------------------------
    # HIGH PRIORITY
    # --------------------------------------------------------

    if business_condition in {
        "NEGATIVE SALES MOVEMENT",
        "PROFITABILITY RISK",
    }:
        return "HIGH"

    # --------------------------------------------------------
    # MEDIUM PRIORITY
    # --------------------------------------------------------

    if business_condition in {
        "PRODUCT-SPECIFIC ISSUE",
        "POSITIVE SALES MOVEMENT",
    }:
        return "MEDIUM"

    if primary_focus in {
        "Basket Value",
        "Promotion Economics",
        "Growth Sustainability",
    }:
        return "MEDIUM"

    # --------------------------------------------------------
    # LOW PRIORITY
    # --------------------------------------------------------

    return "LOW"
    


# ============================================================
# PRIMARY RECOMMENDATION
# ============================================================

def determine_primary_recommendation(
    analysis_result: dict[str, Any],
) -> dict[str, str]:
    """
    Determine the primary focus and recommended action
    based on analytical diagnosis.
    """

    monitoring = analysis_result["monitoring_result"]
    business_condition = monitoring["business_condition"]

    revenue_diagnosis = analysis_result["revenue_diagnosis"]

    profitability = analysis_result["profitability_diagnosis"]
    profitability_diagnosis = profitability["diagnosis"]

    product_scope = analysis_result["product_movement_scope"]["scope"]

    # --------------------------------------------------------
    # PROFITABILITY RISK
    # --------------------------------------------------------

    if business_condition == "PROFITABILITY RISK":

        if "cost pressure" in profitability_diagnosis.lower():
            return {
                "focus": "Cost Structure",
                "action": "Review cost drivers and margin pressure",
            }

        if "revenue per unit" in profitability_diagnosis.lower():
            return {
                "focus": "Revenue / Unit Economics",
                "action": "Review factors affecting realized revenue per unit",
            }

        return {
            "focus": "Profitability",
            "action": "Investigate factors affecting profit margin",
        }

    # --------------------------------------------------------
    # PRODUCT-SPECIFIC ISSUE
    # --------------------------------------------------------

    if business_condition == "PRODUCT-SPECIFIC ISSUE":
        return {
            "focus": "Product Performance",
            "action": "Review performance of materially declining products",
        }

    # --------------------------------------------------------
    # NEGATIVE SALES MOVEMENT
    # --------------------------------------------------------

    if business_condition == "NEGATIVE SALES MOVEMENT":

        transaction_result = analysis_result["comparison"].get(
            "total_transactions"
        )

        aov_result = analysis_result["comparison"].get(
            "aov"
        )

        # --------------------------------------------------------
        # Transaction + AOV available
        # --------------------------------------------------------

        if (
            transaction_result is not None
            and aov_result is not None
        ):

            transaction_change = (
                transaction_result["percentage_change"]
            )

            aov_change = (
                aov_result["percentage_change"]
            )

            transaction_decline = (
                transaction_change <= -0.10
            )

            aov_decline = (
                aov_change <= -0.10
            )

            if transaction_decline and aov_decline:
                return {
                    "focus": "Transaction Volume + Basket Value",
                    "action": (
                        "Investigate both demand movement and "
                        "basket-size movement"
                    ),
                }

            if transaction_decline:
                return {
                    "focus": "Transaction Volume",
                    "action": (
                        "Investigate transaction-volume drivers"
                    ),
                }

            if aov_decline:
                return {
                    "focus": "Basket Value",
                    "action": (
                        "Investigate factors affecting basket value"
                    ),
                }

            return {
                "focus": "Sales Performance",
                "action": (
                    "Investigate the drivers of the "
                    "negative sales movement"
                ),
            }

        # --------------------------------------------------------
        # Revenue-only fallback
        # --------------------------------------------------------

        return {
            "focus": "Sales Performance",
            "action": (
                "Investigate the drivers of the "
                "negative sales movement"
            ),
        }

    # --------------------------------------------------------
    # POSITIVE SALES MOVEMENT
    # --------------------------------------------------------

    if business_condition == "POSITIVE SALES MOVEMENT":

        return {
            "focus": "Growth Sustainability",
            "action": (
                "Monitor whether the improvement persists"
            ),
        }

    # --------------------------------------------------------
    # STABLE
    # --------------------------------------------------------

    return {
        "focus": "Routine Monitoring",
        "action": "Continue monitoring key business KPIs",
    }


# ============================================================
# SUPPORTING RECOMMENDATIONS
# ============================================================

def determine_supporting_actions(
    analysis_result: dict[str, Any],
    primary_focus: str,
) -> list[dict[str, str]]:
    """
    Generate up to two supporting recommendations.
    """

    supporting: list[dict[str, str]] = []

    monitoring = analysis_result["monitoring_result"]

    business_condition = monitoring["business_condition"]

    product_scope = analysis_result["product_movement_scope"]["scope"]

    # --------------------------------------------------------
    # BUSINESS-WIDE PRODUCT DECLINE
    # --------------------------------------------------------

    if (
        product_scope == "BUSINESS_WIDE_DECLINE"
        and primary_focus != "Product Performance"
    ):
        supporting.append(
            {
                "focus": "Business-wide Product Movement",
                "action": (
                    "Review broad-based product decline "
                    "for common demand patterns"
                ),
            }
        )

    # --------------------------------------------------------
    # AOV MONITORING
    # --------------------------------------------------------

    aov_result = analysis_result["comparison"].get(
        "aov"
    )

    if (
        business_condition == "NEGATIVE SALES MOVEMENT"
        and primary_focus == "Transaction Volume"
        and aov_result is not None
        and abs(aov_result["percentage_change"]) < 0.10
    ):
        supporting.append(
            {
                "focus": "Basket Value",
                "action": (
                    "Monitor AOV to confirm basket size "
                    "remains broadly stable"
                ),
            }
        )

    # Keep recommendations concise
    return supporting[:2]


# ============================================================
# EVIDENCE BUILDER
# ============================================================

def build_evidence(
    analysis_result: dict[str, Any],
    primary_focus: str,
) -> list[str]:
    """
    Build context-aware evidence statements.

    Evidence is only generated from metrics that are
    available in the analysis result.
    """

    evidence: list[str] = []

    comparison = analysis_result["comparison"]
    profitability = analysis_result["profitability_diagnosis"]
    product_scope = analysis_result["product_movement_scope"]

    # --------------------------------------------------------
    # Always available: Revenue
    # --------------------------------------------------------

    revenue_change = pct(
        comparison["total_revenue"]["percentage_change"]
    )

    # --------------------------------------------------------
    # TRANSACTION VOLUME
    # --------------------------------------------------------

    if primary_focus == "Transaction Volume":

        transaction_change = pct(
            comparison["total_transactions"][
                "percentage_change"
            ]
        )

        aov_change = pct(
            comparison["aov"][
                "percentage_change"
            ]
        )

        evidence.append(
            f"Revenue changed by {revenue_change:+.2f}%"
        )

        evidence.append(
            f"Transaction volume changed by "
            f"{transaction_change:+.2f}%"
        )

        evidence.append(
            f"AOV changed by {aov_change:+.2f}%"
        )

        return evidence

    # --------------------------------------------------------
    # TRANSACTION VOLUME + BASKET VALUE
    # --------------------------------------------------------

    if primary_focus == "Transaction Volume + Basket Value":

        transaction_change = pct(
            comparison["total_transactions"][
                "percentage_change"
            ]
        )

        aov_change = pct(
            comparison["aov"][
                "percentage_change"
            ]
        )

        evidence.append(
            f"Revenue changed by {revenue_change:+.2f}%"
        )

        evidence.append(
            f"Transaction volume changed by "
            f"{transaction_change:+.2f}%"
        )

        evidence.append(
            f"AOV changed by {aov_change:+.2f}%"
        )

        return evidence

    # --------------------------------------------------------
    # BASKET VALUE
    # --------------------------------------------------------

    if primary_focus == "Basket Value":

        aov_change = pct(
            comparison["aov"][
                "percentage_change"
            ]
        )

        evidence.append(
            f"Revenue changed by {revenue_change:+.2f}%"
        )

        evidence.append(
            f"AOV changed by {aov_change:+.2f}%"
        )

        if "total_transactions" in comparison:

            transaction_change = pct(
                comparison["total_transactions"][
                    "percentage_change"
                ]
            )

            evidence.append(
                f"Transaction volume changed by "
                f"{transaction_change:+.2f}%"
            )

        return evidence

    # --------------------------------------------------------
    # PRODUCT PERFORMANCE
    # --------------------------------------------------------

    if primary_focus == "Product Performance":

        product_diagnosis = (
            analysis_result["product_diagnosis"]
        )

        declining_products = [
            item
            for item in product_diagnosis
            if item["revenue_change"] < 0
        ]

        if declining_products:

            top_declining_product = min(
                declining_products,
                key=lambda item: item["revenue_change_abs"],
            )

            product_name = (
                top_declining_product["product"]
            )

            product_change = pct(
                top_declining_product["revenue_change"]
            )

            evidence.append(
                f"{product_name} revenue changed by "
                f"{product_change:+.2f}%"
            )

        evidence.append(
            "Product movement was concentrated in "
            f'{product_scope["declining_products"]} of '
            f'{product_scope["total_products_analyzed"]} products'
        )

        evidence.append(
            f"Overall revenue changed by "
            f"{revenue_change:+.2f}%"
        )

        return evidence

    # --------------------------------------------------------
    # BUSINESS-WIDE PRODUCT MOVEMENT
    # --------------------------------------------------------

    if primary_focus == "Business-wide Product Movement":

        evidence.append(
            "Product performance declined broadly across "
            f'{product_scope["declining_products"]} of '
            f'{product_scope["total_products_analyzed"]} products'
        )

        evidence.append(
            f"Revenue changed by {revenue_change:+.2f}%"
        )

        return evidence

    # --------------------------------------------------------
    # COST STRUCTURE
    # --------------------------------------------------------

    if primary_focus == "Cost Structure":

        cost_per_unit_change = pct(
            profitability["cost_per_unit_change"]
        )

        margin_change = (
            profitability["margin_change"] * 100
        )

        profit_change = pct(
            profitability["profit_change"]
        )

        evidence.append(
            f"Cost per unit changed by "
            f"{cost_per_unit_change:+.2f}%"
        )

        evidence.append(
            f"Profit margin changed by "
            f"{margin_change:+.2f} percentage points"
        )

        evidence.append(
            f"Profit changed by "
            f"{profit_change:+.2f}%"
        )

        return evidence

    # --------------------------------------------------------
    # REVENUE / UNIT ECONOMICS
    # --------------------------------------------------------

    if primary_focus == "Revenue / Unit Economics":

        revenue_per_unit_change = pct(
            profitability["revenue_per_unit_change"]
        )

        margin_change = (
            profitability["margin_change"] * 100
        )

        profit_change = pct(
            profitability["profit_change"]
        )

        evidence.append(
            f"Revenue per unit changed by "
            f"{revenue_per_unit_change:+.2f}%"
        )

        evidence.append(
            f"Profit margin changed by "
            f"{margin_change:+.2f} percentage points"
        )

        evidence.append(
            f"Profit changed by "
            f"{profit_change:+.2f}%"
        )

        return evidence

    # --------------------------------------------------------
    # PROFITABILITY
    # --------------------------------------------------------

    if primary_focus == "Profitability":

        margin_change = (
            profitability["margin_change"] * 100
        )

        profit_change = pct(
            profitability["profit_change"]
        )

        evidence.append(
            f"Profit margin changed by "
            f"{margin_change:+.2f} percentage points"
        )

        evidence.append(
            f"Profit changed by "
            f"{profit_change:+.2f}%"
        )

        return evidence

    # --------------------------------------------------------
    # PROMOTION ECONOMICS
    # --------------------------------------------------------

    if primary_focus == "Promotion Economics":

        revenue_per_unit_change = pct(
            profitability["revenue_per_unit_change"]
        )

        margin_change = (
            profitability["margin_change"] * 100
        )

        evidence.append(
            f"Revenue increased by "
            f"{revenue_change:.2f}%"
        )

        evidence.append(
            f"Revenue per unit changed by "
            f"{revenue_per_unit_change:+.2f}%"
        )

        evidence.append(
            f"Profit margin changed by "
            f"{margin_change:+.2f} percentage points"
        )

        return evidence

    # --------------------------------------------------------
    # GROWTH SUSTAINABILITY
    # --------------------------------------------------------

    if primary_focus == "Growth Sustainability":

        evidence.append(
            f"Revenue increased by "
            f"{revenue_change:.2f}%"
        )

        if "total_transactions" in comparison:

            transaction_change = pct(
                comparison["total_transactions"][
                    "percentage_change"
                ]
            )

            evidence.append(
                f"Transaction volume changed by "
                f"{transaction_change:+.2f}%"
            )

        if "aov" in comparison:

            aov_change = pct(
                comparison["aov"][
                    "percentage_change"
                ]
            )

            evidence.append(
                f"AOV changed by "
                f"{aov_change:+.2f}%"
            )

        return evidence

    # --------------------------------------------------------
    # ROUTINE MONITORING
    # --------------------------------------------------------

    if primary_focus == "Routine Monitoring":

        evidence.append(
            f"Revenue changed by "
            f"{revenue_change:+.2f}%"
        )

        if "total_transactions" in comparison:

            transaction_change = pct(
                comparison["total_transactions"][
                    "percentage_change"
                ]
            )

            evidence.append(
                f"Transaction volume changed by "
                f"{transaction_change:+.2f}%"
            )

        if "aov" in comparison:

            aov_change = pct(
                comparison["aov"][
                    "percentage_change"
                ]
            )

            evidence.append(
                f"AOV changed by "
                f"{aov_change:+.2f}%"
            )

        return evidence

    # --------------------------------------------------------
    # SALES PERFORMANCE
    # --------------------------------------------------------

    if primary_focus == "Sales Performance":

        evidence.append(
            f"Revenue changed by "
            f"{revenue_change:+.2f}%"
        )

        return evidence

    # --------------------------------------------------------
    # FALLBACK
    # --------------------------------------------------------

    evidence.append(
        f"Revenue changed by "
        f"{revenue_change:+.2f}%"
    )

    return evidence


# ============================================================
# MAIN ENGINE
# ============================================================

def generate_recommendation(
    analysis_result: dict[str, Any],
) -> dict[str, Any]:
    """
    Generate deterministic business recommendations.
    """

    primary = determine_primary_recommendation(
        analysis_result
    )

    supporting = determine_supporting_actions(
        analysis_result,
        primary["focus"],
    )

    priority = assign_priority(
        analysis_result,
        primary["focus"],
    )

    evidence = build_evidence(
        analysis_result,
        primary["focus"],
    )

    return {
        "recommendation_summary": {
            "priority": priority,
            "primary_focus": primary["focus"],
            "primary_action": primary["action"],
        },
        "supporting_recommendations": supporting,
        "evidence": evidence,
    }


# ============================================================
# EXPORT
# ============================================================

def export_recommendation(
    recommendation: dict[str, Any],
    output_path: str | Path,
) -> None:
    """
    Export recommendation result to JSON.
    """

    output_path = Path(output_path)
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
            recommendation,
            file,
            indent=4,
            ensure_ascii=False,
        )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    analysis_result = load_analysis_result(INPUT_FILE)

    recommendation = generate_recommendation(
        analysis_result
    )

    print("=" * 60)
    print("RECOMMENDATION ENGINE")
    print("=" * 60)

    print(
        f"Priority       : "
        f'{recommendation["recommendation_summary"]["priority"]}'
    )

    print(
        f"Primary Focus  : "
        f'{recommendation["recommendation_summary"]["primary_focus"]}'
    )

    print(
        f"Primary Action : "
        f'{recommendation["recommendation_summary"]["primary_action"]}'
    )

    print("\nSupporting Recommendations:")

    for item in recommendation["supporting_recommendations"]:
        print(
            f"- {item['focus']}: "
            f"{item['action']}"
        )

    print("\nEvidence:")

    for item in recommendation["evidence"]:
        print(f"- {item}")

    export_recommendation(
        recommendation,
        OUTPUT_FILE
    )

    print("\n" + "=" * 60)
    print(f"Exported to: {OUTPUT_FILE}")
    print("=" * 60)