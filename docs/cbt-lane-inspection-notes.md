# CBT Lane Inspection Notes

Date: 2026-07-03

Purpose: working notes for adding a CBT therapist persona/lane to Ariadne, with
Qwen3.6-27B on the Strix box and a CBT literature corpus alongside the existing
medicine/offsec corpora.

## Ground Rules

- Treat existing uncommitted changes as user-owned.
- Avoid editing current llama/router handoff files unless the CBT work requires
  it.
- If Python package installs become necessary, use a project `.venv` rather
  than the OS Python environment.
- No `AGENTS.md` exists inside `/Users/damyandeshev/projects/ariadne`; this
  note uses the user-provided `.venv` instruction as the active repo guidance.
- Strix host details come from the `strix-halo-llama-cpp` skill:
  `deshev@192.168.1.117`, SSH key
  `/Users/damyandeshev/.ssh/ariadne_192_168_1_117_ed25519`.
- Do not merge the CBT corpus into the medical `literature_corpus`. Keep CBT as
  a separate corpus root alongside existing roots such as `literature_corpus`,
  `offsec_corpus`, and `news_corpus`.

## Initial Git State

Repository root: `/Users/damyandeshev/projects/ariadne`

Branch:

```text
main...origin/main
```

Modified files present before CBT inspection:

```text
backend/open_webui/test/util/test_travel_orchestration.py
docs/llama-dual-router-handoff.md
docs/llama-mtp-qwen36-27b-benchmark.md
docs/llama-ngram-router-handoff.md
scripts/llama_patch/ariadne-llama-backend.sh
scripts/llama_patch/ngram-routing-benchmark.py
```

Untracked files present before CBT inspection:

```text
docs/llama-prompt-cache-reuse-handoff.md
docs/llama-rocm-gfx1151-idle-queue-workaround.md
docs/vllm-strix-halo-qwen36-27b-canary.md
```

Observed diff summary:

- Existing changes rename the 27B resident model alias from
  `Qwen3.6-27B-Dense-MTP-Q6_K` to `Qwen3.6-27B-MTP-Q6_K`.
- Existing docs/scripts now document/use `GPU_MAX_HW_QUEUES=1` for the dual
  resident Strix llama.cpp profile.
- One backend test fixture model id changed from `Qwen3.5-35B-A3B-Q8_0` to
  `Qwen3.6-35B-A3B-MTP-UD-Q8_K_XL`.
- `scripts/llama_patch/ngram-routing-benchmark.py` still routes image requests
  to the 27B text-only alias; the CBT task should not assume that benchmark
  router logic is production-safe.

## First Repository Landmarks

- Existing local corpus root in repo: `literature_corpus`.
- Existing retrieval code:
  - `backend/open_webui/retrieval/local_corpus.py`
  - `backend/open_webui/retrieval/local_corpus_reasoning.py`
  - `backend/open_webui/retrieval/corpus_runtime.py`
  - `backend/open_webui/retrieval/medical_lane.py`
  - `backend/open_webui/retrieval/offsec_corpus.py`
  - `backend/open_webui/retrieval/working_mode.py`
- Existing corpus packs:
  `backend/open_webui/retrieval/local_corpus_packs/*.json`.
- Existing persona substrate:
  - `backend/open_webui/models/personas.py`
  - `backend/open_webui/routers/personas.py`
  - `backend/open_webui/utils/personas.py`
  - frontend workspace persona routes under
    `src/routes/(app)/workspace/personas/`.
- Existing persona roadmap docs:
  `docs/roadmap/persona-runtime-and-continuity.md`,
  `docs/roadmap/persona-runtime-ux-and-implementation-plan.md`,
  `docs/roadmap/persona-partner-profile-spec.md`, and
  `docs/roadmap/persona-scene-note-spec.md`.

## Local Corpus Runtime Findings

- `backend/open_webui/retrieval/working_mode.py` currently accepts only:
  `general`, `medical`, `general_science`, `offsec`, and `news`.
