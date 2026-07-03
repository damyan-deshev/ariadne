# CBT Toolkit Inventory And Architecture Notes

Date: 2026-07-04

Status: working architecture note. This is not a PRD and not a clinical
protocol.

## Context

The CBT lane started as an Ariadne persona plus a separate CBT literature
corpus. The tooling requirements now look broader than a normal Open WebUI /
Ariadne working mode: the useful product is a structured CBT practice harness
with durable client-state tools, corpus-grounded guidance, model routing, UI
state, export, and safety boundaries.

Architecture decision for now:

- Start inside Ariadne because the local model, persona plumbing, Strix
  deployment path, and literature corpus access already exist.
- Build the CBT toolkit as a portable domain layer with thin Ariadne adapters.
- Avoid hard-coding Open WebUI assumptions into the CBT schemas and workflows.
- Keep the option open to extract this into a standalone harness later.

In practice: build this as if it may become `cbt-harness`, but host the first
prototype in Ariadne.

## Why Plain Notes Are Not Enough

A human CBT therapist can work with a notebook and pen because the human keeps
the schema in their head. Ariadne cannot safely rely on loose notes alone if we
want durable practice tools.

Plain notes are still useful for narrative session notes, but structured tools
are needed for:

- validation of required fields and optional/skippable fields
- partial saves without losing the user's work
- model-readable state without scraping prose
- trend summaries across time
- therapist-share exports separated from private raw records
- safety routing for crisis, medication, abuse, and scope boundaries
- UI reflection of active tool, corpus, and persona
- future extraction into a standalone app or harness

## Client Toolkit

These are the client-side tools to build from item 1 through item 11. The order
is also the recommended implementation order unless later prototyping changes
the dependency graph.

### 1. Thought Record

Purpose: capture and rework automatic thoughts.

Variants:

- quick 3-column: situation, automatic thought, alternative thought
- full 7-column: situation, emotion, automatic thought, evidence for, evidence
  against, balanced thought, emotion re-rate
- optional extended fields: cognitive distortion, behavior, body sensation,
  safety behavior, core belief, learning

Core requirements:

- save partial records
- no mandatory mood gate before thought work
- user confirms before model rewrites or stores a balanced thought
- allow "I do not know yet" values
- support examples from corpus, but do not inject long literature excerpts
- exportable as private JSON and readable summary

Likely schema primitives:

- `id`
- `created_at`
- `updated_at`
- `locale`
- `mode`: `quick_3_column | full_7_column | extended`
- `situation`
- `automatic_thought`
- `emotion_ratings_before`
- `body_sensations`
- `behavior`
- `evidence_for`
- `evidence_against`
- `balanced_thought`
- `emotion_ratings_after`
- `cognitive_distortions`
- `safety_behaviors`
- `core_belief_hypotheses`
- `learning`
- `visibility`: `private | shareable_summary`

### 2. Practice / Action-Plan Tracker

Purpose: replace vague "homework" with concrete between-session practice.

User-facing language should prefer "practice", "exercise", or "action plan";
"homework" can remain an internal alias where useful.

Core requirements:

- define the planned practice in small, doable terms
- include rationale: why this practice matters
- specify when, where, and how long
- identify likely barriers
- create a backup plan
- record attempt, partial completion, completion, barrier, and learning
- review without blame: "what got in the way?"

Likely schema primitives:

- `id`
- `title`
- `goal_link`
- `rationale`
- `planned_action`
- `when_where`
- `expected_duration`
- `difficulty_rating`
- `barrier_plan`
- `backup_plan`
- `attempts`
- `completion_state`: `planned | attempted | partial | completed | skipped`
- `barriers_observed`
- `learning`
- `next_step`

### 3. Behavioral Experiment Planner

Purpose: test predictions rather than debate them abstractly.

Core requirements:

- capture prediction and belief strength before the experiment
- define an observable experiment
- name safety behaviors to reduce or drop
- capture what happened
- compare prediction against result
- extract learning and next experiment

