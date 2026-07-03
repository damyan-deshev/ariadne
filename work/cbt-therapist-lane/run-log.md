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

## 2026-07-03 - S6 Completed

Added backend runtime support for the CBT corpus and a small persona runtime
defaults primitive.

Changes:

- Added `CBT_CORPUS_ROOT` config with default `cbt_corpus`.
- Added `cbt` to backend working modes.
- Added `resolve_cbt_corpus_root`, `cbt_root`, and `cbt_enabled` to corpus
  runtime selection.
- Added persona capability `runtime_defaults` support for runtime params:
  `working_mode`, `local_corpus_mode`, `science_research_mode`, and
  `science_attached_corpora`.
- Kept legacy `preferred_working_mode` and `preferred_local_corpus_mode`
  compatibility.
- Changed Morning News persona seeding to include
  `runtime_defaults: {"working_mode": "news"}`.
- Applied persona runtime defaults in `main.py` only when chat params do not
  explicitly set the same key.

Important behavior:

- A CBT persona can later set:
  `runtime_defaults: {"working_mode": "cbt", "local_corpus_mode": "prefer"}`.
- Manual user/chat params still win. If a user explicitly sets
  `local_corpus_mode: "off"`, the persona default does not override it.

Verification:

- Compile check exited 0:
  `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile backend/open_webui/main.py backend/open_webui/utils/personas.py backend/open_webui/retrieval/corpus_runtime.py backend/open_webui/retrieval/working_mode.py`
- Targeted tests exited 0:
  `.venv.py312.news-tests/bin/python -m pytest -q backend/open_webui/test/util/test_lane_runtime.py backend/open_webui/test/util/test_news_lane.py::test_morning_news_persona_form_uses_news_defaults backend/open_webui/test/util/test_news_lane.py::test_persona_preferred_working_mode_reports_news backend/open_webui/test/util/test_news_lane.py::test_persona_runtime_param_defaults_prefer_explicit_runtime_defaults`
- Test result: `12 passed, 7 warnings`.
- `git diff --check` exited 0.

Next:

- Add CBT tool and middleware wiring.

## 2026-07-03 - S7 Completed

Added CBT tool and middleware wiring.

Changes:

- Added CBT-specific built-in wrappers:
  - `cbt_corpus_shortlist_books`
  - `cbt_corpus_view_book_cards`
  - `cbt_corpus_retrieve_evidence`
  - `cbt_corpus_view_table`
  - `cbt_corpus_view_figure_metadata`
- CBT wrappers resolve `corpus_runtime.cbt_root` and pass that path into the
  generic local corpus engine, so CBT retrieval does not hit
  `LOCAL_CORPUS_ROOT`.
- Added CBT tool injection for `corpus_runtime.cbt_enabled`.
- Added CBT default selector guidance.
- Added CBT native system prompt injection.
- Added CBT tools to shared tool narration phases.

Verification:

- Compile check exited 0:
  `.venv.py312.news-tests/bin/python -m py_compile backend/open_webui/tools/builtin.py backend/open_webui/utils/tools.py backend/open_webui/utils/middleware.py backend/open_webui/retrieval/corpus_runtime.py`
- Targeted tests exited 0:
  `.venv.py312.news-tests/bin/python -m pytest -q backend/open_webui/test/util/test_lane_runtime.py backend/open_webui/test/util/test_local_corpus_tools.py::test_builtin_cbt_corpus_tools_use_cbt_root backend/open_webui/test/util/test_chat_response_middleware.py::test_build_default_selector_guidance_adds_cbt_corpus_rules backend/open_webui/test/util/test_chat_response_middleware.py::test_should_enable_shared_tool_narration_for_cbt_mode`
- Test result: `12 passed, 3 warnings`.
- `git diff --check` exited 0.

Known test harness note:

- `backend/open_webui/test/util/conftest.py` may stub
  `open_webui.utils.tools.get_builtin_tools` to `{}` when optional import
  dependencies are unavailable, so this slice verifies CBT wrappers and
  middleware directly rather than relying on the existing tool-availability
  tests in that lightweight harness.

Next:

- Add frontend `cbt` working mode and reflect persona-selected runtime/corpus
  defaults in the chat controls.

## 2026-07-03 - S8 Completed

Added frontend CBT working-mode surface and persona-selected runtime/corpus
reflection.

Changes:

- Added `cbt` to the chat working-mode union and selector options.
- Added a visible `CBT` working-mode control state in `MessageInput`.
- Added frontend persona runtime-default extraction for:
  `working_mode`, `local_corpus_mode`, `science_research_mode`, and
  `science_attached_corpora`.
