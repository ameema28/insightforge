"""
Enhanced InsightForge Data Tools

Adds product-level and region-level aggregation.
Compatible with Pylance strict type checking.
"""
import os
import re
import pandas as pd
from typing import Dict, Any, List, Tuple


def _validate_file_path(file_path: str) -> Tuple[bool, str]:
    """Security guardrail: Validate file path before processing."""
    if not file_path or not isinstance(file_path, str):
        return False, "Invalid file path provided."

    abs_path = os.path.abspath(file_path)

    if not os.path.exists(abs_path):
        return False, f"File not found: {file_path}"

    if not os.path.isfile(abs_path):
        return False, f"Path is not a file: {file_path}"

    allowed_extensions = (".csv", ".xlsx", ".xls")
    if not abs_path.lower().endswith(allowed_extensions):
        return False, (
            f"Invalid file type: {os.path.splitext(abs_path)[1]}. "
            f"Allowed: {', '.join(allowed_extensions)}"
        )

    return True, ""


def _redact_pii(text: str) -> str:
    """Security guardrail: Redact common PII patterns from text output."""
    text = re.sub(
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "[REDACTED-EMAIL]",
        text,
    )
    text = re.sub(
        r"(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}",
        "[REDACTED-PHONE]",
        text,
    )
    text = re.sub(
        r"\b[0-9]{3}-[0-9]{2}-[0-9]{4}\b",
        "[REDACTED-SSN]",
        text,
    )
    return text


def _robust_read(abs_path: str):
    """Read CSV/TSV/Excel with encoding + delimiter auto-detection.

    Falls back to plain pandas if the robust loader is unavailable, so this
    never makes an already-working path worse.
    """
    try:
        from agents.data_loader import load_dataframe
        df, _profile = load_dataframe(abs_path)
        return df
    except Exception:
        import pandas as _pd
        if abs_path.lower().endswith((".xlsx", ".xls")):
            return _pd.read_excel(abs_path)
        return _pd.read_csv(abs_path, sep=None, engine="python")


def _get_product_breakdown(df: pd.DataFrame) -> str:
    """Generate product-level revenue and units breakdown."""
    if 'Product' not in df.columns or 'Revenue' not in df.columns:
        return ""

    # Group by product and sum revenue
    grouped = df.groupby('Product', as_index=False).agg({'Revenue': 'sum'})
    # Sort by revenue descending using explicit boolean
    grouped = grouped.sort_values(by='Revenue', ascending=False)  # type: ignore

    lines: List[str] = ["\nPRODUCT-LEVEL BREAKDOWN", "-" * 30]

    for idx in range(len(grouped)):
        product_name = str(grouped.iloc[idx]['Product'])
        revenue = float(grouped.iloc[idx]['Revenue'])

        units_str = ""
        if 'Units' in df.columns:
            units_for_product = df[df['Product'] == product_name]['Units']
            if len(units_for_product) > 0:
                units_val = int(units_for_product.sum())
                units_str = f", {units_val} units"

        lines.append(f"  {product_name}: ${revenue:,.0f} revenue{units_str}")

    return "\n".join(lines)


def _get_region_breakdown(df: pd.DataFrame) -> str:
    """Generate region-level revenue and units breakdown."""
    if 'Region' not in df.columns or 'Revenue' not in df.columns:
        return ""

    grouped = df.groupby('Region', as_index=False).agg({'Revenue': 'sum'})
    grouped = grouped.sort_values(by='Revenue', ascending=False)  # type: ignore

    lines: List[str] = ["\nREGION-LEVEL BREAKDOWN", "-" * 30]

    for idx in range(len(grouped)):
        region_name = str(grouped.iloc[idx]['Region'])
        revenue = float(grouped.iloc[idx]['Revenue'])

        units_str = ""
        if 'Units' in df.columns:
            units_for_region = df[df['Region'] == region_name]['Units']
            if len(units_for_region) > 0:
                units_val = int(units_for_region.sum())
                units_str = f", {units_val} units"

        lines.append(f"  {region_name}: ${revenue:,.0f} revenue{units_str}")

    return "\n".join(lines)


