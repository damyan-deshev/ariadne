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

## 2026-07-03 - S3 Completed

Committed the repo-tracked execution docs, roadmap update, and canonical CBT
serving builder copy before Strix deploy.

Evidence:

- Commit: `0a8109432 Add CBT corpus execution ledger and builder`
- Commit includes:
  - `scripts/corpus/build_cbt_serving_layer.py`
  - `work/cbt-therapist-lane/execution-ledger.md`
  - `work/cbt-therapist-lane/run-log.md`
  - `docs/roadmap/cbt-therapist-lane.md`

Next:

- Copy the rebuilt CBT corpus to the separate Strix root
  `/home/deshev/open-webui/cbt_corpus`.

## 2026-07-03 - S4 Completed

Copied the rebuilt CBT corpus to the separate Strix root.

Evidence:

- Target root: `/home/deshev/open-webui/cbt_corpus`
- Copy command exited 0:
  `rsync -az --delete --info=stats2 ... /Volumes/External/Books/cbt/_compiled_docling_review/ deshev@192.168.1.117:/home/deshev/open-webui/cbt_corpus/`
- `rsync` stats:
  - files: `1,311`
  - created files: `1,310`
  - regular files transferred: `1,275`
  - total file size: `297,356,699` bytes
  - deleted files: `0`

Next:

- Verify the remote serving catalog and path portability on Strix.

## 2026-07-03 - S5 Completed

Verified the CBT corpus on Strix.

Evidence:

- Remote root: `/home/deshev/open-webui/cbt_corpus`
- Remote size: `287M`
- Remote serving catalog:
  `/home/deshev/open-webui/cbt_corpus/_serving/serving-catalog.jsonl`
- Catalog inspection:
  - rows: `6`
  - domains: `['cbt']`
  - primary disciplines: `['cognitive_behavioral_therapy']`
  - resource types: `['manual', 'reference', 'textbook']`
  - evidence tiers: `['clinical_manual', 'reference', 'textbook']`
  - missing required fields: all `0`
  - missing selected retrieval files: `0`
  - absolute values in catalog fields: `0`
- `_serving` grep for `/Volumes/External`, `/Users/`, and `/home/deshev`
  returned 0 lines.
- Medical root separation check:
  - `/home/deshev/open-webui/literature_corpus/_serving/domains/cbt` is absent
  - `/home/deshev/open-webui/cbt_corpus/_serving/domains/cbt/index.md` is
    present

Next:

- Add Ariadne backend config/runtime support for `working_mode="cbt"` and a
  separate CBT corpus root.

## 2026-07-03 - Corpus Git Guard

Recorded the hard rule that CBT literature payload must not enter git.

Evidence:

- `git status --short --branch` showed only the execution ledger and run log
  modified before the guard change.
- `git ls-files` did not show CBT corpus payload, `_compiled_docling_review`,
  `serving-catalog.jsonl`, `retrieval.md`, `plain.txt`, or
  `figure-descriptions.md`.
- Repo-local files related to this work are limited to docs, execution logs, and
  the canonical builder script.
- The CBT corpus payload was transferred with `rsync` over SSH to:
  `/home/deshev/open-webui/cbt_corpus`.
- Added `.gitignore` guards for root-level `/cbt_corpus*/` and
  `/_compiled_docling_review/`.

Next:

- Commit the S5 ledger update and `.gitignore` guard before backend code work.