- Applied persona runtime defaults once per persona/default set in
  `Chat.svelte`, so selecting a CBT persona can move the visible chat controls
  to `CBT` and set `local_corpus_mode=prefer`.
- Kept legacy `preferred_working_mode` and `preferred_local_corpus_mode`
  compatibility.
- Added Vitest coverage for the frontend runtime-default extraction.

Verification:

- Targeted Vitest exited 0:
  `npm exec -- vitest run src/lib/utils/personas.test.ts`
- Test result: `1 passed`, `2 tests`.
- Format check exited 0:
  `npm exec -- prettier --check src/lib/apis/personas/index.ts src/lib/utils/personas.ts src/lib/utils/personas.test.ts src/lib/components/chat/Chat.svelte src/lib/components/chat/MessageInput.svelte src/lib/components/chat/Placeholder.svelte`
- `git diff --check` exited 0.
- Full `npm run check` was attempted and remains blocked by pre-existing,
  unrelated Svelte/TypeScript errors outside this slice, including
  `src/routes/auth/+page.svelte` i18n store typing errors and
  `src/routes/s/[id]/+page.svelte` implicit-any errors.

Next:

- Seed the CBT therapist persona with CBT runtime defaults and model binding.

## 2026-07-03 - S9 Completed

Seeded the CBT Therapist persona and extended persona runtime defaults so the
persona can open the CBT lane and carry Qwen non-thinking sampling params.

Changes:

- Added `CBT_THERAPIST_MODEL` config with default `Qwen3.6-27B-MTP-Q6_K`.
- Added CBT persona builder and admin seeding:
  - persona name: `CBT Therapist`
  - archetype: `coach`
  - bound model: `Qwen3.6-27B-MTP-Q6_K` unless overridden by config
  - startup ensure function: `ensure_cbt_therapist_personas_for_admins`
- Added CBT persona runtime defaults:
  - `working_mode=cbt`
  - `local_corpus_mode=prefer`
  - `temperature=0.7`
  - `top_p=0.8`
  - `top_k=20`
  - `min_p=0.0`
  - `presence_penalty=1.5`
  - `repeat_penalty=1.0`
  - `chat_template_kwargs={"enable_thinking": false}`
- Extended frontend and backend persona runtime-default parsing to include the
  sampling params and `chat_template_kwargs`.
- Added backend merge helper so persona defaults are applied to chat params only
  when the chat has not explicitly set the same param.
- Kept explicit `working_mode` conservative: if a request explicitly selects a
  different working mode, CBT's default `local_corpus_mode=prefer` is not added.
- CBT system prompt includes method scope, dedicated CBT corpus preference,
  corpus separation, Bulgarian style guidance, medication boundary, and direct
  self-harm/plan/intent/means safety questions.

Vendor parameter source:

- Qwen's Hugging Face model page documents the non-thinking sampling profile as
  `temperature=0.7`, `top_p=0.80`, `top_k=20`, `min_p=0.0`,
  `presence_penalty=1.5`, `repetition_penalty=1.0`, and shows disabling
  thinking through `chat_template_kwargs={"enable_thinking": false}` for
  OpenAI-compatible APIs. Ariadne uses `repeat_penalty=1.0`, the existing
  llama.cpp/OpenWebUI request key corresponding to repetition penalty.

Verification:

- Compile check exited 0:
  `.venv.py312.news-tests/bin/python -m py_compile backend/open_webui/utils/personas.py backend/open_webui/config.py backend/open_webui/main.py backend/open_webui/test/util/test_cbt_lane.py`
- Targeted backend tests exited 0:
  `.venv.py312.news-tests/bin/python -m pytest -q backend/open_webui/test/util/test_cbt_lane.py backend/open_webui/test/util/test_lane_runtime.py backend/open_webui/test/util/test_news_lane.py::test_persona_runtime_param_defaults_prefer_explicit_runtime_defaults`
- Backend result: `13 passed, 3 warnings`.
- Targeted frontend Vitest exited 0:
  `npm exec -- vitest run src/lib/utils/personas.test.ts`
- Frontend result: `1 passed`, `2 tests`.
- Prettier check for touched frontend files exited 0:
  `npm exec -- prettier --check src/lib/utils/personas.ts src/lib/utils/personas.test.ts src/lib/components/chat/Chat.svelte`
- `git diff --check` exited 0.

Next:

- Commit and push S9, then start S10 focused CBT smoke checks.