Likely schema primitives:

- `id`
- `target_belief_or_prediction`
- `belief_strength_before`
- `experiment_plan`
- `observable_outcome`
- `safety_behaviors_to_reduce`
- `risk_or_scope_notes`
- `result`
- `belief_strength_after`
- `learning`
- `next_experiment`

### 4. Exposure Toolkit

Purpose: support gradual exposure and review learning over repeated trials.

Core requirements:

- create fear ladder / exposure hierarchy
- use SUDS or equivalent distress ratings
- plan exposures
- record safety behaviors
- record repeated trials, not just one-off events
- show learning and trend over time
- keep stronger safety boundaries than ordinary journaling

Likely schema primitives:

- `hierarchy_id`
- `theme`
- `items`
- `item_id`
- `feared_situation`
- `starting_suds`
- `target_safety_behaviors`
- `planned_exposure`
- `exposure_attempts`
- `suds_start`
- `suds_peak`
- `suds_end`
- `duration`
- `what_happened`
- `learning`
- `next_repetition`

### 5. Activity / Mood / Mastery Monitoring

Purpose: observe the relation between activity, mood, avoidance, mastery, and
pleasure.

Core requirements:

- activity chart
- mood before/after where useful
- pleasure/mastery ratings
- optional values/alignment rating
- identify avoidance and over-demanding schedules
- avoid making mood logging mandatory for every tool

Likely schema primitives:

- `id`
- `date`
- `time_block`
- `activity`
- `mood_ratings`
- `pleasure_rating`
- `mastery_rating`
- `values_alignment`
- `avoidance_flag`
- `energy_rating`
- `notes`

### 6. Problem-Solving Tool

Purpose: separate solvable practical problems from rumination loops and choose
a next action.

Core requirements:

- define the problem concretely
- split controllable and uncontrollable parts
- generate options
- compare costs/benefits
- choose the next smallest action
- review result

Likely schema primitives:

- `id`
- `problem_statement`
- `controllable_parts`
- `uncontrollable_parts`
- `options`
- `option_costs`
- `option_benefits`
- `chosen_step`
- `when_where`
- `result`
- `learning`

### 7. Worry / Rumination Tools

Purpose: reduce repetitive thinking loops and move the user toward either
action or attention shift.

Core requirements:

- distinguish actionable worry from non-actionable worry
- worry postponement
- rumination trigger log
- attention refocus plan
- worry experiment where appropriate

Likely schema primitives:

- `id`
- `trigger`
- `worry_or_rumination_content`
- `actionable`: `yes | no | unclear`
- `chosen_response`: `solve | postpone | refocus | experiment`
- `postponement_time`
- `refocus_activity`
- `experiment_link`
- `outcome`
- `learning`

### 8. Core Belief / Schema Work

Purpose: track deeper beliefs carefully after enough concrete thought-record
evidence exists.

Core requirements:

- avoid jumping to core beliefs too early
- track belief strength over time
- collect evidence for and against
- support continuum work
- practice alternative belief
- keep trauma-processing boundaries explicit

Likely schema primitives:

- `id`
- `belief`
- `belief_category`
- `belief_strength`
- `evidence_for`
- `evidence_against`
- `alternative_belief`
- `alternative_belief_strength`
- `continuum_anchor_low`
- `continuum_anchor_high`
- `practice_examples`
- `linked_thought_records`

### 9. Coping Cards / Reminders

Purpose: short, portable prompts for difficult moments.

Core requirements:

- very short text
- optional link to record/experiment/action plan
- local/offline-friendly
- no spammy engagement pattern
- exportable and printable

Likely schema primitives:

- `id`
- `title`
- `card_text`
- `context`
- `linked_tool_item`
- `created_from`
- `reviewed_at`
- `active`

### 10. Session Prep / Session Review

Purpose: help the user carry between-session work into a real or simulated
review.

Core requirements:

- what happened this week
- what the user wants to discuss
- what was practiced
- what was learned
- what was not done and what got in the way
- shareable summary separate from private records

