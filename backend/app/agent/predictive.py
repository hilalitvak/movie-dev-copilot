# backend/app/agent/predictive.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any, List

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
PROCESSED = ROOT / "data" / "processed"
AGG_PATH = PROCESSED / "roi_aggregates.csv"


@dataclass(frozen=True)
class RoiBucketStats:
    bucket: str
    count: int
    median: float
    p25: float
    p75: float
    mean: float


_AGG_DF: Optional[pd.DataFrame] = None


def load_roi_aggregates() -> pd.DataFrame:
    global _AGG_DF
    if _AGG_DF is not None:
        return _AGG_DF

    if not AGG_PATH.exists():
        raise FileNotFoundError(f"Missing ROI aggregates file: {AGG_PATH}")

    df = pd.read_csv(AGG_PATH)
    # expected columns: budget_bucket, count, median, mean, p25, p75
    need = {"budget_bucket", "count", "median", "mean", "p25", "p75"}
    missing = need - set(df.columns)
    if missing:
        raise ValueError(f"roi_aggregates.csv missing columns: {sorted(missing)}")

    # types
    df["count"] = pd.to_numeric(df["count"], errors="coerce").fillna(0).astype(int)
    for c in ["median", "mean", "p25", "p75"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    _AGG_DF = df
    return _AGG_DF


def budget_to_bucket(budget: Optional[float]) -> str:
    if budget is None:
        return "unknown"
    try:
        b = float(budget)
    except Exception:
        return "unknown"
    if not np.isfinite(b) or b <= 0:
        return "unknown"
    if b < 5_000_000:
        return "0-5M"
    if b < 15_000_000:
        return "5-15M"
    if b < 40_000_000:
        return "15-40M"
    if b < 100_000_000:
        return "40-100M"
    return "100M+"


def get_bucket_stats(bucket: str) -> Optional[RoiBucketStats]:
    df = load_roi_aggregates()
    row = df[df["budget_bucket"] == bucket]
    if row.empty:
        return None
    r = row.iloc[0]
    # if numeric missing, return None
    if any(pd.isna(r[c]) for c in ["median", "mean", "p25", "p75"]):
        return None
    return RoiBucketStats(
        bucket=str(r["budget_bucket"]),
        count=int(r["count"]),
        median=float(r["median"]),
        mean=float(r["mean"]),
        p25=float(r["p25"]),
        p75=float(r["p75"]),
    )


def top_buckets_by_count(n: int = 3) -> List[RoiBucketStats]:
    df = load_roi_aggregates().copy()
    df = df[df["count"] > 0].sort_values("count", ascending=False).head(n)
    out: List[RoiBucketStats] = []
    for _, r in df.iterrows():
        if any(pd.isna(r[c]) for c in ["median", "mean", "p25", "p75"]):
            continue
        out.append(
            RoiBucketStats(
                bucket=str(r["budget_bucket"]),
                count=int(r["count"]),
                median=float(r["median"]),
                mean=float(r["mean"]),
                p25=float(r["p25"]),
                p75=float(r["p75"]),
            )
        )
    return out