- `backend/open_webui/retrieval/corpus_runtime.py` maps:
  - `medical` -> `LOCAL_CORPUS_ROOT`
  - `general` + `local_corpus_mode=prefer` -> `LOCAL_CORPUS_ROOT`
  - `general_science` -> attached corpora, currently only `medicine`
  - `offsec` -> `OFFSEC_CORPUS_ROOT`
  - `news` -> `NEWS_CORPUS_ROOT`
- `backend/open_webui/config.py` defaults:
  - `ENABLE_LOCAL_CORPUS_TOOLS`: true when repo `literature_corpus` exists
  - `LOCAL_CORPUS_ROOT`: `literature_corpus`
  - `OFFSEC_CORPUS_ROOT`: `offsec_corpus`
- `backend/open_webui/retrieval/local_corpus.py` expects a serving catalog at
  `<root>/_serving/serving-catalog.jsonl`, creates per-domain SQLite FTS indexes
  under `DATA_DIR/local_corpus`, and exposes shortlist/evidence/table/figure
  access.
- The generic local corpus loader expects records shaped like the medical
  serving catalog:
  `domain`, `primary_discipline`, `resource_type`, `evidence_tier`,
  `coverage_phrases`, `negative_scope`, `clean_toc`, `what_this_is`,
  `selected_dir`, `parse_status`, etc.
- Missing record fields mostly fall back to generic defaults, so a minimal
  non-medical catalog can load, but ranking quality suffers.
- `local_corpus_reasoning.py` adds domain packs from
  `backend/open_webui/retrieval/local_corpus_packs/*.json`. A CBT domain would
  need `local_corpus_packs/cbt.json` before the reasoning tools
  `local_corpus_frame_problem`, `plan_axes`, `collect_axis_evidence`, and
  `assess_evidence` can use domain-specific scaffolding.

## Tool And Middleware Findings

- Built-in corpus tools live in `backend/open_webui/tools/builtin.py`.
- Tool availability is gated in `backend/open_webui/utils/tools.py`:
  - local corpus tools attach only for `medical`, `general`, and
    `general_science`
  - offsec gets only `offsec_consult` and `offsec_retrieve_evidence`
  - news gets its news-specific tools
- Lane system prompts and selector guidance live near the top of
  `backend/open_webui/utils/middleware.py`.
- Medical mode has a deterministic precheck:
  `assess_medical_corpus_sufficiency`, injected either as a forced default
  function-calling tool call or as metadata/system context for native tools.
- CBT will need changes in at least:
  - `working_mode.py`
  - `corpus_runtime.py`
  - `utils/tools.py`
  - `utils/middleware.py`
  - probably `tools/builtin.py` if we create CBT-specific tools
  - tests under `backend/open_webui/test/util/`
- Existing built-in local corpus wrappers always pass
  `__request__.app.state.config` into `local_corpus.py`, so today they resolve
  through `LOCAL_CORPUS_ROOT`. For CBT as a separate root, either add CBT-specific
  wrappers that pass a CBT root, or generalize the wrappers/runtime so the
  active lane maps to a resolved corpus root before calling the generic
  `local_corpus` engine.
- The existing config pattern already supports sibling roots:
  `LOCAL_CORPUS_ROOT`, `OFFSEC_CORPUS_ROOT`, `NEWS_CORPUS_ROOT`. CBT should
  follow that shape with a dedicated `CBT_CORPUS_ROOT` or a small generic
  corpus-root registry. Avoid overloading `LOCAL_CORPUS_ROOT`.

## Existing Medical Corpus Shape

- Repo-local `literature_corpus` is a medical corpus with 84 serving records,
  all under domain `medicine`.
- Strix `/home/deshev/open-webui/literature_corpus` is newer than the repo copy:
  101 serving records, all under domain `medicine`, with relative `selected_dir`
  paths such as `2512-24601v1--7f0e822fdde9/selected`.
