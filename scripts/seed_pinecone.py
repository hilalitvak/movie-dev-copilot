from __future__ import annotations

import sys
import os
import time
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
import httpx
from openai import OpenAI
from pinecone import Pinecone


# ---------- setup ----------
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

ENV_PATH = ROOT / "backend" / ".env"
load_dotenv(ENV_PATH)

PARQUET_PATH = ROOT / "data" / "processed" / "movies_clean.parquet"


def make_openai_client() -> OpenAI:
    base = (os.getenv("LLM_BASE_URL") or "").rstrip("/")
    if not base.endswith("/v1"):
        base += "/v1"

    # Bigger timeouts help with large batches
    http_client = httpx.Client(timeout=httpx.Timeout(60.0, connect=30.0))
    return OpenAI(
        api_key=os.getenv("LLM_API_KEY"),
        base_url=base,
        http_client=http_client,
    )


def make_pinecone_index():
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    return pc.Index(os.getenv("PINECONE_INDEX"))


def embed_with_retry(openai_client: OpenAI, texts: list[str], max_retries: int = 6):
    last_err = None
    for attempt in range(max_retries):
        try:
            return openai_client.embeddings.create(
                model=os.getenv("LLM_EMBED_MODEL"),
                input=texts,
            )
        except Exception as e:
            last_err = e
            sleep_s = min(2 ** attempt, 30)  # 1,2,4,8,16,30...
            print(f"[embed retry {attempt+1}/{max_retries}] {type(e).__name__}: {e} -> sleep {sleep_s}s")
            time.sleep(sleep_s)
    raise last_err


def upsert_with_retry(index, vectors, namespace: str, max_retries: int = 6):
    last_err = None
    for attempt in range(max_retries):
        try:
            index.upsert(vectors=vectors, namespace=namespace)
            return
        except Exception as e:
            last_err = e
            sleep_s = min(2 ** attempt, 30)
            print(f"[upsert retry {attempt+1}/{max_retries}] {type(e).__name__}: {e} -> sleep {sleep_s}s")
            time.sleep(sleep_s)
    raise last_err


def build_metadata(row) -> dict:
    md = {
        "tmdb_id": int(row.get("tmdb_id")),
        "title": str(row.get("title") or ""),
    }

    genres = row.get("genres_list")
    if isinstance(genres, list):
        # Pinecone allows list of strings
        md["genres"] = [str(g) for g in genres if isinstance(g, str)]

    director = row.get("director")
    if isinstance(director, str) and director.strip():
        md["director"] = director.strip()

    # Only include numeric fields if valid (no null)
    budget = row.get("budget")
    if pd.notna(budget) and float(budget) > 0:
        md["budget"] = float(budget)

    revenue = row.get("revenue")
    if pd.notna(revenue) and float(revenue) > 0:
        md["revenue"] = float(revenue)

    roi = row.get("roi")
    if pd.notna(roi) and float(roi) > 0:
        md["roi"] = float(roi)

    return md


def upload_batch(rows, openai_client: OpenAI, index, namespace: str):
    texts = [str(r.get("doc_text") or "") for r in rows]

    emb_resp = embed_with_retry(openai_client, texts)

    vectors = []
    for row, emb in zip(rows, emb_resp.data):
        tmdb_id = int(row.get("tmdb_id"))
        md = build_metadata(row)
        vectors.append((str(tmdb_id), emb.embedding, md))

    upsert_with_retry(index, vectors, namespace)


def main():
    if not PARQUET_PATH.exists():
        raise FileNotFoundError(
            f"Missing {PARQUET_PATH}. Run: python -m backend.app.agent.build_index"
        )

    print("Loading parquet...")
    df = pd.read_parquet(PARQUET_PATH)
    print(f"Rows: {len(df)}")

    openai_client = make_openai_client()
    index = make_pinecone_index()
    namespace = os.getenv("PINECONE_NAMESPACE", "movies")

    batch_size = 20            # smaller batches = fewer disconnects
    throttle_sleep = 0.8       # slow down between batches
    total_uploaded = 0

    buffer = []
    for _, row in df.iterrows():
        tmdb_id = row.get("tmdb_id")
        if pd.isna(tmdb_id):
            continue

        doc_text = str(row.get("doc_text") or "").strip()
        if not doc_text:
            continue

        buffer.append(row)

        if len(buffer) >= batch_size:
            upload_batch(buffer, openai_client, index, namespace)
            total_uploaded += len(buffer)
            print(f"Uploaded: {total_uploaded}")
            buffer.clear()
            time.sleep(throttle_sleep)

    if buffer:
        upload_batch(buffer, openai_client, index, namespace)
        total_uploaded += len(buffer)

    print("DONE")
    print(f"Total uploaded: {total_uploaded}")


if __name__ == "__main__":
    main()
