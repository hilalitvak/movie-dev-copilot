from __future__ import annotations

import os
from typing import List, Dict, Any

from openai import OpenAI
from pinecone import Pinecone


# ------------------------
# helpers
# ------------------------

def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing environment variable: {name}")
    return value


def _normalized_base_url() -> str | None:
    base = (os.getenv("LLM_BASE_URL") or "").strip()
    if not base:
        return None
    base = base.rstrip("/")
    if not base.endswith("/v1"):
        base += "/v1"
    return base


# ------------------------
# LLM
# ------------------------

def openai_client() -> OpenAI:
    return OpenAI(
        api_key=_require_env("LLM_API_KEY"),
        base_url=_normalized_base_url(),
    )


def embed_text(text: str) -> List[float]:
    client = openai_client()
    model = _require_env("LLM_EMBED_MODEL")
    resp = client.embeddings.create(model=model, input=text)
    return resp.data[0].embedding


def generate_report(system_prompt: str, user_prompt: str) -> str:
    client = openai_client()
    model = _require_env("LLM_CHAT_MODEL")
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        
    )
    return resp.choices[0].message.content or ""


# ------------------------
# Pinecone
# ------------------------

def pinecone_index():
    pc = Pinecone(api_key=_require_env("PINECONE_API_KEY"))
    index_name = _require_env("PINECONE_INDEX")
    return pc.Index(index_name)

def pinecone_query(query: str, top_k: int = 8) -> List[Dict[str, Any]]:
    index = pinecone_index()
    namespace = os.getenv("PINECONE_NAMESPACE", "movies")
    vector = embed_text(query)

    result = index.query(
        vector=vector,
        top_k=top_k,
        include_metadata=True,
        namespace=namespace,
    )

    # Works for both dict-like and object-like responses
    matches = getattr(result, "matches", None)
    if matches is None and isinstance(result, dict):
        matches = result.get("matches", [])
    return matches or []
