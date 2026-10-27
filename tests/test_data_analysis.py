import pandas as pd
import numpy as np
from functions.data_analysis import DataAnalysis


def test_null_report():
    df = pd.DataFrame({"a": [1, 2, None], "b": [None, "x", "y"]})
    rep = DataAnalysis.null_report(df)
    assert rep.iloc[0]["null_count"] == 1


def test_correlation():
    df = pd.DataFrame({"x": [1, 2, 3, 4], "y": [2, 4, 6, 8], "z": ["a", "b", "c", "d"]})
    corr = DataAnalysis.correlation(df)
    assert "x" in corr.columns and "y" in corr.columns
    assert "z" not in corr.columns
    assert abs(corr.loc["x", "y"] - 1.0) < 1e-9


def test_outliers_iqr():
    df = pd.DataFrame({"v": [1, 1, 1, 1, 100, 1, 1, 1]})
    out = DataAnalysis.outliers_iqr(df, "v")
    assert len(out) == 1
    assert out.iloc[0]["value"] == 100


def test_group_aggregate():
    df = pd.DataFrame({"g": ["a", "a", "b"], "v": [1, 2, 3]})
    s = DataAnalysis.group_aggregate(df, "g", "v", agg="sum")
    assert s.loc["a"] == 3
    assert s.loc["b"] == 3