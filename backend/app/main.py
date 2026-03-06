# backend/app/main.py

from __future__ import annotations
from backend.app.agent.rag_llm import pinecone_query, generate_report, build_rag_query
import json
import os
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from starlette.responses import Response

from backend.app.agent.retrieval import retrieve_comps
from backend.app.agent.predictive import top_buckets_by_count

# ----------------------------
# env
# ----------------------------
BACKEND_DIR = Path(__file__).resolve().parents[1]  # backend/
load_dotenv(BACKEND_DIR / ".env", override=True)

# ----------------------------
# app
# ----------------------------
app = FastAPI()
FRONTEND_DIR = BACKEND_DIR.parent / "frontend"  # C:\dev\movie-dev-copilot\frontend

app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

@app.get("/")
def serve_frontend():
    return FileResponse(str(FRONTEND_DIR / "index.html"))

STATIC_PATH = Path(__file__).parent / "static"
ARCH_FILE = STATIC_PATH / "architecture.png"

# ----------------------------
# schema
# ----------------------------
class ExecuteIn(BaseModel):
    prompt: str

# ----------------------------
# helpers
# ----------------------------
def json_utf8(payload: dict, status_code: int = 200) -> Response:
    return Response(
        content=json.dumps(payload, ensure_ascii=False),
        media_type="application/json; charset=utf-8",
        status_code=status_code,
    )

def postfilter_matches(matches: List[Dict[str, Any]], keep: int = 6) -> List[Dict[str, Any]]:
    seen = set()
    out: List[Dict[str, Any]] = []
    for m in matches:
        md = m.get("metadata") or {}
        title = (md.get("title") or "").strip()
        if not title:
            continue
        key = title.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(m)
        if len(out) >= keep:
            break
    return out

# ----------------------------
# endpoints (required)
# ----------------------------
@app.get("/api/team_info")
def team_info():
    return {
        "group_batch_order_number": "3_9",
        "team_name": "Movie Development Copilot",
        "students": [
            {"name": "Maayan", "email": "maayan.sadeh@campus.technion.ac.il"},
            {"name": "Hila", "email": "hila.litvak@campus.technion.ac.il"},
            {"name": "Yanis", "email": "Yanisp@campus.technion.ac.il"},
        ],
    }

@app.get("/api/agent_info")
def agent_info():
    return {
        "description": "Movie Development Copilot that generates a production report from a logline, genre and budget.",
        "purpose": "Find comps, sanity-check budget and estimate ROI.",
        "prompt_template": {"template": "Logline: {logline}, Genre: {genre}, Budget: {budget}"},
        "prompt_examples": [
            {
                "prompt": "Logline: A detective loses memory while chasing a killer. Genre: Thriller. Budget: 12M",
                "full_response": "Example production report…",
                "steps": [],
            }
        ],
    }

@app.get("/api/model_architecture")
def model_architecture():
    if ARCH_FILE.exists():
        return FileResponse(ARCH_FILE, media_type="image/png")
    return {"error": "architecture.png not found"}

