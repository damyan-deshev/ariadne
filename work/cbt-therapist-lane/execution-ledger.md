# CBT Therapist Lane Execution Ledger

Feature slug: `cbt-therapist-lane`

Execution mode: `sequential-main-agent`

Last updated: 2026-07-03

## Operating Rules

- Work slices in dependency order.
- Keep the CBT corpus separate from the medical `literature_corpus`.
- Commit Ariadne repo changes before copying or deploying matching changes to
  the Strix box.
- Use `Qwen3.6-27B-MTP-Q6_K` with vendor-recommended non-thinking sampling for
  normal CBT tests.
- Verify every completed slice with concrete command output or file evidence.

## Slice Status

| ID | Slice | Status | Why This Order | Evidence |
| --- | --- | --- | --- | --- |
| S0 | Create execution ledger and run log | completed | Needed before executing the rest of the sequence | `work/cbt-therapist-lane/execution-ledger.md` and `work/cbt-therapist-lane/run-log.md` exist |
| S1 | Make CBT serving layer portable and Ariadne-compatible | completed | Strix copy and runtime integration require relative paths and compatible catalog fields | Patched builder, rebuilt 6 usable records, catalog has no absolute path matches, required Ariadne fields present |
| S2 | Rebuild CBT `_serving` locally and smoke test Ariadne local corpus retrieval | completed | Requires S1 builder changes | Loader saw domain `cbt` with 6 usable books; shortlist returned 3 books; retrieval returned 4 evidence chunks with FTS enabled |
| S3 | Commit repo-tracked execution/docs and canonical builder copy before Strix deploy | in_progress | Required by project operating rule before pushing to the box | Pending |
| S4 | Copy CBT corpus to separate Strix root | pending | Requires S2 evidence and S3 commit | Pending |
| S5 | Verify CBT corpus on Strix | pending | Requires S4 copy | Pending |
| S6 | Add Ariadne backend CBT corpus root and working mode | pending | Requires corpus shape to be known and verified | Pending |
| S7 | Add CBT tool and middleware wiring | pending | Requires S6 runtime selection | Pending |
| S8 | Add frontend CBT working-mode surface | pending | Requires backend mode contract | Pending |
| S9 | Seed CBT therapist persona | pending | Requires CBT working mode and model binding path | Pending |
| S10 | Add focused tests and CBT smoke eval | pending | Requires backend/frontend/persona implementation | Pending |

## Completed

- S0: Created execution ledger and run log.
- S1: Made the CBT serving builder emit relative paths and Ariadne-compatible
  metadata fields, then rebuilt `_serving`.
- S2: Smoke tested the rebuilt CBT corpus through Ariadne's local corpus loader
  and retrieval path.

## In Progress

- S3: Commit repo-tracked execution docs and canonical builder copy before
  Strix deploy.

## Blocked

- None.

## Next

Complete S3.

S3 is current because repo-tracked changes must be committed before any Strix
copy or deploy. The patched external corpus builder has also been copied into
the Ariadne repo as `scripts/corpus/build_cbt_serving_layer.py`.