- Strix sibling roots currently present:
  `literature_corpus`, `literature_corpus.prev-20260402`, `offsec_corpus`, and
  `news_corpus`.
- Strix does not currently have a CBT/therapy corpus root.
- Canonical inference layer is `_serving`, not older routing/profile catalogs.
- `literature_corpus/tools/build_markdown_serving_layer.py` is strongly
  medicine-specific:
  - hardcodes `domain: "medicine"`
  - hardcodes medical disciplines and resource types
  - writes `domains/medicine/...`
- This builder is useful as a pattern, not as a direct CBT builder.

## CBT Corpus Findings

Source: `/Volumes/External/Books/cbt/_compiled_docling_review`

- Size: approximately `286M`.
- Documents: 6 manifests and 6 `selected/retrieval.md` files.
- Source formats: 5 PDF and 1 EPUB.
- PDF text layers were usable; no OCR fallback was required.
- Figures/images described and injected: 382.
- Figure-description QC flags after manual review: 0.
- Serving review queue: empty.
- It already has a CBT-specific serving layer:
  - `_serving/domains/index.md`
  - `_serving/domains/cbt/index.md`
  - `_serving/domains/cbt/topics/*.md`
  - `_serving/domains/cbt/books/*.md`
  - `_serving/serving-catalog.jsonl`
- CBT topics currently present:
  `cbt_foundations`, `case_formulation`, `behavioral_experiments`,
  `behavior_change`, `eating_disorders`, `therapeutic_process`.
- Topic coverage:
  - `cbt_foundations`: core model, treatment structure, sessions, automatic
    thoughts, therapist skills.
  - `case_formulation`: conceptualization, schemas, beliefs, maintenance
    cycles, resilience/vulnerability maps.
  - `behavioral_experiments`: prediction testing, exposure, safety behaviors,
    learning reviews.
  - `behavior_change`: avoidance, behavioral activation, rumination,
    procrastination, emotion-driven behavior, skills practice.
  - `eating_disorders`: CBT-E/eating-disorder-specific material.
  - `therapeutic_process`: collaborative empiricism, relationship, agendas,
    supervision/reflection, treatment planning.
- `review-catalog.json` covers the 5 PDF routes. The EPUB route is present in
  serving and figure summaries but not in that PDF review catalog, so count
  checks should use manifests/serving catalog rather than review-catalog alone.
- The CBT serving builder is
  `/Volumes/External/Books/cbt/_compiled_docling_review/tools/build_cbt_serving_layer.py`.
- CBT catalog fields differ from Ariadne's generic local corpus record schema:
  it has `topics`, `topic_scores`, `authors`, `publisher`, absolute
  `retrieval_markdown_path`, etc., but not `primary_discipline`,
  `resource_type`, `evidence_tier`, `coverage_phrases`, `negative_scope`,
  or `what_this_is`.
- Current CBT catalog paths are absolute `/Volumes/External/...` paths.
  This is the main deployment blocker: after copying to Strix under
  a separate CBT corpus root, `selected_dir` and related paths must be relative
  or rewritten to remote-local paths.
- The target shape should be a separate sibling corpus root, not a merge into
  medical `literature_corpus`. Candidate root name for planning:
  `/home/deshev/open-webui/cbt_corpus`.
- CBT book directory names do not collide with the current Strix medical corpus
  directories, but collision avoidance is secondary because the deployment root
  should be separate anyway.
- Local smoke test through Ariadne's existing `local_corpus` functions:
  - `load_local_corpus_registry('/Volumes/External/Books/cbt/_compiled_docling_review')`
    loads domain `cbt` with 6 usable books on the Mac.
  - `shortlist_local_corpus_books(..., domain='cbt')` works.
  - `retrieve_local_corpus_evidence(...)` builds/uses FTS and returns evidence.
  - This success depends on absolute Mac paths existing and is not portable to
    Strix as-is.

## Docling And Serving Reuse Findings

- `~/projects/docling` is the upstream Docling checkout with an untracked
  `tools/` directory containing the corpus scripts.
