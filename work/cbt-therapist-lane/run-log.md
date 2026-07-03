# CBT Therapist Lane Run Log

Feature slug: `cbt-therapist-lane`

Execution mode: `sequential-main-agent`

## 2026-07-03 - S0 Started

Created the execution ledger and run log before implementation work.

Evidence:

- `work/cbt-therapist-lane/execution-ledger.md`
- `work/cbt-therapist-lane/run-log.md`

Next:

- Complete S0.
- Start S1: make the CBT serving layer portable and Ariadne-compatible.

## 2026-07-03 - S0 Completed

Marked S0 complete and moved S1 into progress.

Evidence:

- `work/cbt-therapist-lane/execution-ledger.md`
- `work/cbt-therapist-lane/run-log.md`

Next:

- Patch the CBT serving builder to emit portable relative paths and
  Ariadne-compatible catalog metadata.

## 2026-07-03 - S1 Completed

Patched the CBT serving builder at
`/Volumes/External/Books/cbt/_compiled_docling_review/tools/build_cbt_serving_layer.py`
to emit relative paths and Ariadne-compatible metadata fields.

Evidence:

- `PYTHONDONTWRITEBYTECODE=1 python3 /Volumes/External/Books/cbt/_compiled_docling_review/tools/build_cbt_serving_layer.py --help`
  exited 0.
- Rebuild command exited 0:
  `PYTHONDONTWRITEBYTECODE=1 python3 /Volumes/External/Books/cbt/_compiled_docling_review/tools/build_cbt_serving_layer.py /Volumes/External/Books/cbt/_compiled_docling_review --clean`
- Rebuild output reported `records: 6`, `usable_records: 6`, and
  `review_records: 0`.
- `rg -n '/Volumes/External|/Users/|/home/deshev'` over the rebuilt `_serving`
  output and builder returned no matches.
- Catalog inspection found:
  - domains: `cbt`
  - primary discipline: `cognitive_behavioral_therapy`
  - resource types: `manual`, `reference`, `textbook`
  - evidence tiers: `clinical_manual`, `reference`, `textbook`
  - no missing required values for `selected_dir`, `document_dir`,
    `retrieval_markdown_path`, `primary_discipline`, `resource_type`,
    `evidence_tier`, `coverage_phrases`, `negative_scope`, `clean_toc`, or
    `what_this_is`.

Next:

- Smoke test the rebuilt CBT corpus through Ariadne's local corpus loader and
  retrieval path.

## 2026-07-03 - S2 Completed

Smoke tested the rebuilt CBT corpus through Ariadne's local corpus loader using
a scratch `DATA_DIR`.

Evidence:

- Command exited 0:
  `DATA_DIR=/tmp/ariadne-cbt-lane-smoke-data PYTHONPATH=/Users/damyandeshev/projects/ariadne/backend python3 - <<'PY' ...`
- Loader output:
  - root: `/Volumes/External/Books/cbt/_compiled_docling_review`
  - domains: `['cbt']`
  - CBT usable books: `6`
- Shortlist output:
  - status: `ok`
  - count: `3`
  - top books: `Doing CBT`, `Oxford Guide to Behavioural Experiments in
    Cognitive Therapy`, and `Cognitive Behavior Therapy, Third Edition: Basics
    and Beyond`
- Evidence retrieval output:
  - status: `ok`
  - candidate count: `4`
  - FTS enabled: `True`
  - returned evidence from the Oxford behavioral experiments source.
- Scratch index directory `/tmp/ariadne-cbt-lane-smoke-data` was removed after
  the test.

Follow-up:

- Copied the patched external corpus builder into the Ariadne repo as
  `scripts/corpus/build_cbt_serving_layer.py` so the portability logic is
  versioned before Strix copy.

Next:

- Commit repo-tracked execution docs and canonical builder copy before copying
  the corpus to Strix.
