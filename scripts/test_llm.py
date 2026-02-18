import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).resolve().parents[1] / "backend" / ".env")

base = os.environ["LLM_BASE_URL"].rstrip("/")
if not base.endswith("/v1"):
    base += "/v1"

client = OpenAI(api_key=os.environ["LLM_API_KEY"], base_url=base)

resp = client.chat.completions.create(
    model=os.environ["LLM_CHAT_MODEL"],
    messages=[{"role": "user", "content": "Reply with exactly: OK"}],
    temperature=0,
)

print(resp.choices[0].message.content)
