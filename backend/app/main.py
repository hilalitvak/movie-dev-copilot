import json 
import numpy as np
from pathlib import Path
import os
from pathlib import Path
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]  # backend/
load_dotenv(BACKEND_DIR / ".env")

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from starlette.responses import Response
from backend.app.agent.retrieval import retrieve_comps
from backend.app.agent.predictive import top_buckets_by_count
from backend.app.agent.rag_llm import pinecone_query, generate_report

app = FastAPI()

# path to architecture image
STATIC_PATH = Path(__file__).parent / "static"
ARCH_FILE = STATIC_PATH / "architecture.png"

# -------- schema --------
class ExecuteIn(BaseModel):
    prompt: str

# -------- endpoints --------
def json_utf8(payload: dict, status_code: int = 200) -> Response:
    return Response(
        content=json.dumps(payload, ensure_ascii=False),
        media_type="application/json; charset=utf-8",
        status_code=status_code,
    )


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
        "prompt_template": {
            "template": "Logline: {logline}, Genre: {genre}, Budget: {budget}"
        },
        "prompt_examples": [
            {
                "prompt": "A detective loses memory while chasing a killer. Thriller. Budget 12M",
                "full_response": "Example production report…",
                "steps": []
            }
        ]
    }

@app.get("/api/model_architecture")
def model_architecture():
    if ARCH_FILE.exists():
        return FileResponse(ARCH_FILE, media_type="image/png")
    return {"error": "architecture.png not found"}

from backend.app.agent.retrieval import retrieve_comps
from backend.app.agent.predictive import (
    budget_to_bucket,
    get_bucket_stats,
    top_buckets_by_count,
)

@app.post("/api/execute")
def execute(payload: ExecuteIn):
    try:
        prompt = payload.prompt.strip()
        if not prompt:
            return json_utf8(
                {"status": "error", "error": "Missing prompt", "response": None, "steps": []},
                400
            )

        comps = retrieve_comps(prompt, k=10)

        # ROI availability
        roi_vals = [c.get("roi") for c in comps if c.get("roi") is not None]
        roi_known = len(roi_vals)
        roi_total = len(comps)
        comps_median_roi = float(np.median(roi_vals)) if roi_known > 0 else None

        buckets = top_buckets_by_count(3)

        # Build report text
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
            if roi is not None:
                bits.append(f"ROI={roi:.2f}")
            if budget and budget > 0:
                bits.append(f"Budget=${budget:,.0f}")
            if revenue and revenue > 0:
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
        
        # -------- RAG context from Pinecone --------
        rag_matches = []
        rag_error = None
        try:
            rag_matches = pinecone_query(prompt, top_k=6)
        except Exception as e:
            rag_error = str(e)
            rag_matches = []

        context_lines = []
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

        base_text = "\n".join(lines)
        report_text = (llm_text + "\n\n---\n\n" + base_text) if llm_text else base_text

        return json_utf8({
            "status": "ok",
            "error": None,
            "response": report_text,
            "steps": [],
            "comps": comps,
            "roi_known": roi_known,
            "roi_total": roi_total,
            "rag_count": len(rag_matches),
            "rag_error": rag_error,
            "llm_error": llm_error,
        })
    
    except Exception as e:
            return json_utf8(
                {"status": "error", "error": str(e), "response": None, "steps": []},
                500
            )
