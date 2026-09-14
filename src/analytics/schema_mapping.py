"""
Schema Mapping
--------------
Maps flexible business column names into the canonical
schema expected by the analytics engine.
"""

from __future__ import annotations

import re
from typing import Any

import pandas as pd


# ============================================================
# CONFIG
# ============================================================

REQUIRED_FIELDS = {
    "date",
    "revenue",
}

OPTIONAL_FIELDS = {
    "product",
    "quantity",
    "cost",
    "profit",
    "transaction_id",
    "unit_price",
    "discount",
    "category",
    "payment_method",
    "channel",
    "outlet",
}


COLUMN_ALIASES = {
    "date": [
        "date",
        "tanggal",
        "tanggal_transaksi",
        "transaction_date",
        "order_date",
    ],
    "revenue": [
        "revenue",
        "sales",
        "total_sales",
        "total_penjualan",
        "penjualan",
        "sales_total",
    ],
    "product": [
        "product",
        "product_name",
        "nama_produk",
        "nama_barang",
        "barang",
    ],
    "quantity": [
        "quantity",
        "qty",
        "jumlah",
        "jumlah_produk",
    ],
    "cost": [
        "cost",
        "cost_total",
        "total_cost",
        "modal",
        "biaya",
        "harga_modal",
    ],
    "profit": [
        "profit",
        "laba",
        "laba_bersih",
    ],
    "transaction_id": [
        "transaction_id",
        "trx_id",
        "id_transaksi",
        "order_id",
    ],
    "unit_price": [
        "unit_price",
        "harga_satuan",
        "price",
        "harga",
    ],
    "discount": [
        "discount",
        "diskon",
    ],
    "category": [
        "category",
        "kategori",
    ],
    "payment_method": [
        "payment_method",
        "metode_pembayaran",
        "payment",
    ],
    "channel": [
        "channel",
        "sales_channel",
        "kanal_penjualan",
    ],
    "outlet": [
        "outlet",
        "branch",
        "cabang",
    ],
}


# ============================================================
# HELPERS
# ============================================================

def normalize_column_name(column: str) -> str:
    """
    Normalize column names for matching.

    Example:
    'Total Penjualan' -> 'total_penjualan'
    'Tanggal Transaksi' -> 'tanggal_transaksi'
    """

    column = str(column).strip().lower()

    column = re.sub(
        r"[^a-z0-9]+",
        "_",
        column,
    )

    column = re.sub(
        r"_+",
        "_",
        column,
    ).strip("_")

    return column

# ============================================================
# CAPABILITY CHECK
# ============================================================

def has_capability(
    mapping_metadata: dict[str, Any],
    capability: str,
) -> bool:
    """
    Check whether a specific analytics capability
    is available for the mapped dataset.
    """

    return capability in mapping_metadata[
        "available_capabilities"
    ]

def validate_data_quality(
    df: pd.DataFrame,
) -> dict[str, Any]:
    """
    Validate data quality for required canonical fields.

    Returns:
        Dictionary containing validation status, errors, warnings,
        and per-field check details.
    """

    errors: list[str] = []
    warnings: list[str] = []

    checks: dict[str, Any] = {}

    # --------------------------------------------------------
    # DATE
    # --------------------------------------------------------

    date_series = df["date"]

    date_null_count = int(date_series.isna().sum())

    parsed_dates = pd.to_datetime(
        date_series,
        errors="coerce",
        format="mixed",
    )

    date_invalid_count = int(parsed_dates.isna().sum())

    if date_null_count == len(df):
        errors.append(
            "Date field contains no usable values."
        )

    elif date_invalid_count > 0:
        warnings.append(
            f"Date field contains "
            f"{date_invalid_count} invalid value(s)."
        )

    checks["date"] = {
        "status": (
            "ERROR"
            if date_null_count == len(df)
            else (
                "WARNING"
                if date_invalid_count > 0
                else "PASS"
            )
        ),
        "null_count": date_null_count,
        "invalid_count": date_invalid_count,
    }

    # --------------------------------------------------------
    # REVENUE
    # --------------------------------------------------------

    revenue_series = pd.to_numeric(
        df["revenue"],
        errors="coerce",
    )

    revenue_null_count = int(
        df["revenue"].isna().sum()
    )

    revenue_invalid_count = int(
        revenue_series.isna().sum()
    )

    negative_revenue_count = int(
        (revenue_series < 0).sum()
    )

    if revenue_invalid_count == len(df):
        errors.append(
            "Revenue field contains no usable numeric values."
        )

    elif revenue_invalid_count > 0:
        warnings.append(
            f"Revenue field contains "
            f"{revenue_invalid_count} non-numeric "
            f"value(s)."
        )

    if negative_revenue_count > 0:
        warnings.append(
            f"Revenue field contains "
            f"{negative_revenue_count} negative value(s)."
        )

    checks["revenue"] = {
        "status": (
            "ERROR"
            if revenue_invalid_count == len(df)
            else (
                "WARNING"
                if (
                    revenue_invalid_count > 0
                    or negative_revenue_count > 0
                )
                else "PASS"
            )
        ),
        "null_count": revenue_null_count,
        "invalid_count": revenue_invalid_count,
        "negative_count": negative_revenue_count,
    }

    # --------------------------------------------------------
    # OVERALL STATUS
    # --------------------------------------------------------

    if errors:
        status = "ERROR"
    elif warnings:
        status = "WARNING"
    else:
        status = "PASS"

    return {
        "status": status,
        "errors": errors,
        "warnings": warnings,
        "checks": checks,
    }