- CBT compiled root copies of `medical_corpus_router.py`,
  `enrich_compiled_corpus.py`, and `build_book_profiles.py` match the
  `~/projects/docling/tools` copies, so the conversion/enrichment pipeline is
  reusable.
- The CBT serving builder in the compiled root is identical to the reusable
  skill script:
  `/Users/damyandeshev/.codex/skills/book-corpus-markdown/scripts/build_cbt_serving_layer.py`.
- The CBT builder currently writes absolute paths for `document_dir`,
  `selected_dir`, `manifest_path`, `raw_markdown_path`, `retrieval_markdown_path`,
  `plain_text_path`, and `figure_descriptions_path`.
- The newer medical builder at
  `/Volumes/External/Books/Medicine/_compiled_docling_review/tools/build_markdown_serving_layer.py`
  already has the portability patch: `normalize_record(manifest_path,
  compiled_root, overrides)` and fields written with
  `relative_to(compiled_root)`.
- Recommended corpus prep before Strix copy:
  1. Patch/adapt `build_cbt_serving_layer.py` to write relative paths.
  2. Add Ariadne-compatible fields to CBT records (`primary_discipline`,
     `resource_type`, `evidence_tier`, `coverage_phrases`, `negative_scope`,
     `clean_toc`, `what_this_is`) rather than relying on generic fallback values.
  3. Rebuild `_serving` locally.
  4. Smoke test `load_local_corpus_registry`, shortlist, and retrieval using the
     rebuilt separate CBT root.
  5. Copy the rebuilt CBT root to a separate Strix sibling directory.

## Persona And Lane Findings

- Persona runtime already supports the two main hooks needed for CBT:
  - `bound_model_id` can force the model for persona chats.
  - `capabilities.preferred_working_mode` can select a lane when the chat does
    not explicitly override `params.working_mode`.
- `backend/open_webui/main.py` resolves persona state before model dispatch and
  writes the effective working mode into metadata params.
- The existing `Morning News` persona uses this pattern with
  `preferred_working_mode: "news"`.
- Frontend persona selection applies the persona's bound model, but it does not
  directly set `params.working_mode` or `local_corpus_mode`; the backend
  preferred-working-mode hook does that later.
- `preferred_working_mode` alone does not imply `local_corpus_mode=prefer`.
  News works because its runtime path is independent of `local_corpus_mode`.
  CBT should either follow that lane-specific pattern or have explicit backend
  defaulting so a CBT persona actually gets the CBT corpus tools.
- Persona editor does not expose `preferred_working_mode` as a UI control, but
  unknown capability keys are preserved in the payload. A seeded/system CBT
  persona builder is cleaner than expecting manual capability JSON editing.
- Frontend working modes are hardcoded in:
  - `src/lib/components/chat/Chat.svelte`
  - `src/lib/components/chat/MessageInput.svelte`
  - `src/lib/components/chat/Placeholder.svelte`
- Adding CBT as a visible lane requires adding `cbt` to both backend
  `WORKING_MODES` and frontend `WorkingMode` unions/options.
- Strix llama.cpp endpoint is running on port `1234` in router mode with
  `GPU_MAX_HW_QUEUES=1`.
- Current Strix model aliases include:
  - `Qwen3.6-27B-BF16` currently loaded
  - `Qwen3.6-27B-MTP-Q6_K` configured and unloaded
  - `Qwen3.6-27B-UD-Q8_K_XL` configured and unloaded
- The Qwen3.6 27B aliases use
  `/home/deshev/models/templates/qwen36-27b-official-think-toggle.jinja` and
  currently default `chat-template-kwargs = {"enable_thinking": false}`.
- CBT persona can bind to an existing 27B alias without a model download. The
  exact alias should be chosen during implementation/runtime testing; default
  should be no-thinking unless explicitly testing thinking mode.

## Client-Side State And CBT Tooling Findings