def data_quality_report(file_path: str) -> str:
    """
    Robustly load a messy real-world CSV/TSV/Excel file and return a schema +
    data-quality report with a 0-100 quality score.

    Unlike analyze_csv (schema-specific), this works on ANY tabular file:
    it auto-detects encoding and delimiter, tolerates quoted/ragged rows,
    infers column types, and scores completeness/uniqueness/validity/consistency.

    Args:
        file_path: Path to a .csv, .tsv, .txt, .xlsx, or .xls file.

    Returns:
        A natural-language data-quality report, or SECURITY_ERROR / PROCESSING_ERROR.
    """
    is_valid, error_msg = _validate_file_path(file_path)
    if not is_valid:
        # data_quality_report also accepts .tsv/.txt, so re-check those extensions.
        if not (file_path.lower().endswith((".tsv", ".txt"))):
            return f"SECURITY_ERROR: {error_msg}"
    try:
        from agents.data_loader import load_dataframe, profile_to_text

        _df, profile = load_dataframe(file_path)
        return _redact_pii(profile_to_text(profile))
    except ValueError as e:
        return f"SECURITY_ERROR: {str(e)}"
    except Exception as e:
        return f"PROCESSING_ERROR: {str(e)}"


def analyze_csv(file_path: str) -> str:
    """
    Loads a CSV or Excel file and returns a structured summary.
    """
    is_valid, error_msg = _validate_file_path(file_path)
    if not is_valid:
        return f"SECURITY_ERROR: {error_msg}"

    try:
        abs_path = os.path.abspath(file_path)
        df = _robust_read(abs_path)

        row_count = len(df)
        column_names = list(df.columns)
        dtype_map = {str(col): str(dtype) for col, dtype in df.dtypes.items()}
        missing_counts = df.isnull().sum().to_dict()
        total_missing = int(sum(missing_counts.values()))

        numeric_df = df.select_dtypes(include=["number"])
        if not numeric_df.empty:
            desc = numeric_df.describe().to_dict()
            numeric_summary = "\n".join(
                f"  {col}: mean={stats.get('mean', 'N/A'):.2f}, "
                f"std={stats.get('std', 'N/A'):.2f}, "
                f"min={stats.get('min', 'N/A'):.2f}, "
                f"max={stats.get('max', 'N/A'):.2f}"
                for col, stats in desc.items()
            )
        else:
            numeric_summary = "No numeric columns detected."

        product_breakdown = _get_product_breakdown(df)
        region_breakdown = _get_region_breakdown(df)

        report = f"""DATA SCOUT REPORT
==================
File: {os.path.basename(abs_path)}
Rows: {row_count}
Columns: {len(column_names)}
Column Names: {', '.join(column_names)}
Data Types: {dtype_map}
Missing Values (Total): {total_missing}
Missing Breakdown: {missing_counts}

NUMERIC SUMMARY
---------------
{numeric_summary}
{product_breakdown}
{region_breakdown}

DATA QUALITY FLAGS
------------------
{"ALERT: Missing values detected in " + str([k for k,v in missing_counts.items() if v > 0]) if total_missing > 0 else "No missing values detected."}"""

        return _redact_pii(report.strip())

    except Exception as e:
        return f"PROCESSING_ERROR: {str(e)}"


def generate_chart(file_path: str, x_column: str, y_column: str, chart_type: str = "bar") -> str:
    """
    Generates a chart from a CSV/Excel file and returns it as a base64 PNG string.
    Aggregates data if x_column has duplicate values.
    """
    is_valid, error_msg = _validate_file_path(file_path)
    if not is_valid:
        return f"SECURITY_ERROR: {error_msg}"

    try:
        abs_path = os.path.abspath(file_path)
        df = _robust_read(abs_path)

        if x_column not in df.columns:
            return f"ERROR: Column '{x_column}' not found. Available: {list(df.columns)}"
        if y_column not in df.columns:
            return f"ERROR: Column '{y_column}' not found. Available: {list(df.columns)}"

        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import base64
        import io

        # AGGREGATE: If x has duplicates, sum the y values
        if df[x_column].duplicated().any():
            df = df.groupby(x_column, as_index=False)[y_column].sum()

        plt.figure(figsize=(10, 6))

        if chart_type == "bar":
            df.plot(x=x_column, y=y_column, kind="bar", ax=plt.gca(), legend=False)
        elif chart_type == "line":
            df.plot(x=x_column, y=y_column, kind="line", ax=plt.gca(), legend=False, marker='o')
        elif chart_type == "scatter":
            df.plot(x=x_column, y=y_column, kind="scatter", ax=plt.gca())
        else:
            return f"ERROR: Unsupported chart_type '{chart_type}'. Use: bar, line, scatter."

        plt.title(f"{y_column} by {x_column}")
        plt.xlabel(x_column)
        plt.ylabel(y_column)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode("utf-8")
        plt.close('all')

        return f"data:image/png;base64,{img_base64}"

    except Exception as e:
        return f"PROCESSING_ERROR: {str(e)}"