def prepare_data(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """
    Prepare canonical data for analytics.

    Safe preparation:
    - Standardize date values.
    - Convert revenue to numeric.
    - Exclude rows where required fields are invalid.
    - Retain negative revenue values and report them as warnings.

    Returns:
        prepared_df
        preparation_metadata
    """

    prepared_df = df.copy()

    rows_input = len(prepared_df)

    warnings: list[str] = []

    # --------------------------------------------------------
    # DATE STANDARDIZATION
    # --------------------------------------------------------

    prepared_df["date"] = pd.to_datetime(
        prepared_df["date"],
        errors="coerce",
        format="mixed",
    )

    # --------------------------------------------------------
    # REVENUE STANDARDIZATION
    # --------------------------------------------------------

    prepared_df["revenue"] = pd.to_numeric(
        prepared_df["revenue"],
        errors="coerce",
    )

    # --------------------------------------------------------
    # IDENTIFY INVALID REQUIRED ROWS
    # --------------------------------------------------------

    invalid_mask = (
        prepared_df["date"].isna()
        | prepared_df["revenue"].isna()
    )

    rows_excluded = int(invalid_mask.sum())

    if rows_excluded > 0:
        warnings.append(
            f"{rows_excluded} row(s) excluded "
            f"because required fields were invalid."
        )

    # --------------------------------------------------------
    # CONTROLLED EXCLUSION
    # --------------------------------------------------------

    prepared_df = prepared_df.loc[
        ~invalid_mask
    ].copy()

    # --------------------------------------------------------
    # NEGATIVE REVENUE WARNING
    # --------------------------------------------------------

    negative_revenue_count = int(
        (prepared_df["revenue"] < 0).sum()
    )

    if negative_revenue_count > 0:
        warnings.append(
            f"{negative_revenue_count} negative "
            f"revenue value(s) retained for analysis."
        )

    # --------------------------------------------------------
    # METADATA
    # --------------------------------------------------------

    rows_output = len(prepared_df)

    if rows_excluded == 0 and not warnings:
        status = "PASS"
    else:
        status = "WARNING"

    metadata = {
        "status": status,
        "rows_input": rows_input,
        "rows_output": rows_output,
        "rows_excluded": rows_excluded,
        "negative_revenue_count": negative_revenue_count,
        "warnings": warnings,
    }

    return prepared_df, metadata


# ============================================================
# FIND MAPPING
# ============================================================

def find_column_mapping(
    columns: list[str],
) -> dict[str, str]:
    """
    Match raw dataframe columns to canonical fields.
    """

    normalized_columns = {
        column: normalize_column_name(column)
        for column in columns
    }

    mapping: dict[str, str] = {}

    # Reverse alias lookup
    alias_lookup = {}

    for canonical_field, aliases in COLUMN_ALIASES.items():

        for alias in aliases:

            alias_lookup[
                normalize_column_name(alias)
            ] = canonical_field

    for original_column, normalized_column in normalized_columns.items():

        canonical_field = alias_lookup.get(
            normalized_column
        )

        if canonical_field is None:
            continue

        if canonical_field in mapping:
            raise ValueError(
                f"Multiple columns were mapped to "
                f"'{canonical_field}': "
                f"'{mapping[canonical_field]}' and "
                f"'{original_column}'"
            )

        mapping[canonical_field] = original_column

    return mapping


# ============================================================
# VALIDATE MAPPING
# ============================================================

def validate_mapping(
    mapping: dict[str, str],
) -> dict[str, Any]:
    """
    Validate required fields and identify missing optional fields.
    """

    missing_required = [
        field
        for field in REQUIRED_FIELDS
        if field not in mapping
    ]

    missing_optional = [
        field
        for field in OPTIONAL_FIELDS
        if field not in mapping
    ]

    if missing_required:

        raise ValueError(
            "Required fields could not be mapped: "
            f"{missing_required}"
        )

    available_fields = set(mapping.keys())

    capabilities = [
        "sales_monitoring",
        "period_comparison",
        "change_monitoring",
    ]

    if {
        "product",
        "quantity",
    }.issubset(available_fields):
        capabilities.append(
            "product_performance"
        )

    if (
        "cost" in available_fields
        or "profit" in available_fields
    ):
        capabilities.append(
            "profitability"
        )

    return {
        "missing_required": missing_required,
        "missing_optional": missing_optional,
        "available_capabilities": capabilities,
    }


# ============================================================
# APPLY MAPPING
# ============================================================

def apply_mapping(
    df: pd.DataFrame,
    mapping: dict[str, str],
) -> pd.DataFrame:
    """
    Rename raw dataframe columns to canonical names.
    """

    canonical_df = df.rename(
        columns={
            raw_column: canonical_field
            for canonical_field, raw_column
            in mapping.items()
        }
    ).copy()

    return canonical_df


# ============================================================
# MAIN MAPPER
# ============================================================

def map_schema(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:

    if df.empty:
        raise ValueError(
            "Input dataframe is empty."
        )

    mapping = find_column_mapping(
        list(df.columns)
    )

    validation = validate_mapping(
        mapping
    )

    canonical_df = apply_mapping(
        df,
        mapping,
    )

    data_quality = validate_data_quality(
        canonical_df
    )

    metadata = {
        "mapped_columns": mapping,
        **validation,
        "data_quality": data_quality,
    }

    return canonical_df, metadata


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    sample_df = pd.DataFrame(
        {
            "Tanggal Transaksi": [
                "2026-01-01",
                "2026-01-01",
            ],
            "Total Penjualan": [
                25000,
                30000,
            ],
            "Nama Barang": [
                "Nasi Goreng",
                "Es Teh",
            ],
            "Qty": [
                1,
                2,
            ],
            "Modal": [
                13000,
                4000,
            ],
        }
    )

    # ========================================================
    # INVALID DATA PREPARATION TEST
    # ========================================================

    invalid_sample_df = pd.DataFrame(
        {
            "Tanggal Transaksi": [
                "2026-01-01",
                "01/01/2026",
                "banana",
                "2026-01-04",
                "2026-01-05",
            ],
            "Total Penjualan": [
                25000,
                30000,
                20000,
                "abc",
                -5000,
            ],
        }
    )

    invalid_canonical_df, _ = map_schema(
        invalid_sample_df
    )

    prepared_invalid_df, invalid_preparation = prepare_data(
        invalid_canonical_df
    )

    print("\n" + "=" * 70)
    print("INVALID DATA PREPARATION TEST")
    print("=" * 70)

    print("\nPreparation Metadata:")
    print(invalid_preparation)

    print("\nPrepared Data:")
    print(prepared_invalid_df)

    print("\n" + "=" * 70)
    print("INVALID DATA PREPARATION TEST COMPLETED")
    print("=" * 70)

    canonical_df, metadata = map_schema(
        sample_df
    )

    prepared_df, preparation_metadata = prepare_data(
    canonical_df
    )

    print("\nData Preparation:")
    print(preparation_metadata)

    print("\nPrepared Data:")
    print(prepared_df)

    data_quality = validate_data_quality(
        canonical_df
    )

    print("\nData Quality Validation:")
    print(data_quality)

    print("=" * 70)
    print("SCHEMA MAPPING TEST")
    print("=" * 70)

    print("\nMapped Columns:")

    for canonical, original in metadata[
        "mapped_columns"
    ].items():
        print(
            f"- {original} -> {canonical}"
        )

    print("\nMissing Optional Fields:")
    print(
        metadata["missing_optional"]
    )

    print("\nAvailable Capabilities:")

    for capability in metadata[
        "available_capabilities"
    ]:
        print(
            f"- {capability}"
        )

    print("\nCanonical Data:")
    print(canonical_df)

    print("\n" + "=" * 70)
    print("SCHEMA MAPPING TEST PASSED")
    print("=" * 70)

    # ========================================================
    # ERROR DATA PREPARATION TEST
    # ========================================================

    error_sample_df = pd.DataFrame(
        {
            "Tanggal Transaksi": [
                "2026-01-01",
                "2026-01-02",
                "2026-01-03",
            ],
            "Total Penjualan": [
                "abc",
                "banana",
                "not-a-number",
            ],
        }
    )

    error_canonical_df, _ = map_schema(
        error_sample_df
    )

    error_quality = validate_data_quality(
        error_canonical_df
    )

    print("\n" + "=" * 70)
    print("ERROR DATA QUALITY TEST")
    print("=" * 70)

    print("\nData Quality:")
    print(error_quality)

    print("\n" + "=" * 70)
    print("ERROR DATA QUALITY TEST COMPLETED")
    print("=" * 70)