# ----------------------------
# execute (required)
# Must return ONLY: status, error, response, steps
# ----------------------------
@app.post("/api/execute")
def execute(payload: ExecuteIn):
    try:
        prompt = (payload.prompt or "").strip()
        if not prompt:
            return json_utf8(
                {"status": "error", "error": "Missing prompt", "response": None, "steps": []},
                400,
            )

        steps: List[Dict[str, Any]] = []

        # -------- local retrieval comps (your existing logic) --------
        comps = retrieve_comps(prompt, k=10)

        roi_vals = [c.get("roi") for c in comps if c.get("roi") is not None]
        roi_known = len(roi_vals)
        roi_total = len(comps)
        comps_median_roi = float(np.median(roi_vals)) if roi_known > 0 else None

        buckets = top_buckets_by_count(3)

        steps.append(
            {
                "module": "retrieval_local_comps",
                "prompt": {"query": prompt, "k": 10},
                "response": {"num_comps": len(comps), "roi_known": roi_known, "roi_total": roi_total},
            }
        )

        # -------- build base report text (deterministic) --------
        lines = [f"Prompt: {prompt}", "", "Top comparable movies:"]
        for i, c in enumerate(comps, 1):
            title = c.get("title") or "Unknown title"
            director = c.get("director")
            genres = c.get("genres_list") or []
            genres_str = ", ".join(genres) if isinstance(genres, list) else ""
            roi = c.get("roi")
            budget = c.get("budget")
            revenue = c.get("revenue")

            bits = [f"{i}. {title}"]
            if director:
                bits.append(f"(Director: {director})")
            if genres_str:
                bits.append(f"[{genres_str}]")
            if isinstance(roi, (int, float)):
                bits.append(f"ROI={roi:.2f}")
            if isinstance(budget, (int, float)) and budget > 0:
                bits.append(f"Budget=${budget:,.0f}")
            if isinstance(revenue, (int, float)) and revenue > 0:
                bits.append(f"Revenue=${revenue:,.0f}")

            lines.append(" ".join(bits))

        lines += ["", f"ROI data available for {roi_known}/{roi_total} comps."]
        if comps_median_roi is not None:
            lines.append(f"Median ROI among comps with ROI: {comps_median_roi:.2f}")

        lines += ["", "Typical ROI benchmarks by budget bucket (from dataset):"]
        for b in buckets:
            lines.append(
                f"- {b.bucket}: median ROI={b.median:.2f} (IQR {b.p25:.2f}-{b.p75:.2f}), n={b.count}"
            )

        base_text = "\n".join(lines)

        # -------- RAG context from Pinecone --------
        rag_error = None
        rag_query = build_rag_query(prompt)
        rag_matches: List[Dict[str, Any]] = []
        try:
            raw_matches = pinecone_query(rag_query, top_k=12)
            rag_matches = postfilter_matches(raw_matches, keep=6)
        except Exception as e:
            rag_error = str(e)
            rag_matches = []

        steps.append(
            {
                "module": "rag_pinecone",
                "prompt": {"query": rag_query, "top_k": 12, "keep": 6},
                "response": {"rag_count": len(rag_matches), "rag_error": rag_error},
            }
        )

        # Make short context lines for the LLM
        context_lines: List[str] = []
        for m in rag_matches:
            md = (m.get("metadata") or {})
            title = md.get("title") or "Unknown"
            director = md.get("director") or ""
            roi = md.get("roi")
            budget = md.get("budget")
            score = m.get("score")

            bits = [f"- {title}"]
            if director:
                bits.append(f"(Director: {director})")
            if isinstance(score, (int, float)):
                bits.append(f"[sim={score:.3f}]")
            if isinstance(roi, (int, float)):
                bits.append(f"ROI={roi:.2f}")
            if isinstance(budget, (int, float)):
                bits.append(f"Budget=${budget:,.0f}")

            context_lines.append(" ".join(bits))

        # -------- LLM report (optional; you already have this) --------
        system_prompt = (
            "You are a movie development assistant. "
            "Write a concise production-style report using the provided comparable films and ROI benchmarks. "
            "Do not invent numbers. If data is missing, say it is missing."
        )

        roi_bench_lines = [
            f"- {b.bucket}: median={b.median:.2f}, IQR={b.p25:.2f}-{b.p75:.2f}, n={b.count}"
            for b in buckets
        ]

        user_prompt = (
            f"Prompt:\n{prompt}\n\n"
            f"Top retrieved comps (RAG):\n"
            f"{chr(10).join(context_lines) if context_lines else 'No RAG comps available.'}\n\n"
            f"ROI benchmarks by bucket:\n{chr(10).join(roi_bench_lines)}\n\n"
            "Return sections:\n"
            "1) Logline interpretation (1-2 sentences)\n"
            "2) Comparable films (bullet list)\n"
            "3) Budget/ROI notes (short)\n"
            "4) Risks & assumptions (short)\n"
        )

        llm_text = None
        llm_error = None
        try:
            llm_text = (generate_report(system_prompt, user_prompt) or "").strip()
        except Exception as e:
            llm_error = str(e)
            llm_text = None

        steps.append(
            {
                "module": "llm_report",
                "prompt": {"system": system_prompt, "user": user_prompt},
                "response": {
                    "llm_error": llm_error,
                    "text_preview": (llm_text[:300] + "...") if llm_text else None,
                },
            }
        )

        report_text = (llm_text + "\n\n---\n\n" + base_text) if llm_text else base_text

        # IMPORTANT: return ONLY the required keys
        return json_utf8(
            {
                "status": "ok",
                "error": None,
                "response": report_text,
                "steps": steps,
            }
        )

    except Exception as e:
        return json_utf8(
            {"status": "error", "error": str(e), "response": None, "steps": []},
            500,
        )
