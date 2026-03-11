# backend/app/agent/retrieval.py
from __future__ import annotations
import os
import numpy as np
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


ROOT = Path(__file__).resolve().parents[3]
PARQUET_PATH = ROOT / "data" / "processed" / "movies_clean.parquet"

_df = None
_doc = None
_vectorizer = None
_matrix = None

ENABLE_LOCAL_RETRIEVAL = os.getenv("ENABLE_LOCAL_RETRIEVAL", "false").lower() == "true"

if ENABLE_LOCAL_RETRIEVAL and PARQUET_PATH.exists():
    try:
        _df = pd.read_parquet(PARQUET_PATH)
        _doc = _df["doc_text"].fillna("").astype(str)

        _vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=60000,
            ngram_range=(1, 2),
            min_df=2,
        )
        _matrix = _vectorizer.fit_transform(_doc)
    except Exception:
        _df = None
        _doc = None
        _vectorizer = None
        _matrix = None

def fix_mojibake(s):
    if not isinstance(s, str):
        return s
    if not any(ch in s for ch in ("Ã", "Â", "Ð", "Ñ")):
        return s
    try:
        return s.encode("latin1").decode("utf-8")
    except Exception:
        return s

def expand_query(query: str) -> str:
    q = query.lower()

    extras = []

    if "repeat" in q or "repeating" in q or "same night" in q or "time loop" in q:
        extras.extend([
            "time loop",
            "repeating day",
            "repeating night",
            "temporal loop",
            "time travel thriller",
            "high concept thriller",
        ])

    if "detective" in q:
        extras.extend([
            "detective",
            "investigation",
            "procedural thriller",
            "crime mystery",
        ])

    if "attack" in q or "stop an attack" in q or "prevent" in q:
        extras.extend([
            "prevent attack",
            "stop catastrophe",
            "race against time",
        ])

    if "thriller" in q:
        extras.extend([
            "thriller",
            "suspense",
            "mystery thriller",
        ])

    if not extras:
        return query

    return query + " " + " ".join(extras)

def retrieve_comps(query: str, k: int = 15) -> List[Dict[str, Any]]:
    """
    Return top-k similar movies to a query string (logline/description).
    Output is JSON-serializable list of dicts.
    """
    if _df is None or _vectorizer is None or _matrix is None:
        return []

    if not isinstance(query, str) or not query.strip():
        return []

    expanded_query = expand_query(query)
    q_vec = _vectorizer.transform([expanded_query])
    scores = cosine_similarity(q_vec, _matrix).ravel()

    # Take top-N candidates by similarity, then re-rank with a small finance-data bonus
    N = max(k * 50, 200)  # e.g., 200
    cand_idx = scores.argsort()[-N:][::-1]

    def bonus(i: int) -> float:
        row = _df.iloc[int(i)]
        b = row.get("budget")
        r = row.get("revenue")
        roi = row.get("roi")
        has_budget = (pd.notna(b) and float(b) > 0)
        has_revenue = (pd.notna(r) and float(r) > 0)
        has_roi = pd.notna(roi)
        return 0.08 * has_budget + 0.08 * has_revenue + 0.04 * has_roi  # small, won't dominate similarity

    cand_idx = sorted(cand_idx, key=lambda i: float(scores[int(i)]) + bonus(int(i)), reverse=True)
    top_idx = cand_idx[:k]

    cols = [
        "tmdb_id",
        "title",
        "genres_list",
        "budget",
        "revenue",
        "roi",
        "director",
        "dop",
        "editor",
    ]

    out: List[Dict[str, Any]] = []
    for i in top_idx:
        row = _df.iloc[int(i)]
        item = {}
        for c in cols:
            if c in row:
                item[c] = row[c]
            else:
                item[c] = None

        # Make sure lists are lists, floats are floats, NaNs -> None for JSON
        gl = item.get("genres_list")
        if isinstance(gl, np.ndarray):
            item["genres_list"] = gl.tolist()
        elif isinstance(gl, list):
            item["genres_list"] = gl
        else:
            item["genres_list"] = []
        for num_col in ["budget", "revenue", "roi"]:
            v = item.get(num_col)
            if v is None or pd.isna(v):
                item[num_col] = None
                continue

            fv = float(v)
            # Treat 0 (and negative) as "unknown" for budget/revenue
            if num_col in ("budget", "revenue") and fv <= 0:
                item[num_col] = None
            else:
                item[num_col] = fv
        b = item.get("budget")
        r = item.get("revenue")
        if item.get("roi") is None and b is not None and r is not None and b > 0:
            item["roi"] = r / b

        if item.get("roi") is not None:
            item["roi"] = round(float(item["roi"]), 2)

        if pd.isna(item.get("tmdb_id")):
            item["tmdb_id"] = None
        else:
            item["tmdb_id"] = int(item["tmdb_id"])

        for s_col in ["title", "director", "dop", "editor"]:
            v = item.get(s_col)
            if v is None or (isinstance(v, float) and pd.isna(v)):
                item[s_col] = None
            else:
                item[s_col] = str(v)

        for k in ["title", "director", "dop", "editor"]:
            item[k] = fix_mojibake(item.get(k))

        item["sim_score"] = float(scores[int(i)])
        item["has_budget"] = item.get("budget") is not None
        item["has_revenue"] = item.get("revenue") is not None

        out.append(item)

    return out
