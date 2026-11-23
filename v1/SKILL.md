---
name: taiwan-road-safety-analysis
description: >
  Analyze real Taiwanese traffic collision open data (A1/A2), audit accident data,
  identify historical collision clusters, compare time windows, and create validated
  road-safety evidence reports. Use for Taiwan traffic accidents, accident hotspots,
  historical road warnings, casualty statistics, or collision-location analysis,
  even if the user does not mention a Skill. Do not use for unrelated questions,
  real-time emergency dispatch, individual hospital transport records, or promises
  that a commuting route is safe.
---

# Taiwan Road Safety — three-role analytics Skill

Use **real source files only**. An empty dataset means stop: never invent accident rows or results.
The 57023 source contains **A1 fatal accidents**, not all injured collisions; use verified A2 files if provided.

## 1. When to run
- Yes: analyze police Taiwan accidents, compare collision concentration, explore historical warning locations, accident time or weather statistics.
- No: generic routing, live accident alerts, medical dispatch, creative writing, unrelated questions.
- Note: historical density is **not** the risk/probability of a future accident without traffic exposure data.

## 2. Prerequisites
- Python 3.12 recommended; install `pip install -r requirements.txt`.
- Official source description: https://data.gov.tw/dataset/57023
- Annual A1/A2 data: https://data.gov.tw/dataset/177136
- Never claim a downloaded file is verified until the file is inspected and its SHA256 recorded.

## 3. Workflow (sequential, auditable handoffs)
1. Read `agents/01_inspector.md`. Verify real data provenance and run `python scripts/run_pipeline.py --input data/raw/<file>` (the pipeline invokes inspector, analyst, auditor stages in order).
2. The inspector validates actual input, normalizes supported variants, isolates invalid GPS records, and writes `outputs/01_*` files.
3. Read `agents/02_analyst.md`. It aggregates **records** and labels unit of analysis carefully, generates `outputs/02_*` and interactive `outputs/dashboard.html`.
4. Read `agents/03_auditor.md`. It independently recomputes totals and validates outputs, writes `outputs/03_audit.json`; any failure must be shown.
5. Show the final artifacts, source URL, date range, excluded coordinate count, and audit results. Open `streamlit run app.py` for the visual dashboard.
6. For requests to locate actual transferred hospitals or hospitalizations, say not available in accident data. Do not infer.

## 4. Role contracts
| Role | Guide | Input | Output | Not responsible for |
|---|---|---|---|---|
| Inspector | `agents/01_inspector.md` | original JSON/CSV/ZIP | `01_normalized.csv`, `01_quality.json` | chart/risk judgments |
| Analyst | `agents/02_analyst.md` | normalized CSV, quality JSON | `02_summary.json`, `02_hotspots.csv`, HTML | source repair or audits |
| Auditor | `agents/03_auditor.md` | raw-derived normalized + analyst outputs | `03_audit.json`, `03_report.md` | silently altering source data |

The three Markdown roles are instructional modules, not proof of three simultaneous LLM processes. The Python pipeline sequentially executes their deterministic tasks.

## 5. Outputs
- Original inputs stay unchanged in `data/raw`.
- All derived outputs go into `outputs`, with metadata and audit trail.
- Include city/date/record units, data type A1/A2, uncertainty, and limitations in any report.
- `outputs/03_audit.json` must be `PASS` before presenting numerical results as validated.

## 6. Failure handling
- Missing input / invalid format / no useful records: STOP and ask for real official download; do not replace with examples.
- Missing coordinates: include in time stats, exclude only from maps; state excluded count.
- Multi-party format without event identifiers: state record-level counts, never claim accident-event counts.
- A1-only: prominently label fatal accident subset, not nationwide all accidents.
- Never use a nearby hospital as a claim about where someone was transported.

## 7. Supporting documents
- `references/data_sources.md`: data lineage, definition and source URLs.
- `references/methods.md`: calculation, disclosure and methodological limitations.
- `assets/report_template.md`: human-readable report structure.

## 8. Trigger tests
Use `tests/skill_trigger_cases.md` to run real model A/B/C triggering trials. Save observable evidence and distinguish automatic vs manual invocation. Do not claim Python tests prove automatic Skill activation.