Likely schema primitives:

- `id`
- `period_start`
- `period_end`
- `important_events`
- `agenda_candidates`
- `practice_review`
- `barriers`
- `learning`
- `questions_for_therapist`
- `shareable_summary`
- `private_notes`

### 11. Safety And Boundaries

Purpose: keep acute risk and scope boundaries explicit.

Core requirements:

- crisis plan
- warning signs
- protective factors
- trusted contacts/resources
- self-harm ideation, plan, intent, means checks when triggered
- medication boundary
- abuse/coercion flags
- explicit "not emergency care" behavior

Likely schema primitives:

- `id`
- `warning_signs`
- `coping_steps`
- `trusted_contacts`
- `professional_contacts`
- `local_emergency_resources`
- `means_safety_notes`
- `protective_factors`
- `risk_check_events`
- `boundary_events`
- `last_reviewed_at`

## Therapist / Guide Toolkit

The therapist-side toolkit is less about giving Ariadne "more notes" and more
about giving the model a stable scaffold for guiding and reviewing client work.

### 1. Case Formulation

Purpose: maintain a working CBT map.

Fields:

- presenting problems
- goals
- maintaining factors
- automatic thoughts
- emotions
- behaviors and avoidance
- safety behaviors
- core-belief hypotheses
- strengths/resources
- active constraints and boundaries

### 2. Session Structure

Purpose: keep CBT sessions from becoming generic supportive chat.

Fields:

- mood/check-in
- bridge from last session
- agenda
- action-plan review
- in-session work
- new action plan
- summary
- feedback

### 3. Treatment Plan / Protocol Map

Purpose: know which tool families are active and what comes next.

Fields:

- active focus areas
- active tool families
- staged next steps
- tools deliberately not used yet
- safety constraints
- language/register preferences
- corpus pack preference

### 4. Assignment Builder

Purpose: create practice items that are small, meaningful, and reviewable.

Fields:

- linked goal
- linked formulation item
- rationale
- task
- size/difficulty
- schedule
- obstacle plan
- review plan

### 5. Review Console

Purpose: review practice without blame and adapt the plan.

Fields:

- completed items
- partial attempts
- skipped items
- barriers
- repeated patterns
- learning
- adjustment recommendation

### 6. Measurement / Progress

Purpose: track trends without turning the app into a diagnostic instrument.

Fields:

- mood trend
- activity trend
- pleasure/mastery trend
- belief-strength trend
- SUDS/exposure trend
- practice engagement
- optional symptom scales only if explicitly designed and bounded

### 7. Safety / Risk Checklist

Purpose: consistent risk handling.

Fields:

- ideation
- plan
- intent
- means
- timeframe
- protective factors
- emergency boundary
- abuse/coercion flags
- medication boundary
- escalation notes

### 8. Corpus-Grounded Intervention Helper

Purpose: retrieve relevant CBT knowledge for the current tool and reflect the
active corpus in UI.

Fields:

- active corpus: CBT only
- current tool context
- retrieval query
- retrieved source IDs
- rationale summary
- citations/source handles where available

### 9. Notes

Purpose: separate raw notes, model working notes, and shareable summaries.

Fields:

- private guide notes
- client-visible summary
- therapist-share summary
- model scratchpad constraints
- linked records

## Architecture Shape

The CBT toolkit should be implemented as a domain layer plus host adapters.

### Domain Layer

Portable code and schemas that should not depend on Ariadne UI internals:

- tool schemas
- validators
- migration/versioning rules
- record IDs and timestamps
- privacy/export rules
- state transitions
- derived summaries
- safety event types

Possible module boundary:

```text
cbt_toolkit/
  schemas/
  validators/
  workflows/
  storage/
  export/
  safety/
  retrieval_context/
```

### Storage Layer

Start with a local filesystem adapter because it is inspectable and close to
the existing Ariadne "model can write files" primitive. Do not let raw markdown
be the canonical storage format.

