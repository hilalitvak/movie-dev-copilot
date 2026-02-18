import sys
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))
load_dotenv(ROOT / "backend" / ".env")

from backend.app.agent.rag_llm import pinecone_query

matches = pinecone_query("dark thriller detective memory", top_k=5)
print("matches:", len(matches))
for m in matches[:3]:
    md = m.get("metadata", {})
    print("-", md.get("title"), "| score:", m.get("score"))
