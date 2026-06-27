"""
InsightForge Data Tools (Self-Contained for ADK App)

These tools are copied here so the 'agents' folder is a self-contained ADK app.
The root-level 'tools/' folder is for shared use by other modules/tests.
"""
import os
import re
import pandas as pd


def _validate_file_path(file_path):
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


def _redact_pii(text):
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


def analyze_csv(file_path):
    """
    Loads a CSV or Excel file and returns a structured summary.

    Args:
        file_path: Absolute or relative path to the data file.

    Returns:
        A formatted string containing file metadata and summary statistics.
        Returns an error message if validation fails or processing errors occur.
    """
    is_valid, error_msg = _validate_file_path(file_path)
    if not is_valid:
        return f"SECURITY_ERROR: {error_msg}"

    try:
        abs_path = os.path.abspath(file_path)
        if abs_path.lower().endswith(".csv"):
            df = pd.read_csv(abs_path)
        else:
            df = pd.read_excel(abs_path)

        row_count = len(df)
        column_names = list(df.columns)
        dtype_map = {str(col): str(dtype) for col, dtype in df.dtypes.items()}
        missing_counts = df.isnull().sum().to_dict()
        total_missing = sum(missing_counts.values())

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
----------------
{numeric_summary}

DATA QUALITY FLAGS
-------------------
{"ALERT: Missing values detected in " + str([k for k,v in missing_counts.items() if v > 0]) if total_missing > 0 else "No missing values detected."}"""

        return _redact_pii(report.strip())

    except Exception as e:
        return f"PROCESSING_ERROR: {str(e)}"


def generate_chart(file_path, x_column, y_column, chart_type="bar"):
    """
    Generates a chart from a CSV/Excel file and returns it as a base64 PNG string.
    Aggregates data if x_column has duplicate values.
    """
    print(f"DEBUG generate_chart: file={file_path}, x={x_column}, y={y_column}, type={chart_type}")

    is_valid, error_msg = _validate_file_path(file_path)
    if not is_valid:
        print(f"DEBUG validation failed: {error_msg}")
        return f"SECURITY_ERROR: {error_msg}"

    try:
        abs_path = os.path.abspath(file_path)
        print(f"DEBUG abs_path={abs_path}")
        
        if abs_path.lower().endswith(".csv"):
            df = pd.read_csv(abs_path)
        else:
            df = pd.read_excel(abs_path)

        print(f"DEBUG columns={list(df.columns)}")

        if x_column not in df.columns:
            print(f"DEBUG x_column '{x_column}' not found")
            return f"ERROR: Column '{x_column}' not found. Available: {list(df.columns)}"
        if y_column not in df.columns:
            print(f"DEBUG y_column '{y_column}' not found")
            return f"ERROR: Column '{y_column}' not found. Available: {list(df.columns)}"

        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import base64
        import io

        # AGGREGATE: If x has duplicates, sum the y values
        if df[x_column].duplicated().any():
            print(f"DEBUG aggregating duplicates on {x_column}")
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
        plt.close('all')  # Prevent memory leak

        print(f"DEBUG chart generated successfully, base64 length={len(img_base64)}")
        return f"data:image/png;base64,{img_base64}"

    except Exception as e:
        print(f"DEBUG exception: {type(e).__name__}: {str(e)}")
        return f"PROCESSING_ERROR: {str(e)}"