- There is no existing CBT-specific diary, homework, thought-record, mood-log,
  exposure-log, or behavioral-experiment model/tool in the repo.
- Ariadne does have a generic personal notes substrate:
  - data model: `backend/open_webui/models/notes.py`
  - REST router: `backend/open_webui/routers/notes.py`
  - built-in chat tools: `notes_lookup`, `search_notes`, `view_note`,
    `write_note`, and `replace_note_content`
  - frontend notes components under `src/lib/components/notes/`
- Note rows are generic markdown-backed records:
  - `id`, `user_id`, `title`, `data`, `meta`, `created_at`, `updated_at`
  - markdown content is stored at `data.content.md`
  - access is mediated through the shared `AccessGrants` model
- Existing note tools are user-scoped, private-by-default for writes, and can
  search/view/update markdown content. This could support a first CBT prototype
  by creating structured markdown notes such as thought records or homework
  logs.
- Generic notes are not enough for a polished CBT lane if the product needs
  durable structured objects, trend analysis, reminders, completion tracking,
  repeated measures, or therapist/client separation. Those would require either
  new CBT-specific models/tools or a thin schema layer on top of notes.
- If notes are reused initially, the CBT persona prompt/tool descriptions should
  be explicit about consent and scope before writing client-facing records.

## Qwen3.6 27B Test Runtime Notes

- Fixed test alias for CBT work:
  `Qwen3.6-27B-MTP-Q6_K`.
- Current Strix `models.ini` entry for that alias:
  - `model = /home/deshev/models/Qwen3.6-27B-MTP-Q6_K.gguf`
  - `spec-type = mtp`
  - `spec-draft-n-max = 2`
  - `spec-draft-n-min = 1`
  - `chat-template-file = /home/deshev/models/templates/qwen36-27b-official-think-toggle.jinja`
  - `chat-template-kwargs = {"enable_thinking": false}`
- Official Qwen model card says Qwen3.6 thinks by default and does not support
  Qwen3-style `/think` and `/nothink` soft switches. For OpenAI-compatible
  runtimes, disable thinking through
  `chat_template_kwargs: {"enable_thinking": false}`.
- Official/vendor sampling recommendations:
  - Thinking, general tasks:
    `temperature=1.0`, `top_p=0.95`, `top_k=20`, `min_p=0.0`,
    `presence_penalty=0.0`, `repetition_penalty=1.0`.
  - Thinking, precise coding tasks:
    `temperature=0.6`, `top_p=0.95`, `top_k=20`, `min_p=0.0`,
    `presence_penalty=0.0`, `repetition_penalty=1.0`.
  - Instruct/non-thinking:
    `temperature=0.7`, `top_p=0.80`, `top_k=20`, `min_p=0.0`,
    `presence_penalty=1.5`, `repetition_penalty=1.0`.
- For CBT tests, start with non-thinking mode because evals showed it is
  concise and fast. Compare vendor non-thinking sampling against the previous
  deterministic eval setting (`temperature=0.0`) rather than assuming one
  should replace the other globally.
- Preserve-thinking exists in Qwen3.6, but do not enable it for first CBT tests.
  It is an agent/long-context option and should be evaluated separately because
  therapy turns need predictable boundaries and concise visible output.
- MTP/speculative references:
  - ggml-org recommends `--spec-type draft-mtp` with `--spec-draft-n-max 2` or
    `3` for the MTP GGUF.
  - The current Strix alias uses `n-max=2`, which is the safer initial value.
  - A llama.cpp issue reported deterministic output divergence with
    `--spec-draft-n-max 3` on a Qwen3.6 MTP model, while `n-max<=2` matched the
    non-MTP baseline in that report. Treat `n-max=3` as a separate benchmark,
    not the default CBT test setting.
- Source references checked:
  - Qwen official HF card: `https://huggingface.co/Qwen/Qwen3.6-27B`
  - Unsloth GGUF card: `https://huggingface.co/unsloth/Qwen3.6-27B-MTP-GGUF`
  - ggml-org MTP GGUF card:
    `https://huggingface.co/ggml-org/Qwen3.6-27B-MTP-GGUF`
  - llama.cpp issue on `n-max=3`:
    `https://github.com/ggml-org/llama.cpp/issues/23302`

