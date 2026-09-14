"""
Business Analytics Automation Pipeline
--------------------------------------
Orchestrates the complete analytics workflow:

1. Load transactional data
2. Run analytics and diagnosis
3. Export analysis result
4. Generate recommendations
5. Export recommendation result
6. Generate business report
7. Export business report
"""

from __future__ import annotations
import pandas as pd
from pathlib import Path
import os
import sys
from dotenv import load_dotenv


# ============================================================
# IMPORT MODULES
# ============================================================

ENV_FILE = (
    Path(__file__).resolve().parents[2]
    / ".env"
)

load_dotenv(ENV_FILE)

from analytics_engine import (
    load_data,
    run_analysis,
    export_analysis_result,
)

from recommendation_engine import (
    generate_recommendation,
    export_recommendation,
)

from report_generator import (
    generate_business_report,
    save_report,
)

from schema_mapping import (
    map_schema,
    prepare_data,
)


# ============================================================
# CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

output_dir_value = os.getenv(
    "OUTPUT_DIR",
    "data/generated"
)

OUTPUT_DIR = Path(output_dir_value)

if not OUTPUT_DIR.is_absolute():
    OUTPUT_DIR = BASE_DIR / OUTPUT_DIR

ANALYSIS_OUTPUT = OUTPUT_DIR / "analysis_result.json"
RECOMMENDATION_OUTPUT = OUTPUT_DIR / "recommendation_result.json"
REPORT_OUTPUT = OUTPUT_DIR / "business_report.md"

def get_pipeline_arguments() -> tuple[Path, str, str]:
    """
    Get input file and analysis period from command-line arguments.

    Usage:
        python run_pipeline.py <csv_path> <current_start> <current_end>
    """

    if len(sys.argv) < 4:
        raise ValueError(
            "Input file and analysis period are required.\n"
            "Usage: python run_pipeline.py "
            "<path_to_csv> <current_start> <current_end>"
        )

    input_path = Path(sys.argv[1]).expanduser()

    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_path}"
        )

    if not input_path.is_file():
        raise ValueError(
            f"Input path is not a file: {input_path}"
        )

    if input_path.suffix.lower() != ".csv":
        raise ValueError(
            f"Unsupported file type: {input_path.suffix}. "
            "Expected a CSV file."
        )

    current_start = sys.argv[2]
    current_end = sys.argv[3]

    # Validate that the supplied dates are parseable.
    try:
        pd.to_datetime(current_start)
        pd.to_datetime(current_end)
    except Exception as exc:
        raise ValueError(
            "Analysis period must use valid date values "
            "such as YYYY-MM-DD."
        ) from exc

    return (
        input_path.resolve(),
        current_start,
        current_end,
    )

def validate_analysis_period(
    df: pd.DataFrame,
    current_start: str,
    current_end: str,
) -> tuple[pd.Timestamp, pd.Timestamp]:
    """
    Validate the requested analysis period against the dataset.
    """

    start = pd.to_datetime(
        current_start,
        errors="raise",
    )

    end = pd.to_datetime(
        current_end,
        errors="raise",
    )

    if start > end:
        raise ValueError(
            "Analysis period start date cannot be later "
            "than the end date."
        )

    min_date = df["date"].min()
    max_date = df["date"].max()

    if pd.isna(min_date) or pd.isna(max_date):
        raise ValueError(
            "Dataset does not contain valid dates."
        )

    if end < min_date or start > max_date:
        raise ValueError(
            f"Analysis period {start.date()} to {end.date()} "
            f"does not overlap the dataset date range "
            f"({min_date.date()} to {max_date.date()})."
        )

    return start, end

# ============================================================
# PIPELINE
# ============================================================

