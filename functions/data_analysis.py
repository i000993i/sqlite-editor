"""
Аналитика на pandas/NumPy: описательная статистика, пропуски,
корреляции, выбросы, группировки, сводный отчёт.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Optional


class DataAnalysis:

    # ---------------- источники ----------------

    @staticmethod
    def from_query(connection, query: str, limit: int = 100_000) -> pd.DataFrame:
        if connection is None:
            return pd.DataFrame()
        try:
            df = pd.read_sql_query(query, connection)
            if limit and len(df) > limit:
                df = df.head(limit)
            return df
        except Exception:
            return pd.DataFrame()

    @staticmethod
    def from_table(connection, table_name: str, limit: int = 100_000) -> pd.DataFrame:
        if not table_name:
            return pd.DataFrame()
        safe = f'"{table_name}"'
        return DataAnalysis.from_query(
            connection, f"SELECT * FROM {safe} LIMIT {int(limit)}", limit=limit,
        )

    # ---------------- описательная статистика ----------------

    @staticmethod
    def describe(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        return df.describe(include="all").transpose()

    @staticmethod
    def null_report(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame(columns=["column", "null_count", "null_pct", "dtype"])
        total = len(df)
        rep = pd.DataFrame({
            "column": df.columns,
            "null_count": df.isna().sum().values,
            "dtype": df.dtypes.astype(str).values,
        })
        rep["null_pct"] = (rep["null_count"] / total * 100).round(2)
        return rep.sort_values("null_count", ascending=False).reset_index(drop=True)

    @staticmethod
    def detect_column_types(df: pd.DataFrame) -> dict[str, str]:
        out = {}
        for col in df.columns:
            s = df[col]
            if pd.api.types.is_bool_dtype(s):
                out[col] = "boolean"
            elif pd.api.types.is_numeric_dtype(s):
                out[col] = "numeric"
            elif pd.api.types.is_datetime64_any_dtype(s):
                out[col] = "datetime"
            else:
                out[col] = "categorical"
        return out

    # ---------------- корреляция ----------------

    @staticmethod
    def correlation(df: pd.DataFrame, method: str = "pearson") -> pd.DataFrame:
        numeric = df.select_dtypes(include=[np.number])
        if numeric.shape[1] < 2:
            return pd.DataFrame()
        return numeric.corr(method=method)

    # ---------------- выбросы ----------------

    @staticmethod
    def outliers_iqr(df: pd.DataFrame, column: str) -> pd.DataFrame:
        if column not in df.columns:
            return pd.DataFrame()
        s = pd.to_numeric(df[column], errors="coerce").dropna()
        if s.empty:
            return pd.DataFrame()
        q1, q3 = s.quantile([0.25, 0.75])
        iqr = q3 - q1
        lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        mask = (s < lo) | (s > hi)
        return pd.DataFrame({
            "value": s[mask].values,
            "lower_bound": lo,
            "upper_bound": hi,
        })

    # ---------------- группировки ----------------

    @staticmethod
    def group_aggregate(df: pd.DataFrame, group_col: str,
                        value_col: Optional[str] = None,
                        agg: str = "mean",
                        top: int = 50) -> pd.Series:
        if group_col not in df.columns:
            return pd.Series(dtype=float)
        if value_col and value_col in df.columns and \
                pd.api.types.is_numeric_dtype(df[value_col]):
            res = df.groupby(group_col, dropna=False)[value_col].agg(agg)
        else:
            res = df[group_col].value_counts(dropna=False)
        return res.sort_values(ascending=False).head(top)

    # ---------------- сводный отчёт ----------------

    @staticmethod
    def full_report(df: pd.DataFrame) -> dict:
        if df.empty:
            return {"rows": 0, "columns": 0}
        corr = DataAnalysis.correlation(df)
        return {
            "rows": int(len(df)),
            "columns": int(df.shape[1]),
            "dtypes": DataAnalysis.detect_column_types(df),
            "null_report": DataAnalysis.null_report(df).to_dict(orient="records"),
            "numeric_describe": df.describe().to_dict()
                                 if not df.select_dtypes("number").empty else {},
            "correlation": corr.round(3).to_dict() if not corr.empty else {},
        }