## Eval Artifact Findings

- Eval packs:
  - `/Volumes/External/projects/cbt-therapist/eval/cbt_eval_v01.jsonl`
  - `/Volumes/External/projects/cbt-therapist/eval/cbt_eval_v01_bg.jsonl`
- Both packs have the same 16 case ids:
  `agenda_resistance_beginner`, `partner_is_the_problem`,
  `automatic_thought_work`, `emotion_tolerance_silence`,
  `behavioral_experiment_design`, `homework_nonadherence_repair`,
  `alliance_direct_challenge`, `panic_avoidance_loop`,
  `values_vs_mood_action`, `core_belief_evidence`,
  `termination_relapse_plan`, `safety_self_harm_ambiguous`,
  `medication_boundary`, `anger_externalizing`,
  `cultural_humility_check`, `rumination_loop`.
- The eval prompts are lab prompts. Do not copy the "research-only simulated
  session" framing into production persona prompts.
- The reviewed result directories inspected do not contain `review_notes.json`,
  so there are no human ratings/flags to import directly.
- English no-thinking 27B gives concise, generally useful CBT turns. Thinking
  mode often gives richer structure but is much longer and slower.
- Safety self-harm ambiguous cases: good outputs ask directly about self-harm,
  plan, and intent. This must remain explicit in production lane guidance.
- Medication boundary cases: good outputs avoid medication advice and redirect
  medication changes to a prescriber while still offering CBT-compatible support
  such as thought work or symptom/side-effect tracking.
- Bulgarian no-thinking outputs are usable but show prompt-induced awkwardness:
  slash gender forms (`изтощен/а`) and a translated/manual-like register. The
  production Bulgarian prompt should be more natural and should avoid slash
  gender morphology where possible.
- Runtime speed signals from evals:
  - Bulgarian Q6 no-thinking averaged about 13.36 tok/s.
  - Bulgarian BF16 no-thinking averaged about 5.83 tok/s.
  - Bulgarian Q8 no-thinking averaged about 9.21 tok/s.
  - English Q6 no-thinking averaged about 13.38 tok/s.
  These are eval-run signals only, not final production throughput claims.

## Test Surfaces

- Existing tests relevant to CBT lane work:
  - `backend/open_webui/test/util/test_local_corpus_tools.py`
  - `backend/open_webui/test/util/test_chat_response_middleware.py`
  - `backend/open_webui/test/util/test_lane_runtime.py`
  - `backend/open_webui/test/util/test_science_lane.py`
  - `backend/open_webui/test/util/test_news_lane.py`
  - `backend/open_webui/test/util/test_offsec_corpus_tools.py`
- A small CBT implementation should add focused tests for:
  - `normalize_working_mode("cbt")`
  - `resolve_corpus_runtime(... working_mode="cbt" ...)`
  - CBT built-in tool availability with separate root
  - native middleware injecting CBT lane prompt
  - CBT local corpus retrieval using a mini CBT corpus fixture

## Open Questions For Planning

- Whether CBT should be a new `working_mode` value, a persona capability that
  selects the existing medical local corpus path, or both.
- Exact remote root name for the separate CBT corpus. Current working candidate:
  `/home/deshev/open-webui/cbt_corpus`.
- Whether CBT should be exposed through a dedicated `CBT_CORPUS_ROOT` config or
  through a more generic multi-corpus root registry. Do not implement it as a
  merge into the medical corpus.
- Whether CBT tools such as diaries/homework should be Open WebUI tools,
  persona-scoped capabilities, first-class app state, or a small combination.
- Whether to update the CBT serving builder to emit Ariadne-compatible catalog
  records directly, or teach Ariadne's `local_corpus` loader a second record
  shape for topic-based corpora.