def run_pipeline(
    data_file: Path,
    current_start: str,
    current_end: str,
) -> dict:
    """
    Run the complete business analytics automation pipeline.

    The pipeline is responsible for analysis, recommendation, and report
    generation. Delivery mechanisms such as email are handled by the
    calling layer (e.g. Streamlit or CLI), not here.
    """

    DATA_FILE = data_file
    
    print("\n" + "=" * 70)
    print("BUSINESS ANALYTICS AUTOMATION PIPELINE")
    print("=" * 70)

    print(
        f"\nInput file:\n{DATA_FILE}"
    )

    print(
        f"\nAnalysis period:\n"
        f"{current_start} → {current_end}"
    )

    # --------------------------------------------------------
    # 1. LOAD DATA
    # --------------------------------------------------------
    print("\n[1/5] Loading and mapping transactional data...")
    raw_df = load_data(DATA_FILE)

    print(
        f"      Raw data loaded: {len(raw_df):,} rows"
    )

    canonical_df, mapping_metadata = map_schema(
        raw_df
    )

    print("      Schema mapping completed")

    data_quality = mapping_metadata["data_quality"]

    print("      Data quality validation:")
    print(
        f"      - Date: {data_quality['checks']['date']['status']}"
    )
    print(
        f"      - Revenue: {data_quality['checks']['revenue']['status']}"
    )

    if data_quality["status"] == "ERROR":

        error_message = (
            "Data quality validation failed:\n"
            + "\n".join(
                f"- {error}"
                for error in data_quality["errors"]
            )
        )

        raise ValueError(error_message)

    prepared_df, preparation_metadata = prepare_data(
        canonical_df
    )

    current_start_date, current_end_date = validate_analysis_period(
        prepared_df,
        current_start,
        current_end,
    )

    print("      Data preparation:")
    print(
        f"      - Input rows: "
        f"{preparation_metadata['rows_input']:,}"
    )
    print(
        f"      - Output rows: "
        f"{preparation_metadata['rows_output']:,}"
    )
    print(
        f"      - Excluded rows: "
        f"{preparation_metadata['rows_excluded']:,}"
    )
    print(
        f"      - Status: "
        f"{preparation_metadata['status']}"
    )
    # --------------------------------------------------------
    # 2. ANALYTICS ENGINE
    # --------------------------------------------------------

    print("\n[2/5] Running analytics engine...")

    analysis_result = run_analysis(
        prepared_df,
        current_start=current_start_date,
        current_end=current_end_date,
        capabilities=mapping_metadata["available_capabilities"],
    )

    export_analysis_result(
        analysis_result,
        ANALYSIS_OUTPUT,
    )

    print(
        f"      Analysis result exported to:\n"
        f"      {ANALYSIS_OUTPUT}"
    )

    # --------------------------------------------------------
    # 3. RECOMMENDATION ENGINE
    # --------------------------------------------------------

    print("\n[3/5] Running recommendation engine...")

    recommendation_result = generate_recommendation(
        analysis_result
    )

    export_recommendation(
        recommendation_result,
        RECOMMENDATION_OUTPUT,
    )

    print(
        f"      Recommendation result exported to:\n"
        f"      {RECOMMENDATION_OUTPUT}"
    )

    # --------------------------------------------------------
    # 4. REPORT GENERATOR
    # --------------------------------------------------------

    print("\n[4/5] Generating business report...")

    report = generate_business_report(
        analysis_result=analysis_result,
        recommendation_result=recommendation_result,
    )

    
    recommendation_summary = (
        recommendation_result["recommendation_summary"]
    )

    save_report(
        report=report,
        output_path=REPORT_OUTPUT,
    )

    print(
        f"      Business report exported to:\n"
        f"      {REPORT_OUTPUT}"
    )

    # --------------------------------------------------------
    # 5. BUILD PIPELINE RESULT
    # --------------------------------------------------------

    comparison = analysis_result["comparison"]

    product_scope = analysis_result["product_movement_scope"]
    product_diagnosis = analysis_result["product_diagnosis"]
    profitability = analysis_result["profitability_diagnosis"]

    result = {
        "status": "success",

        "analysis_period": {
            "start": str(current_start),
            "end": str(current_end),
        },

        "priority": recommendation_summary["priority"],
        "primary_focus": recommendation_summary["primary_focus"],
        "primary_action": recommendation_summary["primary_action"],

        "business_condition": (
            analysis_result["monitoring_result"]["business_condition"]
        ),

        "kpis": {
            "revenue": (
                comparison["total_revenue"]["percentage_change"]
                if "total_revenue" in comparison
                else None
            ),
            "transactions": (
                comparison["total_transactions"]["percentage_change"]
                if "total_transactions" in comparison
                else None
            ),
            "quantity": (
                comparison["total_quantity"]["percentage_change"]
                if "total_quantity" in comparison
                else None
            ),
            "aov": (
                comparison["aov"]["percentage_change"]
                if "aov" in comparison
                else None
            ),
        },

        "product_performance": {
            "scope": product_scope["scope"],
            "declining_products": product_scope["declining_products"],
            "total_products_analyzed": product_scope[
                "total_products_analyzed"
            ],
            "diagnosis": product_diagnosis,
        },

        "profitability": {
            "diagnosis": profitability["diagnosis"],
            "margin_change": profitability["margin_change"],
            "profit_change": profitability["profit_change"],
            "cost_per_unit_change": profitability[
                "cost_per_unit_change"
            ],
            "revenue_per_unit_change": profitability[
                "revenue_per_unit_change"
            ],
        },

        "supporting_findings": analysis_result[
            "monitoring_result"
        ]["supporting_findings"],

        "supporting_recommendations": recommendation_result[
            "supporting_recommendations"
        ],

        "recommendation_evidence": recommendation_result[
            "evidence"
        ],

        "outputs": {
            "analysis": str(ANALYSIS_OUTPUT),
            "recommendation": str(RECOMMENDATION_OUTPUT),
            "report": str(REPORT_OUTPUT),
        },
    }

    # --------------------------------------------------------
    # PIPELINE SUMMARY
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 70)

    print(
        f"\nAnalysis Period : "
        f"{current_start} → {current_end}"
    )

    print(
        f"Priority        : "
        f"{recommendation_summary['priority']}"
    )

    print(
        f"Primary Focus   : "
        f"{recommendation_summary['primary_focus']}"
    )

    print(
        f"Primary Action  : "
        f"{recommendation_summary['primary_action']}"
    )

    print("\nOutputs:")
    print(f"- {ANALYSIS_OUTPUT}")
    print(f"- {RECOMMENDATION_OUTPUT}")
    print(f"- {REPORT_OUTPUT}")

    print("\n" + "=" * 70)

    return result


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    data_file, current_start, current_end = (
        get_pipeline_arguments()
    )

    run_pipeline(
        data_file=data_file,
        current_start=current_start,
        current_end=current_end,
    )


if __name__ == "__main__":
    try:
        main()

    except FileNotFoundError as exc:
        print("\n" + "=" * 70)
        print("PIPELINE FAILED")
        print("=" * 70)

        print("\nError:")
        print(f"      {exc}")

        print("\nPipeline stopped.")
        print("=" * 70)

    except ValueError as exc:
        print("\n" + "=" * 70)
        print("INPUT VALIDATION FAILED")
        print("=" * 70)

        print("\nError:")
        print(f"      {exc}")

        print("\nPipeline stopped.")
        print("=" * 70)

    except Exception as exc:
        print("\n" + "=" * 70)
        print("UNEXPECTED PIPELINE ERROR")
        print("=" * 70)

        print("\nError:")
        print(f"      {exc}")

        print("\nPipeline stopped.")
        print("=" * 70)
