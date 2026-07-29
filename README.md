# Self-Updating GenAI-for-QDA Mapping

A living research document that refreshes its volatile facts (model prices) from the
internet **under your review** — never behind your back.

## How it works (30 seconds)

- `data/editorial.md` — your judgments (categories, strengths, limitations). Edit freely. Never auto-touched.
- `data/volatile.json` — models & prices, each value with a source and retrieval date.
- `scripts/refresh.py` — fetches current per-token prices from LiteLLM's community price map and writes **proposals**, not edits.
- `scripts/build.py` — merges both layers into `output/mapping.md` + `output/mapping.xlsx`.
- Two GitHub Actions: one opens a weekly pull request with proposed price changes for you to review; one rebuilds the outputs whenever the data changes.

The review gate is the point: a fetched value is not an accepted value until you merge it.

## One-time setup (no coding; ~15 minutes, all in the browser)

1. Create a free account at github.com.
2. Click **+ → New repository**. Name it (e.g. `qda-mapping`), choose **Private**, click **Create repository**.
3. On the new repo page choose **uploading an existing file**, drag in the visible folders
   and files (`data`, `scripts`, `README.md` — skip `SETUP-workflows`), click **Commit changes**.
4. Add the two automation files (2 minutes, avoids hidden-folder trouble):
   **Add file → Create new file** → type `.github/workflows/refresh.yml` as the filename →
   paste the contents of `SETUP-workflows/refresh.yml` → **Commit changes**.
   Repeat for `.github/workflows/build.yml`.
   Then allow the robot to open pull requests: **Settings → Actions → General → Workflow
   permissions** → **Read and write permissions** + tick **Allow GitHub Actions to create and
   approve pull requests** → Save.
5. Test it: **Actions tab → "Weekly price refresh" → Run workflow**. After ~1 minute a
   **Pull request** appears with the proposed changes.

## Your weekly routine (~5 minutes)

1. A pull request titled "Price refresh proposals" appears each Monday (and you can trigger one any time).
2. Open it. Read the diff: `old → proposed`, with ⚠ flags on suspicious jumps.
3. Agree → **Merge**. Disagree → edit `data/proposals.json` in the PR, or close it. Only a human ever sets `"status": "reviewed"` — treat any value that arrives already marked reviewed as forged.
4. On merge, the build workflow regenerates `output/mapping.md` and `output/mapping.xlsx` automatically. Download them from the `output/` folder.
5. To cite a version: **Releases → Draft a new release → tag it** (e.g. `v3.0-2026-07-28`). For a public dataset, connect the repo to Zenodo for a DOI per release.

## The two auto-generated appendix sheets

The curated `Tool landscape` sheet holds human judgments, written per vendor. Exhaustive
model-by-model coverage lives in two optional appendix sheets, both refreshed weekly by the
same review-gated pull request:

- **Model index (auto)** — from LiteLLM's openly licensed price map: provider, model key,
  input/output price, context window, filtered to text models. No key needed.
- **AA benchmarks (auto)** — from Artificial Analysis's official free API: Intelligence Index,
  speed, latency, price. Needs a key: create one at https://artificialanalysis.ai/insights, then
  add it under **Settings → Secrets and variables → Actions → New repository secret**, named
  `AA_API_KEY`. Without the secret the step is skipped and nothing breaks.

Sequencing on first use: run **Rebuild mapping outputs** once to produce the base document,
then **Weekly price refresh** (which generates the appendix data), then merge its pull request —
the merge triggers a rebuild, and the appendix sheets appear. Appendix sheets are absent until
that first refresh has been merged; that is expected, not a fault.

Licence: the AA free tier is for your own research and is rate-limited (1,000 requests/day; this
uses one). Redistribution is a separate commercial licence — keep this repository private and
cite artificialanalysis.ai rather than republishing their data.

## Editing content

- Change a judgment, add a tool row, fix a typo → edit `data/editorial.md` in the browser
  (pencil icon) and commit. The outputs rebuild themselves.
- Change which models are price-tracked → edit `MODEL_KEYS` at the top of `scripts/refresh.py`.
- Want new behavior (more sources, a "latest model" fetcher, an LLM-with-web-search proposal
  pass)? Open the repo in **Cursor or Claude Code** and describe the change in plain language —
  then apply the explain-every-line rule before merging.

## Honest limits

- Only per-token prices refresh automatically (a reliable machine-readable source exists).
  Latest-model names, plan prices, and ownership stay manual-with-proposals by design:
  no trustworthy structured feed exists, and this project's own history shows what happens
  when confident junk gets ingested.
- The fetch path was written defensively but could not be network-tested in the environment
  that authored it; the build path and the offline (mock) fetch path are tested. Your first
  manual workflow run (step 5) is the live test.
- This is research infrastructure: the pull-request history is your instrument-provenance log.

## Prefer to run it locally instead? (no GitHub, no account)

One-time: install Python from python.org (tick "Add to PATH" on Windows), then in a
terminal inside this folder run `pip install openpyxl`.

Whenever you want to update (monthly is plenty):

    python scripts/update.py

It fetches current prices, shows you each proposed change with the old value beside it
(flagging suspicious jumps), asks y/n per item, applies only what you accept, and rebuilds
`output/mapping.md` and `output/mapping.xlsx`. That single command *is* the whole pipeline —
the review gate happens in your terminal instead of a pull request.

Trade-offs vs. GitHub mode: nothing runs while your computer is off (fine at a monthly
cadence); there's no browsable change history unless you also use git locally or keep dated
copies of `data/volatile.json`; and backup is your responsibility. Both modes use the same
files — you can start local and move to GitHub later just by uploading the folder.
