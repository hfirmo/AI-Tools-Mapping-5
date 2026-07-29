#!/usr/bin/env python3
"""Fetch current per-token prices and propose updates. NEVER edits editorial.md.

Default source: LiteLLM's community-maintained price map (machine-readable JSON).
Writes: data/proposals.json + PROPOSALS.md (a human-readable diff for review).
Apply reviewed proposals with:  python scripts/refresh.py --apply
Offline test with a saved JSON:  python scripts/refresh.py --mock path/to.json
"""
import json, re, sys, datetime, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
VOLP = ROOT / "data" / "volatile.json"
PROPP = ROOT / "data" / "proposals.json"
URL = "https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json"

# Map each tool row to candidate LiteLLM keys (first found wins). EDIT freely as models rotate.
MODEL_KEYS = {
    "Claude": ["claude-fable-5", "claude-opus-5", "claude-sonnet-5", "claude-opus-4-8", "claude-sonnet-4-6"],
    "OpenAI API": ["gpt-5.6", "gpt-5.5", "gpt-5.1", "gpt-5"],
    "Google Gemini": ["gemini/gemini-3.1-pro", "gemini-3.1-pro", "gemini/gemini-3-pro-preview"],
    "DeepSeek — chat + hosted API": ["deepseek/deepseek-chat", "deepseek/deepseek-reasoner"],
    "Grok — xAI chat + hosted API": ["xai/grok-4-5", "xai/grok-4"],
    "Mistral — hosted + open weights": ["mistral/mistral-large-latest", "mistral/mistral-medium-latest"],
    "Alibaba Qwen — chat + hosted API": ["dashscope/qwen-max", "qwen-max"],
    "Cohere — enterprise API": ["command-a-03-2025", "cohere/command-a"],
}

def fetch(mock=None):
    if mock:
        return json.loads(pathlib.Path(mock).read_text())
    import urllib.request
    with urllib.request.urlopen(URL, timeout=30) as r:
        return json.loads(r.read().decode())

def fmt(price_map, key):
    e = price_map.get(key)
    if not e: return None
    i, o = e.get("input_cost_per_token"), e.get("output_cost_per_token")
    if i is None or o is None: return None
    return f"${i*1e6:g}/${o*1e6:g} per MTok ({key})"

def first_pair(s):
    m = re.search(r"\$([\d.]+)\s*/\s*\$([\d.]+)", s or "")
    return (float(m.group(1)), float(m.group(2))) if m else None

def main():
    mock = sys.argv[sys.argv.index("--mock") + 1] if "--mock" in sys.argv else None
    if "--apply" in sys.argv:
        vol = json.loads(VOLP.read_text(encoding="utf-8"))
        props = json.loads(PROPP.read_text(encoding="utf-8"))
        for tool, p in props.items():
            vol.setdefault(tool, {})
            vol[tool]["token_price"] = p["proposed"]
            vol[tool]["source"] = p["source"]
            vol[tool]["retrieved"] = p["retrieved"]
            vol[tool]["status"] = "auto-applied — review"
        VOLP.write_text(json.dumps(vol, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Applied {len(props)} proposals. Review the diff, then set status to 'reviewed'.")
        return
    try:
        prices = fetch(mock)
    except Exception as e:
        print("Fetch failed (offline or URL moved):", e); sys.exit(1)
    vol = json.loads(VOLP.read_text(encoding="utf-8"))
    today = datetime.date.today().isoformat()
    props, lines = {}, [f"# Price update proposals — {today}", "",
                        "Review each line. Merge the pull request only for values you accept;",
                        "edit data/proposals.json first to drop or correct any entry.", ""]
    for tool, keys in MODEL_KEYS.items():
        newv = next((v for v in (fmt(prices, k) for k in keys) if v), None)
        if not newv:
            lines.append(f"- **{tool}**: no matching key found in source — check MODEL_KEYS."); continue
        oldv = vol.get(tool, {}).get("token_price", "—")
        flag = ""
        a, b = first_pair(oldv), first_pair(newv)
        if a and b and (abs(a[0]-b[0]) > 0.5*max(a[0], 1e-9) or abs(a[1]-b[1]) > 0.5*max(a[1], 1e-9)):
            flag = "  ⚠ LARGE DEVIATION — verify against the vendor's own pricing page"
        if newv.split(" (")[0] not in (oldv or ""):
            props[tool] = {"old": oldv, "proposed": newv,
                           "source": "LiteLLM community price map", "retrieved": today}
            lines.append(f"- **{tool}**: `{oldv}` → `{newv}`{flag}")
        else:
            lines.append(f"- {tool}: unchanged.")
    PROPP.write_text(json.dumps(props, indent=2, ensure_ascii=False), encoding="utf-8")
    (ROOT / "PROPOSALS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(props)} proposal(s) written to data/proposals.json and PROPOSALS.md")

if __name__ == "__main__":
    main()
