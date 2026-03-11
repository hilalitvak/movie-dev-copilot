import os
from supabase import create_client


def get_supabase():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        raise RuntimeError("Missing SUPABASE_URL or SUPABASE_KEY")

    return create_client(url, key)


def save_agent_run(prompt, status, error, response, steps):
    sb = get_supabase()

    payload = {
        "prompt": prompt,
        "status": status,
        "error": error,
        "response": response,
        "steps_json": steps
    }

    print("SUPABASE URL EXISTS:", bool(os.getenv("SUPABASE_URL")))
    print("SUPABASE KEY EXISTS:", bool(os.getenv("SUPABASE_KEY")))
    print("PAYLOAD:", payload)

    res = sb.table("agent_runs").insert(payload).execute()

    print("SUPABASE INSERT RESULT:", res)
    return res