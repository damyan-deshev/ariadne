# CBT Therapist Lane

Status: planned

Owner: local fork

Last updated: 2026-07-03

## Goal

Add a dedicated CBT-oriented therapist lane and persona to Ariadne.

The lane should use the Strix-hosted `Qwen3.6-27B-MTP-Q6_K` model, a separate
CBT literature corpus, and CBT-specific prompting/tooling rather than treating
CBT as a variant of the medical lane.

## Why This Exists

CBT interactions need a different operating envelope from general chat and from
the medicine lane:

- CBT method should be explicit: agenda, guided discovery, automatic thoughts,
  emotions, behaviors, experiments, homework, review, and feedback.
- Safety boundaries need to be direct for self-harm, plan, intent, acute risk,
  and medication advice.
- Bulgarian output needs a natural therapeutic register, not translated
  lab-prompt phrasing or slash gender forms.
- The model should have access to the CBT corpus without merging that corpus
  into the medical literature root.

## Non-Goals

- Do not merge CBT documents into `/home/deshev/open-webui/literature_corpus`.
- Do not make CBT depend on the medical corpus as its primary retrieval root.
- Do not copy the research-only eval prompts into production UX prompts.
- Do not build structured CBT diary/homework tooling in the first corpus/lane
  integration pass unless it becomes necessary for testing.

## Runtime Decisions

- Test model: `Qwen3.6-27B-MTP-Q6_K`.
- Initial mode: non-thinking.
- Use vendor-recommended non-thinking sampling for normal CBT tests:
  `temperature=0.7`, `top_p=0.80`, `top_k=20`, `min_p=0.0`,
  `presence_penalty=1.5`, `repetition_penalty=1.0`.
- Current Strix MTP setting is `spec-draft-n-max=2`; keep this as the default
  test path. Treat `n-max=3` as a separate benchmark.
- Commit Ariadne repo changes locally before deploying or pushing matching
  changes to the Strix box.

## Corpus Plan

Source corpus:

```text
/Volumes/External/Books/cbt/_compiled_docling_review
```

Target deployment root:

```text
/home/deshev/open-webui/cbt_corpus
```

The current CBT compiled corpus already has a serving layer, but its catalog
contains absolute Mac paths. Before copying it to Strix:

1. Patch/adapt `build_cbt_serving_layer.py` to emit paths relative to the
   compiled corpus root. The Ariadne-tracked canonical copy lives at
   `scripts/corpus/build_cbt_serving_layer.py`.
2. Add Ariadne-compatible catalog fields such as `primary_discipline`,
   `resource_type`, `evidence_tier`, `coverage_phrases`, `negative_scope`,
   `clean_toc`, and `what_this_is`.
3. Rebuild `_serving`.
4. Smoke test the rebuilt corpus locally through Ariadne's local corpus loader.
5. Copy the rebuilt corpus to `/home/deshev/open-webui/cbt_corpus`.

## Ariadne Integration Stories

### Story 1: Separate CBT Corpus Root

- Add `CBT_CORPUS_ROOT` config.
- Add `cbt` to backend working modes.
- Resolve CBT runtime to the CBT corpus root, not `LOCAL_CORPUS_ROOT`.
- Keep local corpus SQLite indexes domain/root-aware so CBT does not collide
  with medicine.

### Story 2: CBT Tools And Middleware

- Add CBT tool availability for the `cbt` working mode.
- Decide whether CBT uses generic local corpus tool names scoped to the CBT
  root or dedicated CBT-specific wrappers.
- Add CBT lane system prompt and selector guidance.
- Keep explicit safety behavior for self-harm, plan, intent, acute risk, and
  medication boundaries.
- Add `backend/open_webui/retrieval/local_corpus_packs/cbt.json` if the
  reasoning scaffold is exposed in CBT mode.

### Story 3: CBT Persona

- Seed a CBT therapist persona using `bound_model_id = Qwen3.6-27B-MTP-Q6_K`.
- Set `capabilities.preferred_working_mode = "cbt"`.
- Keep the production prompt natural, especially in Bulgarian.
- Do not expose the lab eval framing as end-user persona language.

### Story 4: Frontend Lane Surface

- Add `cbt` to the frontend working-mode unions/options.
- Add compact/normal labels and lane styling.
- Ensure selecting a CBT persona activates the CBT runtime path without manual
  JSON capability editing.

### Story 5: Future CBT Client-State Tools

There is no existing dedicated CBT diary, homework, thought-record, mood-log,
exposure-log, or behavioral-experiment tooling.

For the first pass, generic notes can be used as a lightweight substrate for
structured markdown records if needed. That is only a prototype path.

Future work should define first-class CBT client-state tools if the lane needs:

- durable thought records
- homework assignment and completion tracking
- mood or symptom logs
- behavioral experiment plans and reviews
- exposure hierarchies and exposure logs
- trend summaries across sessions
- reminders or scheduled follow-up
- clear therapist/client ownership and consent boundaries

## Test Plan

Add focused tests for:

- `normalize_working_mode("cbt")`
- CBT corpus root resolution
- CBT tool availability
- CBT middleware prompt injection
- local corpus retrieval against a small CBT fixture
- seeded CBT persona behavior and bound model selection

## References

- Inspection notes:
  `docs/cbt-lane-inspection-notes.md`
- English eval pack:
  `/Volumes/External/projects/cbt-therapist/eval/cbt_eval_v01.jsonl`
- Bulgarian eval pack:
  `/Volumes/External/projects/cbt-therapist/eval/cbt_eval_v01_bg.jsonl`
- Primary English 27B eval:
  `/Volumes/External/projects/cbt-therapist/eval-runs/cbt-eval-v01-qwen36-27b-thinking-plus-baseline-shortlist-20260703T141730Z/results.json`
- Primary Bulgarian 27B eval:
  `/Volumes/External/projects/cbt-therapist/eval-runs/cbt-eval-v01-bg-qwen36-27b-bf16-q6-q8-nothink-20260703T155324Z/results.json`

## Next Sensible Starting Point

Start with the corpus portability patch: make the CBT serving catalog relative
and Ariadne-compatible, rebuild `_serving`, smoke test locally, then commit
before copying the corpus to Strix.