Preferred canonical format:

- JSON records with schema version
- markdown summaries generated from JSON
- optional SQLite index for search/trends

Possible state root:

```text
cbt_state/
  records/
    thought_records/
    action_plans/
    behavioral_experiments/
    exposure_hierarchies/
    activity_logs/
    problem_solving/
    worry_rumination/
    core_beliefs/
    coping_cards/
    session_reviews/
    safety_plans/
  summaries/
  exports/
  indexes/
```

### Workflow Layer

Each tool should expose explicit operations:

- create draft
- update draft
- validate
- finalize
- summarize
- review
- export
- link to related record

The model should not directly mutate finalized records without an explicit
operation and user confirmation.

### Model Adapter

Ariadne-specific wrapper:

- inject CBT persona/system behavior
- select `Qwen3.6-27B-MTP-Q6_K`
- select CBT corpus automatically
- pass active tool context
- restrict retrieval to CBT corpus
- call structured-tool operations instead of writing arbitrary files where
  possible

### UI Adapter

Ariadne UI should reflect:

- selected CBT persona
- active CBT corpus
- active tool
- draft/finalized state
- private vs shareable fields
- safety boundary state where relevant

### Retrieval Adapter

The corpus/retrieval layer should be separable. Ariadne can provide the first
adapter, but the CBT toolkit should only depend on a small interface:

```text
retrieve_cbt_context(query, tool_context, locale) -> source snippets
```

This is the piece that can be borrowed by a standalone harness later.

## Ariadne Versus Standalone Harness

### Option A: Keep It Inside Ariadne

Pros:

- fastest path to test with current Strix model
- existing persona/model routing
- existing corpus/retrieval work
- existing UI and auth/session substrate
- fewer moving parts for the first prototype

Cons:

- Open WebUI/Ariadne abstractions are chat-first, not tool-first
- CBT practice needs durable structured state and repeated review loops
- UI may become awkward if forced into chat and generic notes
- extraction gets harder if schemas depend on Ariadne internals

### Option B: Build A New Harness Now

Pros:

- clean product fit: CBT tools first, chat second
- simpler mental model for client records and practice workflows
- easier mobile/quick-capture direction later
- no need to fight Open WebUI assumptions

Cons:

- slower first test
- need to rebuild model routing, session handling, retrieval adapter, UI shell,
  persistence, and deployment
- higher risk before we know the exact tool ergonomics

### Option C: Hybrid Path

Build the domain toolkit as a portable package inside Ariadne, with a thin
Ariadne adapter. Treat extraction as a planned possibility rather than a rewrite
emergency.

Recommendation: choose Option C.

Reasoning:

- We need Ariadne now for model/corpus leverage.
- The product shape is likely a separate harness.
- The safest engineering path is to make the first implementation portable:
  structured schemas, storage adapters, retrieval interface, model adapter, and
  UI adapter.

Decision rule:

- If the first three tools fit naturally in Ariadne with minimal UI compromise,
  continue in Ariadne.
- If guided thought records, action plans, and behavioral experiments require a
  custom tool-first surface, start extracting into a standalone CBT harness.

## First Architecture Slice

Before implementing all tools, define the shared substrate:

1. schema versioning
2. record identity and timestamps
3. draft/finalized lifecycle
4. private vs shareable fields
5. export format
6. linking between records
7. local filesystem storage adapter
8. Ariadne adapter for tool invocation
9. UI reflection of active persona/corpus/tool
10. safety event model

The first concrete tool on top of that substrate should be the thought record.

## Constraints

- Do not commit literature/corpus payloads.
- Keep CBT corpus separate from medicine and offsec corpora.
- Do not present Ariadne as a therapist or emergency service.
- Do not force mood tracking as a prerequisite for all CBT work.
- Do not build streak/engagement loops as the primary product mechanism.
- Keep Bulgarian copy natural, not literal/manual-like translation.
- Prefer structured records over model-written freeform markdown.

