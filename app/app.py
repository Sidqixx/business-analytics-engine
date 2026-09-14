from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import os
import re
import sys

import pandas as pd
import streamlit as st
from dotenv import load_dotenv


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ANALYTICS_DIR = PROJECT_ROOT / "src" / "analytics"

if str(ANALYTICS_DIR) not in sys.path:
    sys.path.append(str(ANALYTICS_DIR))

from run_pipeline import run_pipeline
from schema_mapping import map_schema
from email_delivery import send_email


# ============================================================
# EMAIL CONFIG
# ============================================================

ENV_FILE = PROJECT_ROOT / ".env"
load_dotenv(ENV_FILE)

ENABLE_EMAIL = (
    os.getenv("ENABLE_EMAIL", "false").lower() == "true"
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Business Analytics Automation",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CUSTOM STYLES
# ============================================================

st.markdown(
    """
    <style>

    /* ---------- Global ---------- */
    .block-container {
        max-width: 1380px;
        padding-top: 1.8rem;
        padding-bottom: 3rem;
        padding-left: 2.2rem;
        padding-right: 2.2rem;
    }

    [data-testid="stSidebar"] {
        border-right: 1px solid rgba(128, 128, 128, 0.16);
    }

    [data-testid="stSidebar"] > div:first-child {
        padding-top: 1.6rem;
    }

    /* ---------- Typography ---------- */
    h1 {
        font-size: 2.15rem !important;
        letter-spacing: -0.035em;
        margin-bottom: 0.2rem !important;
    }

    h2, h3 {
        letter-spacing: -0.025em;
    }

    .eyebrow {
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.11em;
        text-transform: uppercase;
        opacity: 0.58;
        margin-bottom: 0.25rem;
    }

    .muted {
        opacity: 0.62;
    }

    /* ---------- Brand ---------- */
    .brand-title {
        font-size: 1.15rem;
        font-weight: 800;
        letter-spacing: -0.025em;
        margin-bottom: 0.15rem;
    }

    .brand-caption {
        font-size: 0.78rem;
        opacity: 0.58;
        line-height: 1.45;
        margin-bottom: 1.35rem;
    }

    /* ---------- Cards ---------- */
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 0.85rem;
    }

    .metric-label {
        font-size: 0.74rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        opacity: 0.55;
        margin-bottom: 0.2rem;
    }

    .metric-note {
        font-size: 0.72rem;
        opacity: 0.50;
        margin-top: 0.25rem;
    }

    .status-title {
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.09em;
        opacity: 0.58;
        margin-bottom: 0.45rem;
    }

    .status-value {
        font-size: 1.65rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        margin-bottom: 0.1rem;
    }

    .recommendation-title {
        font-size: 0.76rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        opacity: 0.55;
        margin-bottom: 0.35rem;
    }

    .recommendation-action {
        font-size: 1.15rem;
        font-weight: 700;
        line-height: 1.45;
    }

    .section-note {
        font-size: 0.82rem;
        opacity: 0.58;
        margin-top: -0.45rem;
        margin-bottom: 0.9rem;
    }

    .sidebar-note {
        font-size: 0.72rem;
        opacity: 0.52;
        line-height: 1.5;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None


# ============================================================
# SIDEBAR — BRAND + INPUT
# ============================================================

with st.sidebar:

    st.markdown(
        '<div class="brand-title">📊 Business Analytics</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="brand-caption">Reusable business performance analysis, monitoring, and reporting.</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="eyebrow">Workflow</div>', unsafe_allow_html=True)
    st.markdown("**① Dataset**\n\n**② Analysis**\n\n**③ Recommendation**\n\n**④ Report**")

    st.divider()

    st.markdown('<div class="eyebrow">Data input</div>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Upload transaction data",
        type=["csv"],
        help="Upload a CSV file containing business transaction data.",
    )

    if uploaded_file is not None:
        file_signature = (
            uploaded_file.name,
            uploaded_file.size,
        )

        if st.session_state.get("dataset_signature") != file_signature:
            st.session_state.dataset_signature = file_signature
            st.session_state.analysis_result = None
            st.session_state.pop("start_date", None)
            st.session_state.pop("end_date", None)

    dataset_start = None
    dataset_end = None

    if uploaded_file is not None:
        st.caption(
            f"✓ {uploaded_file.name} · "
            f"{uploaded_file.size / 1024 / 1024:.2f} MB"
        )

        try:
            raw_df = pd.read_csv(uploaded_file)
            canonical_df, _ = map_schema(raw_df)

            parsed_dates = pd.to_datetime(
                canonical_df["date"],
                errors="coerce",
                format="mixed",
            )
            valid_dates = parsed_dates.dropna()

            if valid_dates.empty:
                st.error("No valid dates were found in the uploaded dataset.")
            else:
                dataset_start = valid_dates.min().date()
                dataset_end = valid_dates.max().date()

                st.caption(
                    f"Dataset range: {dataset_start} → {dataset_end}"
                )

        except Exception as exc:
            st.error(f"Could not inspect dataset dates: {exc}")

    st.divider()

    st.markdown('<div class="eyebrow">Analysis controls</div>', unsafe_allow_html=True)

    if dataset_start is not None:
        default_end = dataset_end
        default_start = max(
            dataset_start,
            dataset_end - timedelta(days=6),
        )
    else:
        default_start = date.today()
        default_end = date.today()

    if "start_date" not in st.session_state:
        st.session_state.start_date = default_start

    if "end_date" not in st.session_state:
        st.session_state.end_date = default_end

    start_date = st.date_input(
        "Start date",
        key="start_date",
    )

    end_date = st.date_input(
        "End date",
        key="end_date",
    )

    analyze = st.button(
        "Analyze Data",
        type="primary",
        use_container_width=True,
    )

    st.divider()

    st.markdown(
        '<div class="sidebar-note">Core analytics runs only when Analyze Data is clicked. Email delivery is handled separately from the UI.</div>',
        unsafe_allow_html=True,
    )


# ============================================================
# HEADER
# ============================================================

header_col, period_col = st.columns([2.9, 1.1])

with header_col:
    st.markdown('<div class="eyebrow">Business monitoring workspace</div>', unsafe_allow_html=True)
    st.title("Business Analytics Automation")
    st.caption(
        "Turn transactional data into monitored KPIs, diagnostics, recommendations, and business reports."
    )

with period_col:
    if dataset_start is not None:
        st.markdown('<div class="eyebrow">Current dataset</div>', unsafe_allow_html=True)
        st.markdown(f"**{dataset_start} → {dataset_end}**")
    else:
        st.markdown('<div class="eyebrow">Current dataset</div>', unsafe_allow_html=True)
        st.markdown("**No dataset loaded**")

st.divider()


# ============================================================
# RUN ANALYSIS
# ============================================================

if analyze:

    if uploaded_file is None:
        st.error("Please upload a CSV file first.")
        st.session_state.analysis_result = None

    elif start_date > end_date:
        st.error("Start date cannot be later than end date.")
        st.session_state.analysis_result = None

    else:

        temp_dir = PROJECT_ROOT / "data" / "uploads"
        temp_dir.mkdir(parents=True, exist_ok=True)

        temp_file = temp_dir / uploaded_file.name

        with open(temp_file, "wb") as file:
            file.write(uploaded_file.getbuffer())

        with st.spinner("Running business analytics..."):
            try:
                result = run_pipeline(
                    data_file=temp_file,
                    current_start=str(start_date),
                    current_end=str(end_date),
                )

                st.session_state.analysis_result = result

            except Exception as exc:
                st.error(f"Analysis failed: {exc}")
                st.session_state.analysis_result = None


# ============================================================
# GET STORED RESULT
# ============================================================

result = st.session_state.analysis_result


# ============================================================
# EMPTY STATE
# ============================================================

if result is None:
    with st.container(border=True):
        st.markdown("### Ready to analyze")
        st.write(
            "Upload a transaction CSV from the sidebar, choose an analysis period, "
            "then run the analysis."
        )

    st.caption(
        "Supported workflow: data validation → analytics → recommendation → report."
    )


# ============================================================
# RESULTS
# ============================================================

if result is not None:

    st.success("Analysis completed successfully.")

    # --------------------------------------------------------
    # BUSINESS STATUS
    # --------------------------------------------------------

    st.markdown('<div class="eyebrow">Business overview</div>', unsafe_allow_html=True)

    status_col, priority_col, focus_col = st.columns([1.65, 1, 1.35])

    business_condition = result["business_condition"]
    priority = result["priority"]
    primary_focus = result["primary_focus"]

    with status_col:
        with st.container(border=True):
            st.markdown('<div class="status-title">Business condition</div>', unsafe_allow_html=True)

            if priority == "HIGH":
                st.markdown('<div class="status-value">🔴 ' + business_condition + '</div>', unsafe_allow_html=True)
            elif priority == "MEDIUM":
                st.markdown('<div class="status-value">🟡 ' + business_condition + '</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="status-value">🟢 ' + business_condition + '</div>', unsafe_allow_html=True)

            st.caption("Overall business condition identified by the monitoring engine.")

    with priority_col:
        with st.container(border=True):
            st.markdown('<div class="status-title">Priority</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="status-value">{priority}</div>', unsafe_allow_html=True)
            st.caption("Decision-support priority level.")

    with focus_col:
        with st.container(border=True):
            st.markdown('<div class="status-title">Primary focus</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="status-value">{primary_focus}</div>', unsafe_allow_html=True)
            st.caption("Main business area selected for action.")

    # --------------------------------------------------------
    # RECOMMENDATION
    # --------------------------------------------------------

    st.markdown('<div class="eyebrow">Recommendation</div>', unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown(
            f'<div class="recommendation-title">{primary_focus}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="recommendation-action">{result["primary_action"]}</div>',
            unsafe_allow_html=True,
        )
        st.caption("Generated from the monitoring result and supporting analytics evidence.")

    # --------------------------------------------------------
    # KPI MOVEMENT
    # --------------------------------------------------------

    st.markdown('<div class="eyebrow">KPI movement</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-note">Change compared with the previous analysis period.</div>',
        unsafe_allow_html=True,
    )

    kpis = result["kpis"]

    kpi_items = [
        ("Revenue", kpis["revenue"]),
        ("Transactions", kpis["transactions"]),
        ("Quantity", kpis["quantity"]),
        ("AOV", kpis["aov"]),
    ]

    kpi_cols = st.columns(4)

    for col, (label, value) in zip(kpi_cols, kpi_items):
        with col:
            with st.container(border=True):
                st.markdown(
                    f'<div class="metric-label">{label}</div>',
                    unsafe_allow_html=True,
                )
                st.metric(
                    label="",
                    value=(f"{value:+.2%}" if value is not None else "N/A"),
                    label_visibility="collapsed",
                )
                st.markdown(
                    '<div class="metric-note">vs previous period</div>',
                    unsafe_allow_html=True,
                )

    # --------------------------------------------------------
    # DIAGNOSTICS
    # --------------------------------------------------------

    st.markdown('<div class="eyebrow">Diagnostics</div>', unsafe_allow_html=True)

    product = result["product_performance"]
    profitability = result["profitability"]

    diag_product, diag_profit = st.columns(2)

    with diag_product:
        with st.container(border=True):
            st.markdown("### Product Performance")

            if product["scope"] == "NOT_AVAILABLE":
                st.info(
                    "Product-level analysis is unavailable because product and quantity data were not provided."
                )
            else:
                left, right = st.columns(2)
                with left:
                    st.caption("SCOPE")
                    st.write(f"`{product['scope']}`")
                with right:
                    st.caption("MATERIAL DECLINE")
                    st.write(
                        f"{product['declining_products']} of "
                        f"{product['total_products_analyzed']}"
                    )

                st.caption("Product Movement")
                product_data = product["diagnosis"]

                if isinstance(product_data, list) and product_data:

                    product_rows = []

                    for item in product_data:

                        product_rows.append(
                            {
                                "Product": item["product"],
                                "Qty Change": (
                                    f"{item['quantity_change']:+.1%}"
                                ),
                                "Revenue Change": (
                                    f"{item['revenue_change']:+.1%}"
                                ),
                                "Revenue Impact": (
                                    f"Rp{item['revenue_change_abs']:,.0f}"
                                ),
                                "Revenue Contribution": (
                                    f"{item['revenue_contribution']:.1%}"
                                ),
                            }
                        )

                    st.dataframe(
                        product_rows,
                        use_container_width=True,
                        hide_index=True,
                    )

                else:

                    st.info(
                        "No product-level movement details are available."
                    )

    with diag_profit:
        with st.container(border=True):
            st.markdown("### Profitability")

            if profitability["diagnosis"] == "NOT_AVAILABLE":
                st.info(
                    "Profitability analysis is unavailable because cost or profit data were not provided."
                )
            else:
                top_left, top_right = st.columns(2)
                with top_left:
                    st.metric(
                        "Profit",
                        f"{profitability['profit_change']:+.2%}",
                    )
                with top_right:
                    st.metric(
                        "Margin",
                        f"{profitability['margin_change']:+.2%}",
                    )

                bottom_left, bottom_right = st.columns(2)
                with bottom_left:
                    st.metric(
                        "Cost / Unit",
                        f"{profitability['cost_per_unit_change']:+.2%}",
                    )
                with bottom_right:
                    st.metric(
                        "Revenue / Unit",
                        f"{profitability['revenue_per_unit_change']:+.2%}",
                    )

                st.caption("Diagnosis")
                st.write(profitability["diagnosis"])

    # --------------------------------------------------------
    # EVIDENCE & SUPPORT
    # --------------------------------------------------------

    evidence_col, findings_col = st.columns(2)

    with evidence_col:
        with st.container(border=True):
            st.markdown("### Why this recommendation?")
            evidence = result["recommendation_evidence"]

            if evidence:
                for item in evidence:
                    st.write(f"• {item}")
            else:
                st.info("No supporting evidence was available.")

    with findings_col:
        with st.container(border=True):
            st.markdown("### Supporting findings")
            findings = result["supporting_findings"]

            if findings:
                for finding in findings:
                    st.write(f"• {finding}")
            else:
                st.info("No additional supporting findings were identified.")

    # --------------------------------------------------------
    # SUPPORTING RECOMMENDATIONS
    # --------------------------------------------------------

    with st.container(border=True):
        st.markdown("### Supporting recommendations")
        supporting_recommendations = result["supporting_recommendations"]

        if supporting_recommendations:
            rec_cols = st.columns(min(3, len(supporting_recommendations)))

            for col, item in zip(rec_cols, supporting_recommendations):
                with col:
                    st.caption(item["focus"])
                    st.write(item["action"])
        else:
            st.info("No additional recommendations were generated.")

    # --------------------------------------------------------
    # REPORT & DELIVERY
    # --------------------------------------------------------

    st.markdown('<div class="eyebrow">Report & delivery</div>', unsafe_allow_html=True)

    report_path = Path(result["outputs"]["report"])

    if report_path.exists():
        with open(report_path, "rb") as report_file:
            report_data = report_file.read()

        recipient_email = st.text_input(
            "Recipient Email",
            placeholder="name@example.com",
            key="recipient_email",
        )

        download_col, email_col = st.columns(2)

        with download_col:
            st.download_button(
                label="Download Business Report",
                data=report_data,
                file_name="business_report.md",
                mime="text/markdown",
                use_container_width=True,
            )

        with email_col:
            if ENABLE_EMAIL:
                if st.button(
                    "Email Business Report",
                    use_container_width=True,
                ):
                    recipient_email = recipient_email.strip()

                    if not recipient_email:
                        st.warning("Please enter a recipient email address.")

                    elif not re.fullmatch(
                        r"[^@\s]+@[^@\s]+\.[^@\s]+",
                        recipient_email,
                    ):
                        st.warning("Please enter a valid email address.")

                    else:
                        try:
                            email_subject = (
                                f"Business Analytics Report — "
                                f"{result['analysis_period']['start']} "
                                f"to "
                                f"{result['analysis_period']['end']}"
                            )

                            email_body = (
                                "Business Analytics Automation\n\n"
                                f"Analysis Period: "
                                f"{result['analysis_period']['start']} "
                                f"to "
                                f"{result['analysis_period']['end']}\n"
                                f"Priority: {result['priority']}\n"
                                f"Primary Focus: {result['primary_focus']}\n"
                                f"Recommended Action: {result['primary_action']}\n\n"
                                "The generated business report is attached."
                            )

                            send_email(
                                subject=email_subject,
                                body=email_body,
                                recipient=recipient_email,
                                attachment_path=report_path,
                            )

                            st.success(
                                f"Report emailed to {recipient_email}"
                            )

                        except Exception as exc:
                            st.error(f"Email delivery failed: {exc}")
            else:
                st.button(
                    "Email Business Report",
                    disabled=True,
                    use_container_width=True,
                )
                st.caption("Email delivery is disabled.")

    else:
        st.warning("Business report file could not be found.")
