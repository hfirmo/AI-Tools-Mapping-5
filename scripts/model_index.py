#!/usr/bin/env python3
"""Build the comprehensive Model index appendix from an openly licensed price map.

Source: LiteLLM's community-maintained model_prices_and_context_window.json (MIT).
Covers ~1000+ entries across all major providers. This script filters to TEXT models
(chat/completion modes) and writes data/model_index.json, which build.py renders as a
separate "Model index (auto)" sheet.

This is an APPENDIX, not the curated mapping: it enumerates what exists and what it
costs. Analytic judgments stay in data/editorial.md, written per vendor, by a human.

Usage:          python scripts/model_index.py
Offline test:   python scripts/model_index.py --mock path/to.json
"""
import json, sys, datetime, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUTP = ROOT / "data" / "model_index.json"
URL = "https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json"
TEXT_MODES = {"chat", "completion", "responses"}

def fetch(mock=None):
    if mock:
        return json.loads(pathlib.Path(mock).read_text(encoding="utf-8"))
    import urllib.request
    with urllib.request.urlopen(URL, timeout=60) as r:
        return json.loads(r.read().decode())

def main():
    mock = sys.argv[sys.argv.index("--mock") + 1] if "--mock" in sys.argv else None
    try:
        raw = fetch(mock)
    except Exception as e:
        print("Fetch failed (offline or URL moved):", e); sys.exit(1)

    rows = []
    for key, e in raw.items():
        if not isinstance(e, dict) or key == "sample_spec":
            continue
        if e.get("mode") not in TEXT_MODES:
            continue
        i, o = e.get("input_cost_per_token"), e.get("output_cost_per_token")
        rows.append({
            "provider": e.get("litellm_provider", "?"),
            "model": key,
            "input_per_mtok": round(i * 1e6, 4) if isinstance(i, (int, float)) else None,
            "output_per_mtok": round(o * 1e6, 4) if isinstance(o, (int, float)) else None,
            "context_window": e.get("max_input_tokens") or e.get("max_tokens"),
        })
    rows.sort(key=lambda r: (r["provider"], r["model"]))
    payload = {
        "retrieved": datetime.date.today().isoformat(),
        "source": "LiteLLM model_prices_and_context_window.json (MIT licence)",
        "note": ("Auto-generated appendix: enumeration and list prices only, no analytic judgment. "
                 "Quality/benchmark rankings are NOT included — see artificialanalysis.ai/models, "
                 "cited as a live source rather than copied."),
        "count": len(rows),
        "models": rows,
    }
    OUTP.write_text(json.dumps(payload, indent=1, ensure_ascii=False), encoding="utf-8")
    provs = len({r["provider"] for r in rows})
    print(f"Wrote {len(rows)} text models across {provs} providers -> {OUTP}")

if __name__ == "__main__":
    main()
