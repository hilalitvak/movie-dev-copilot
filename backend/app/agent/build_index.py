# backend/app/agent/build_index.py
# Rebuild a clean movies table + ROI aggregates from Kaggle "The Movies Dataset"

from __future__ import annotations
import ast
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


# ----------------------------
# Paths
# ----------------------------
ROOT = Path(__file__).resolve().parents[3]  # project root
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"
OUT.mkdir(parents=True, exist_ok=True)

MOVIES_CSV = RAW / "movies_metadata.csv"
CREDITS_CSV = RAW / "credits.csv"
KEYWORDS_CSV = RAW / "keywords.csv"

OUT_PARQUET = OUT / "movies_clean.parquet"
OUT_AGG = OUT / "roi_aggregates.csv"


# ----------------------------
# Reading / coercion
# ----------------------------
def read_csv_robust(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing: {path}")
    return pd.read_csv(
        path,
        low_memory=False,
        encoding="utf-8",
        encoding_errors="replace",
    )


def to_int_id(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce").astype("Int64")


def to_float(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce").astype(float)


# ----------------------------
# JSON-ish parsing helpers
# ----------------------------
def parse_jsonish(x: Any) -> Any:
    """
    Robust parser for Kaggle 'json-like' strings.
    Tries json.loads first; if it fails, falls back to ast.literal_eval.
    """
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return []
    if isinstance(x, (list, dict)):
        return x
    if not isinstance(x, str):
        return []
    s = x.strip()
    if not s or s.lower() == "nan":
        return []

    try:
        return json.loads(s)
    except Exception:
        pass

    try:
        return ast.literal_eval(s)
    except Exception:
        return []



def extract_name_list(list_obj: Any) -> List[str]:
    if not isinstance(list_obj, list):
        return []
    out: List[str] = []
    for it in list_obj:
        if isinstance(it, dict):
            name = it.get("name")
            if isinstance(name, str) and name.strip():
                out.append(name.strip())
    return out


def extract_crew_job(crew_str: Any, job: str) -> Optional[str]:
    crew = parse_jsonish(crew_str)
    if not isinstance(crew, list):
        return None
    for person in crew:
        if isinstance(person, dict) and person.get("job") == job:
            name = person.get("name")
            if isinstance(name, str) and name.strip():
                return name.strip()
    return None

def fix_mojibake(s: Any) -> Any:
    """
    Fix common UTF-8-as-Latin1 mojibake like: 'VÃkend' -> 'Víkend'.
    Only attempts fix when telltale characters appear.
    """
    if not isinstance(s, str):
        return s
    if not any(ch in s for ch in ("Ã", "Â", "Ð", "Ñ")):
        return s
    try:
        fixed = s.encode("latin1").decode("utf-8")
        return fixed
    except Exception:
        return s


# ----------------------------
# Budget buckets + ROI
# ----------------------------
def budget_bucket(b: float) -> str:
    # assumes b is float, can be nan
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


def main() -> None:
    print(f"[build_index] ROOT = {ROOT}")

    # ----------------------------
    # Load
    # ----------------------------
    print("[build_index] Loading CSVs...")
    movies = read_csv_robust(MOVIES_CSV)
    credits = read_csv_robust(CREDITS_CSV)
    keywords = read_csv_robust(KEYWORDS_CSV)

    # ----------------------------
    # Normalize IDs
    # ----------------------------
    print("[build_index] Normalizing IDs...")
    movies["tmdb_id"] = to_int_id(movies["id"])
    credits["tmdb_id"] = to_int_id(credits["id"])
    keywords["tmdb_id"] = to_int_id(keywords["id"])

    movies = movies.dropna(subset=["tmdb_id"]).copy()
    credits = credits.dropna(subset=["tmdb_id"]).copy()
    keywords = keywords.dropna(subset=["tmdb_id"]).copy()

    movies["tmdb_id"] = movies["tmdb_id"].astype(int)
    credits["tmdb_id"] = credits["tmdb_id"].astype(int)
    keywords["tmdb_id"] = keywords["tmdb_id"].astype(int)

    credits = credits.drop_duplicates(subset=["tmdb_id"])
    keywords = keywords.drop_duplicates(subset=["tmdb_id"])

    # ----------------------------
    # Clean numeric fields
    # ----------------------------
    print("[build_index] Cleaning numeric fields...")
    for col in ["budget", "revenue", "popularity", "vote_average", "vote_count", "runtime"]:
        if col in movies.columns:
            movies[col] = to_float(movies[col])

    # Some rows have bad runtime as string; handled by to_float -> NaN.
    # Replace NaNs with 0 for budget/revenue for consistent ROI logic (ROI will remain NaN if invalid)
    # Treat 0/NaN as "unknown"
    movies.loc[(~np.isfinite(movies["budget"])) | (movies["budget"] <= 0), "budget"] = np.nan
    movies.loc[(~np.isfinite(movies["revenue"])) | (movies["revenue"] <= 0), "revenue"] = np.nan


    # ----------------------------
    # Parse genres from movies_metadata
    # ----------------------------
    print("[build_index] Parsing genres...")
    movies["genres_parsed"] = movies["genres"].apply(parse_jsonish)
    movies["genres_list"] = movies["genres_parsed"].apply(extract_name_list)

    # ----------------------------
    # Parse keywords from keywords.csv
    # ----------------------------
    print("[build_index] Parsing keywords...")
    # keywords.csv has a column named "keywords" (stringified list)
    keywords_small = keywords[["tmdb_id", "keywords"]].copy()
    keywords_small["keywords_parsed"] = keywords_small["keywords"].apply(parse_jsonish)
    keywords_small["keywords_list"] = keywords_small["keywords_parsed"].apply(extract_name_list)
    keywords_small = keywords_small[["tmdb_id", "keywords_list"]]

    # ----------------------------
    # Credits: crew extraction (director/dop/editor)
    # ----------------------------
    print("[build_index] Extracting crew jobs...")
    credits_small = credits[["tmdb_id", "crew"]].copy()
    credits_small["director"] = credits_small["crew"].apply(lambda x: extract_crew_job(x, "Director"))
    credits_small["dop"] = credits_small["crew"].apply(lambda x: extract_crew_job(x, "Director of Photography"))
    credits_small["editor"] = credits_small["crew"].apply(lambda x: extract_crew_job(x, "Editor"))
    credits_small = credits_small[["tmdb_id", "director", "dop", "editor"]]
    # Fix mojibake in crew names
    for col in ["director", "dop", "editor"]:
        credits_small[col] = credits_small[col].apply(fix_mojibake)

    # ----------------------------
    # Merge (LEFT join from movies)
    # ----------------------------
    print("[build_index] Merging tables...")
    df = movies.merge(credits_small, on="tmdb_id", how="left")
    df = df.merge(keywords_small, on="tmdb_id", how="left")

    # Ensure list columns are proper python lists (not ndarray)
    df["genres_list"] = df["genres_list"].apply(lambda x: x.tolist() if isinstance(x, np.ndarray) else (x if isinstance(x, list) else []))
    df["keywords_list"] = df["keywords_list"].apply(lambda x: x.tolist() if isinstance(x, np.ndarray) else (x if isinstance(x, list) else []))

    # Fill missing lists
    df["keywords_list"] = df["keywords_list"].apply(lambda x: x if isinstance(x, list) else [])

    # ----------------------------
    # ROI + buckets
    # ----------------------------
    print("[build_index] Computing ROI + budget buckets...")
    # ROI defined only if budget > 0 and revenue > 0
    df["roi"] = np.where((df["budget"] > 0) & (df["revenue"] > 0), df["revenue"] / df["budget"], np.nan)
    df["budget_bucket"] = df["budget"].apply(budget_bucket)

    # Fix mojibake in movie title fields (if present)
    for col in ["title", "original_title"]:
        if col in movies.columns:
            movies[col] = movies[col].apply(fix_mojibake)

    # ----------------------------
    # doc_text for retrieval
    # ----------------------------
    print("[build_index] Building doc_text...")
    def make_doc_text(row: pd.Series) -> str:
        parts: List[str] = []
        title = row.get("title")
        overview = row.get("overview")
        if isinstance(title, str) and title.strip():
            parts.append(title.strip())
        if isinstance(overview, str) and overview.strip():
            parts.append(overview.strip())

        gl = row.get("genres_list")
        if isinstance(gl, list) and gl:
            parts.append(" ".join([g for g in gl if isinstance(g, str)]))

        kl = row.get("keywords_list")
        if isinstance(kl, list) and kl:
            parts.append(" ".join([k for k in kl if isinstance(k, str)]))

        for crew_field in ["director", "dop", "editor"]:
            v = row.get(crew_field)
            if isinstance(v, str) and v.strip():
                parts.append(v.strip())

        return " ".join(parts)

    df["doc_text"] = df.apply(make_doc_text, axis=1)

    # ----------------------------
    # Minimal cleaning: drop rows with empty title
    # ----------------------------
    print("[build_index] Final cleanup...")
    df = df[df["title"].notna()].copy()
    df["title"] = df["title"].astype(str)

    # ----------------------------
    # Save parquet (pyarrow)
    # ----------------------------
    print(f"[build_index] Saving parquet -> {OUT_PARQUET}")
    df.to_parquet(OUT_PARQUET, index=False, engine="pyarrow")

    # ----------------------------
    # Save ROI aggregates
    # ----------------------------
    print(f"[build_index] Saving ROI aggregates -> {OUT_AGG}")
    agg = (
        df.dropna(subset=["roi"])
        .groupby("budget_bucket")["roi"]
        .agg(count="count", median="median", mean="mean", p25=lambda s: float(s.quantile(0.25)), p75=lambda s: float(s.quantile(0.75)))
        .reset_index()
        .sort_values("budget_bucket")
    )
    agg.to_csv(OUT_AGG, index=False)

    # ----------------------------
    # Quick report
    # ----------------------------
    director_ratio = float(df["director"].notna().mean())
    dop_ratio = float(df["dop"].notna().mean())
    editor_ratio = float(df["editor"].notna().mean())
    roi_ratio = float(df["roi"].notna().mean())

    budget_ratio = float(df["budget"].notna().mean())
    revenue_ratio = float(df["revenue"].notna().mean())

    print("[build_index] DONE")
    print(f"  rows={len(df):,} cols={len(df.columns)}")
    print(f"  director_non_null_ratio={director_ratio:.3f}")
    print(f"  dop_non_null_ratio={dop_ratio:.3f}")
    print(f"  editor_non_null_ratio={editor_ratio:.3f}")
    print(f"  budget_non_null_ratio={budget_ratio:.3f}")
    print(f"  revenue_non_null_ratio={revenue_ratio:.3f}")
    print(f"  roi_non_null_ratio={roi_ratio:.3f}")


if __name__ == "__main__":
    main()
