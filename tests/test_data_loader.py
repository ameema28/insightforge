"""
Tests for the robust real-world DataLoader.

Covers: encoding detection, delimiter sniffing, messy/missing/duplicate data,
type inference, the 0-100 quality score, Excel multi-sheet, and the
natural-language report. These run without ADK/network, so they're fast.
"""

import os
import tempfile

import pandas as pd
import pytest

from agents.data_loader import (
    detect_delimiter,
    detect_encoding,
    load_dataframe,
    profile_dataframe,
    profile_to_text,
)


def _write(tmp_path, name, content, encoding="utf-8"):
    p = os.path.join(tmp_path, name)
    with open(p, "w", encoding=encoding, newline="") as fh:
        fh.write(content)
    return p


class TestEncodingAndDelimiter:
    def test_detect_utf8(self, tmp_path):
        p = _write(tmp_path, "a.csv", "col\nvalue\n")
        assert "utf" in detect_encoding(p).lower() or detect_encoding(p) == "ascii"

    def test_detect_latin1(self, tmp_path):
        p = _write(tmp_path, "b.csv", "name\nJosé\nMüller\n", encoding="latin-1")
        enc = detect_encoding(p)
        assert enc  # some non-empty encoding returned
        df, _ = load_dataframe(p)
        assert len(df) == 2  # decoded without crashing

    def test_semicolon_delimiter(self, tmp_path):
        p = _write(tmp_path, "c.csv", "a;b;c\n1;2;3\n4;5;6\n")
        assert detect_delimiter(p, "utf-8") == ";"
        df, prof = load_dataframe(p)
        assert prof["cols"] == 3

    def test_tab_delimiter(self, tmp_path):
        p = _write(tmp_path, "d.tsv", "a\tb\n1\t2\n3\t4\n")
        df, prof = load_dataframe(p)
        assert prof["cols"] == 2 and prof["rows"] == 2

    def test_pipe_delimiter(self, tmp_path):
        p = _write(tmp_path, "e.csv", "a|b|c\nx|y|z\n")
        df, prof = load_dataframe(p)
        assert prof["cols"] == 3


class TestMessyData:
    def test_quoted_embedded_newline(self, tmp_path):
        content = 'id,note\n1,"line one\nline two"\n2,"ok"\n'
        p = _write(tmp_path, "q.csv", content)
        df, prof = load_dataframe(p)
        assert prof["rows"] == 2

    def test_ragged_rows_are_skipped_not_fatal(self, tmp_path):
        content = "a,b,c\n1,2,3\nBADROW\n4,5,6\n"
        p = _write(tmp_path, "r.csv", content)
        df, prof = load_dataframe(p)
        assert prof["rows"] >= 2  # good rows survive

    def test_missing_values_counted(self, tmp_path):
        content = "a,b\n1,\n,2\n3,3\n"
        p = _write(tmp_path, "m.csv", content)
        df, prof = load_dataframe(p)
        assert prof["total_missing"] == 2

    def test_duplicate_rows_detected(self, tmp_path):
        content = "a,b\n1,2\n1,2\n1,2\n9,9\n"
        p = _write(tmp_path, "dup.csv", content)
        df, prof = load_dataframe(p)
        assert prof["duplicate_rows"] == 2

    def test_whitespace_stripped_from_headers(self, tmp_path):
        content = " a , b \n1,2\n"
        p = _write(tmp_path, "ws.csv", content)
        df, prof = load_dataframe(p)
        assert "a" in df.columns and "b" in df.columns


class TestTypeInference:
    def test_numeric_inference(self, tmp_path):
        content = "x,y\n1,a\n2,b\n3,c\n"
        p = _write(tmp_path, "t.csv", content)
        df, _ = load_dataframe(p)
        assert pd.api.types.is_numeric_dtype(df["x"])

    def test_datetime_inference(self, tmp_path):
        content = "d,v\n2026-01-01,1\n2026-01-02,2\n2026-01-03,3\n"
        p = _write(tmp_path, "dt.csv", content)
        df, _ = load_dataframe(p)
        assert pd.api.types.is_datetime64_any_dtype(df["d"])


class TestQualityScore:
    def test_clean_data_scores_high(self):
        df = pd.DataFrame({"a": [1, 2, 3, 4], "b": ["w", "x", "y", "z"]})
        prof = profile_dataframe(df)
        assert prof["quality_score"] >= 75

    def test_messy_data_scores_lower(self):
        df = pd.DataFrame(
            {"a": [1, None, None, None], "b": [None, None, None, None]}
        )
        prof = profile_dataframe(df)
        assert prof["quality_score"] < 75
        assert prof["dimensions"]["completeness"] < 0.6

    def test_score_bounded_0_100(self):
        df = pd.DataFrame({"a": [1, 2, 3]})
        prof = profile_dataframe(df)
        assert 0 <= prof["quality_score"] <= 100

    def test_constant_column_flagged(self):
        df = pd.DataFrame({"const": [1, 1, 1, 1], "real": [1, 2, 3, 4]})
        prof = profile_dataframe(df)
        assert any("constant" in f.lower() for f in prof["flags"])


class TestExcel:
    def test_multi_sheet_excel(self, tmp_path):
        p = os.path.join(tmp_path, "wb.xlsx")
        with pd.ExcelWriter(p) as writer:
            pd.DataFrame({"a": [1, 2]}).to_excel(writer, sheet_name="First", index=False)
            pd.DataFrame({"b": [3, 4, 5]}).to_excel(writer, sheet_name="Second", index=False)
        df1, prof1 = load_dataframe(p)
        assert prof1["source"]["sheets_available"] == ["First", "Second"]
        assert prof1["rows"] == 2
        df2, prof2 = load_dataframe(p, sheet="Second")
        assert prof2["rows"] == 3


class TestReportAndErrors:
    def test_profile_to_text_contains_score(self):
        df = pd.DataFrame({"a": [1, 2, 3]})
        prof = profile_dataframe(df)
        prof["source"] = {"file": "x.csv", "encoding": "utf-8", "delimiter": "','", "bytes": 10}
        text = profile_to_text(prof)
        assert "DATA QUALITY SCORE" in text and "SCHEMA" in text

    def test_missing_file_raises_value_error(self):
        with pytest.raises(ValueError):
            load_dataframe("/nonexistent/path/nope.csv")

    def test_unsupported_type_raises(self, tmp_path):
        p = _write(tmp_path, "bad.json", "{}")
        with pytest.raises(ValueError):
            load_dataframe(p)