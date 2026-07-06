"""
InsightForge Robust Data Loader
================================

Turns messy, real-world tabular files into a clean DataFrame + a rich profile,
without assuming any particular schema. Designed for the "real CSV" case:
unknown encodings, non-comma delimiters, quoted fields with embedded newlines,
mixed types, missing data, duplicates, and multi-sheet Excel workbooks.

Dependencies are limited to what InsightForge already ships:
pandas, charset-normalizer (encoding detection), openpyxl (xlsx). No new deps.

Public API:
    load_dataframe(path, sheet=None, sample_rows=None) -> (DataFrame, dict profile)
    profile_dataframe(df) -> dict
    profile_to_text(profile) -> str   # natural-language report for the Data Scout
"""

from __future__ import annotations

import csv
import os
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

# Files larger than this are read in chunks and profiled on a capped sample so
# the demo stays responsive on multi-hundred-MB inputs.
LARGE_FILE_BYTES = 100 * 1024 * 1024  # 100 MB
CHUNK_ROWS = 100_000
MAX_PROFILE_ROWS = 250_000  # cap rows used for profiling on very large files


# --------------------------------------------------------------------------- #
# Encoding + dialect detection
# --------------------------------------------------------------------------- #
def detect_encoding(path: str, n_bytes: int = 65536) -> str:
    """Best-effort encoding detection. Falls back to utf-8 then latin-1."""
    try:
        with open(path, "rb") as fh:
            raw = fh.read(n_bytes)
    except OSError:
        return "utf-8"
    if not raw:
        return "utf-8"
    # Prefer charset-normalizer (already in requirements); degrade gracefully.
    try:
        from charset_normalizer import from_bytes

        best = from_bytes(raw).best()
        if best and best.encoding:
            return best.encoding
    except Exception:
        pass
    # UTF-8 BOM
    if raw.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig"
    try:
        raw.decode("utf-8")
        return "utf-8"
    except UnicodeDecodeError:
        return "latin-1"


def detect_delimiter(path: str, encoding: str) -> str:
    """Sniff the delimiter from a text sample; default to comma."""
    try:
        with open(path, "r", encoding=encoding, errors="replace") as fh:
            sample = fh.read(16384)
    except OSError:
        return ","
    if not sample:
        return ","
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        return dialect.delimiter
    except csv.Error:
        # Fallback: pick the most common candidate on the first non-empty line.
        first = next((ln for ln in sample.splitlines() if ln.strip()), "")
        counts = {d: first.count(d) for d in [",", ";", "\t", "|"]}
        best = max(counts, key=lambda d: counts[d])
        return best if counts[best] > 0 else ","


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #
def _coerce_types(df: pd.DataFrame) -> pd.DataFrame:
    """Attempt lightweight, safe type inference on object columns."""
    for col in df.columns:
        # pandas <3 uses 'object' for text; pandas 3.x may use the new 'str' dtype.
        is_texty = df[col].dtype == object or str(df[col].dtype) in ("str", "string")
        if not is_texty:
            continue
        s = df[col]
        # Try numeric
        num = pd.to_numeric(s, errors="coerce")
        if num.notna().sum() >= max(1, int(0.9 * s.notna().sum())) and s.notna().any():
            df[col] = num
            continue
        # Try datetime (only if it looks date-ish to avoid false positives)
        sample = s.dropna().astype(str).head(20)
        if len(sample) and sample.str.contains(r"[-/:]").mean() > 0.5:
            dt = pd.to_datetime(s, errors="coerce")
            if dt.notna().sum() >= max(1, int(0.9 * s.notna().sum())):
                df[col] = dt
    return df


