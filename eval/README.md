# Eval: full pipeline vs. opencode agent pod

Same task, same model (`gpt-5.4-nano-2026-03-17`), two architectures: the scripted full pipeline (`/full-pipeline/process`) versus one autonomous agent run per document (`../../opencode-agent-pod`). Agent-pod results land here after the first agent run.

## Dataset

30 real trade documents. Bilingual FR/EN; mix of born-digital PDFs, scans, and OCR-overlay PDFs. The documents are not in the repo: they contain real parties, values, and vehicle identifiers, so they stay local (`dataset/` is git-ignored).

| Type | Count | What it is |
|---|---|---|
| CVC | 10 | SGS vehicle identification fiches (Toyota VINs) |
| NEF | 10 | e-FORCE cargo tracking fiches |
| RVC | 10 | SGS valuation / classification reports |

## Results — full pipeline

Run of 2026-07-12; raw outputs and `REVIEW.md` in
`../dataset/_pipeline_runs/2026-07-12_gpt-5.4-nano/`.

**Cost** — 30/30 documents completed.

| | |
|---|---|
| Wall time | median 46s/doc, max 250s (40.7 min serial) |
| Parsing | 17 text layer (~0.1s), 13 Docling+OCR (2–4 min) |
| LLM calls per doc | 3: field extraction, discrepancy analysis, report |
| LLM calls total | 90 |
| API cost | under $1 |

**Quality** — per-document risk and individual findings:

| | low | medium | high | critical |
|---|---|---|---|---|
| Risk verdicts (30 docs) | 3 | 18 | 9 | 0 |
| Findings (184) | 30 | 98 | 43 | 13 |

**Limit** — ~8 of the criticals are valuation ambiguities (declared vs.
SGS-assessed value bases) the pipeline can flag but not resolve. They are the
escalation set for the agent run.

Reproduce: `dataset/run_full_pipeline.py` (all 30 docs, resumable), then
`dataset/make_review.py` (builds `REVIEW.md`); run through `backend/.venv`
with the backend container up.
