#!/usr/bin/env python3
"""Optional: pull Artificial Analysis benchmark data via their official free API.

This is the ONLY legitimate route to AA's numbers (Intelligence Index, speed,
latency, price) — their site data is theirs; we call the documented API with a key
rather than scraping or copying tables.

Setup:
  1. Create an account at https://artificialanalysis.ai/insights and generate an API key.
  2. In your repo: Settings -> Secrets and variables -> Actions -> New repository secret
     Name: AA_API_KEY     Value: <your key>
  3. The weekly workflow then fills data/aa_index.json automatically.
     Without the secret this script exits quietly and changes nothing.

Local use:  export AA_API_KEY=...  &&  python scripts/aa_index.py

Licence note: the free tier is for your own research/analysis and is rate-limited
(1,000 requests/day — this script makes one). Redistribution rights are a separate
commercial licence, so keep this repository private and CITE artificialanalysis.ai
in any publication rather than republishing their dataset.
"""
import os, json, sys, datetime, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUTP = ROOT / "data" / "aa_index.json"
BASE = "https://artificialanalysis.ai/api/v2"
CANDIDATES = ["/data/llms/models", "/language/models"]  # documented variants; first success wins

def get(path, key):
    import urllib.request, urllib.error
    req = urllib.request.Request(BASE + path, headers={"x-api-key": key})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())

def pick(d, *names):
    """Return the first present key (schemas evolve; fail soft, never invent)."""
    for n in names:
        if isinstance(d, dict) and d.get(n) is not None:
            return d[n]
    return None

def main():
    key = os.environ.get("AA_API_KEY")
    if not key:
        print("AA_API_KEY not set — skipping Artificial Analysis pull (this is fine).")
        return 0
    payload, used = None, None
    for path in CANDIDATES:
        try:
            payload, used = get(path, key), path
            break
        except Exception as e:
            print(f"  {path}: {e}")
    if payload is None:
        print("All candidate endpoints failed — check the key and the current API reference:")
        print("  https://artificialanalysis.ai/api-reference")
        return 1

    items = payload.get("data", payload if isinstance(payload, list) else [])
    if items and isinstance(items[0], dict):
        print("Field names returned by the API (use these to refine mapping below):")
        print("  " + ", ".join(sorted(items[0].keys())))

    rows = []
    for m in items:
        ev = m.get("evaluations") or {}
        pr = m.get("pricing") or {}
        creator = m.get("model_creator") or {}
        rows.append({
            "model": pick(m, "name", "model_name", "slug"),
            "creator": creator.get("name") if isinstance(creator, dict) else creator,
            "intelligence_index": pick(ev, "artificial_analysis_intelligence_index",
                                       "intelligence_index") or pick(m, "intelligence_index"),
            "output_speed_tps": pick(m, "median_output_tokens_per_second", "output_speed"),
            "latency_s": pick(m, "median_time_to_first_token_seconds", "latency"),
            "price_input_per_mtok": pick(pr, "price_1m_input_tokens", "input_price"),
            "price_output_per_mtok": pick(pr, "price_1m_output_tokens", "output_price"),
            "context_window": pick(m, "context_window", "max_input_tokens"),
        })
    rows = [r for r in rows if r["model"]]
    rows.sort(key=lambda r: (-(r["intelligence_index"] or -1), str(r["model"])))
    OUTP.write_text(json.dumps({
        "retrieved": datetime.date.today().isoformat(),
        "source": f"Artificial Analysis API ({used}) — free tier, own-research use; cite, do not republish",
        "count": len(rows), "models": rows,
    }, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(rows)} Artificial Analysis models -> {OUTP}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