def load_dataframe(
    path: str,
    sheet: Optional[str] = None,
    sample_rows: Optional[int] = None,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Load a CSV/TSV/Excel file robustly and return (DataFrame, profile).

    Raises ValueError on unsupported types or unreadable files so callers can
    surface a clean message instead of a raw traceback.
    """
    if not path or not os.path.isfile(path):
        raise ValueError(f"File not found: {path}")

    ext = os.path.splitext(path)[1].lower()
    size = os.path.getsize(path)
    meta: Dict[str, Any] = {"file": os.path.basename(path), "bytes": size, "sheet": sheet}

    if ext in (".xlsx", ".xls"):
        xls = pd.ExcelFile(path)
        meta["sheets_available"] = list(xls.sheet_names)
        target = sheet or xls.sheet_names[0]
        meta["sheet"] = target
        df = xls.parse(target, nrows=sample_rows)
        meta["encoding"] = "n/a (excel)"
        meta["delimiter"] = "n/a (excel)"
    elif ext in (".csv", ".tsv", ".txt"):
        enc = detect_encoding(path)
        delim = "\t" if ext == ".tsv" else detect_delimiter(path, enc)
        meta["encoding"] = enc
        meta["delimiter"] = repr(delim)
        read_kwargs: Dict[str, Any] = dict(
            encoding=enc,
            sep=delim,
            engine="python",          # tolerant of ragged/quoted rows
            on_bad_lines="skip",
            skipinitialspace=True,
        )
        if size > LARGE_FILE_BYTES and sample_rows is None:
            # Chunked read, capped for profiling responsiveness.
            frames: List[pd.DataFrame] = []
            rows = 0
            for chunk in pd.read_csv(path, chunksize=CHUNK_ROWS, **read_kwargs):
                frames.append(chunk)
                rows += len(chunk)
                if rows >= MAX_PROFILE_ROWS:
                    meta["sampled"] = True
                    break
            df = pd.concat(frames, ignore_index=True)
        else:
            df = pd.read_csv(path, nrows=sample_rows, **read_kwargs)
    else:
        raise ValueError(f"Unsupported file type: {ext}. Allowed: .csv .tsv .txt .xlsx .xls")

    # Normalise column names (strip whitespace) and coerce obvious types.
    df.columns = [str(c).strip() for c in df.columns]
    df = _coerce_types(df)

    profile = profile_dataframe(df)
    profile["source"] = meta
    return df, profile


# --------------------------------------------------------------------------- #
# Profiling + data-quality score
# --------------------------------------------------------------------------- #
def profile_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
    """Compute a schema + data-quality profile with a 0-100 score."""
    n_rows = int(len(df))
    n_cols = int(df.shape[1])
    total_cells = max(1, n_rows * n_cols)

    columns: List[Dict[str, Any]] = []
    total_missing = 0
    for col in df.columns:
        s = df[col]
        missing = int(s.isna().sum())
        total_missing += missing
        nunique = int(s.nunique(dropna=True))
        col_info = {
            "name": str(col),
            "dtype": str(s.dtype),
            "missing": missing,
            "missing_pct": round(100 * missing / max(1, n_rows), 2),
            "unique": nunique,
            "unique_pct": round(100 * nunique / max(1, n_rows), 2),
        }
        # A small, safe sample of non-null values for context.
        sample_vals = s.dropna().astype(str).head(3).tolist()
        col_info["sample"] = sample_vals
        columns.append(col_info)

    dup_rows = int(df.duplicated().sum())

    # --- Data-quality dimensions (each 0-1) ------------------------------- #
    completeness = 1 - (total_missing / total_cells)
    # Uniqueness: penalise fully-duplicated rows.
    uniqueness = 1 - (dup_rows / max(1, n_rows))
    # Validity: fraction of columns that inferred to a concrete (non-object) type.
    typed_cols = sum(1 for c in columns if c["dtype"] != "object")
    validity = typed_cols / max(1, n_cols)
    # Consistency: penalise "junk" columns (all-null or single-value constant).
    junk_cols = sum(
        1
        for c in columns
        if c["missing_pct"] == 100.0 or (n_rows > 1 and c["unique"] <= 1)
    )
    consistency = 1 - (junk_cols / max(1, n_cols))

    dims = {
        "completeness": round(completeness, 4),
        "uniqueness": round(uniqueness, 4),
        "validity": round(validity, 4),
        "consistency": round(consistency, 4),
    }
    # Weighted overall score (completeness matters most).
    score = (
        0.40 * completeness
        + 0.25 * uniqueness
        + 0.20 * consistency
        + 0.15 * validity
    )
    quality_score = round(100 * score, 1)

    if quality_score >= 90:
        grade = "A (excellent)"
    elif quality_score >= 75:
        grade = "B (good)"
    elif quality_score >= 60:
        grade = "C (usable, review flags)"
    else:
        grade = "D (needs cleaning)"

    # Human-readable flags.
    flags: List[str] = []
    if total_missing:
        worst = max(columns, key=lambda c: c["missing_pct"])
        flags.append(
            f"{total_missing} missing cells; worst column "
            f"'{worst['name']}' ({worst['missing_pct']}% missing)"
        )
    if dup_rows:
        flags.append(f"{dup_rows} duplicate row(s)")
    const_cols = [c["name"] for c in columns if n_rows > 1 and c["unique"] <= 1]
    if const_cols:
        flags.append(f"constant/near-empty column(s): {', '.join(const_cols)}")
    if not flags:
        flags.append("no major data-quality issues detected")

    return {
        "rows": n_rows,
        "cols": n_cols,
        "columns": columns,
        "duplicate_rows": dup_rows,
        "total_missing": total_missing,
        "dimensions": dims,
        "quality_score": quality_score,
        "quality_grade": grade,
        "flags": flags,
    }


def profile_to_text(profile: Dict[str, Any]) -> str:
    """Render a profile as a compact natural-language report for an agent."""
    src = profile.get("source", {})
    lines: List[str] = []
    lines.append("DATA SCOUT REPORT (robust loader)")
    lines.append("================================")
    if src:
        lines.append(f"File: {src.get('file', 'n/a')}")
        if src.get("sheet") and src["sheet"] != "n/a (excel)":
            lines.append(f"Sheet: {src['sheet']}")
        lines.append(
            f"Encoding: {src.get('encoding', 'n/a')} | "
            f"Delimiter: {src.get('delimiter', 'n/a')} | "
            f"Size: {src.get('bytes', 0):,} bytes"
            + ("  [SAMPLED]" if src.get("sampled") else "")
        )
    lines.append(f"Rows: {profile['rows']:,} | Columns: {profile['cols']}")
    lines.append("")
    lines.append(f"DATA QUALITY SCORE: {profile['quality_score']}/100  —  {profile['quality_grade']}")
    d = profile["dimensions"]
    lines.append(
        f"  completeness={d['completeness']:.0%}  "
        f"uniqueness={d['uniqueness']:.0%}  "
        f"validity={d['validity']:.0%}  "
        f"consistency={d['consistency']:.0%}"
    )
    lines.append("")
    lines.append("SCHEMA")
    lines.append("------")
    for c in profile["columns"]:
        sample = ", ".join(c["sample"]) if c["sample"] else "—"
        lines.append(
            f"  {c['name']} :: {c['dtype']} | "
            f"missing {c['missing_pct']}% | unique {c['unique']} | e.g. {sample}"
        )
    lines.append("")
    lines.append("FLAGS")
    lines.append("-----")
    for f in profile["flags"]:
        lines.append(f"  - {f}")
    return "\n".join(lines)
