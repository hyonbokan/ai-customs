# Eval: full pipeline vs. opencode agent pod

Same task, same model (`gpt-5.4-nano-2026-03-17`), two architectures: the scripted full pipeline (`/full-pipeline/process`) versus one autonomous agent run per document (`../../opencode-agent-pod`).

## Dataset

30 real trade documents. Bilingual FR/EN; mix of born-digital PDFs, scans, and OCR-overlay PDFs. The documents are not in the repo: they contain real parties, values, and vehicle identifiers, so they stay local (`dataset/` is git-ignored).

| Type | Count | What it is |
|---|---|---|
| CVC | 10 | SGS vehicle identification fiches (Toyota VINs) |
| NEF | 10 | e-FORCE cargo tracking fiches |
| RVC | 10 | SGS valuation / classification reports |

## Results

Both runs of 2026-07-12. The pipeline ran all 30 documents; the pod ran the
8-document escalation set the pipeline could not resolve. Raw outputs:
`../dataset/_pipeline_runs/2026-07-12_gpt-5.4-nano/` (with `REVIEW.md` and
`ESCALATION.md`) and `../dataset/_agent_runs/2026-07-12_gpt-5.4-nano/` (with
`AGENT_REVIEW.md`, the per-document comparison).

**Cost** — pipeline 30/30 completed, pod 8/8 completed.

| | Full pipeline (30 docs) | Agent pod (8 escalation docs) |
|---|---|---|
| Wall time | median 42s/doc, max 301s (35.3 min serial) | median ~47s/doc, 24–91s |
| Parsing | 17 text layer (~0.1s), 13 Docling+OCR (2–4 min) | reads the staged text + PDF itself |
| LLM calls per doc | 3 fixed: extraction, discrepancy analysis, report | 1 autonomous run (every doc finished in 1 turn) |
| API cost | under $1 for 30 docs | $0.006–$0.022/doc, $0.094 for the set |

**Quality** — what each tier concluded about the same 8 escalation documents
(the valuation criticals the pipeline flagged but could not resolve), agent
verdicts independently verified (every value re-derived from the source text,
every reconciliation re-computed in code — `REVIEW_VERDICTS.md` in the agent
run dir):

| | Full pipeline (at flag time) | Agent pod (reviewed) |
|---|---|---|
| Risk verdicts | 6 high / 2 medium | 5 low / 3 critical — all 8 confirmed correct |
| The 8 criticals | flagged, none resolved | 5 resolved as extraction artifacts; 3 confirmed real: under-declaration, assessed FOB exceeds declared by ×3.35 / ×4.05 / ×1.35 (inspection required) |
| Structured output | schema-valid | 8/8 valid against the same schema |

What the agent taught fed back into the pipeline: its extraction schema now
separates declared vs. assessed values, so it resolves the artifact class
itself and names under-declarations directly (largest catch: ×5.69, a document
it previously scored medium with no findings). Its remaining blind spot —
OCR-scrambled scans where extraction misplaces figures — is the standing
escalation queue for the pod.

(Pipeline across all 30 docs, current run: risk 4 low / 16 medium / 9 high /
1 critical; 161 findings — 19 low / 85 medium / 42 high / 15 critical.)

## Reproducing

Pipeline (backend container up): `dataset/run_full_pipeline.py` (all 30 docs,
resumable), then `dataset/make_review.py` (builds `REVIEW.md`); run through
`backend/.venv`.

Agent pod: bring the pod up (`../../opencode-agent-pod`,
`.venv/bin/python -m pod`, `.env` supplies the token and provider key), then
`dataset/run_agent_pod.py` (escalation docs from `ESCALATION.md`, resumable)
through `backend/.venv`.
