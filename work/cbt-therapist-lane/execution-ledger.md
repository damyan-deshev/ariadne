# CBT Therapist Lane Execution Ledger

Feature slug: `cbt-therapist-lane`

Execution mode: `sequential-main-agent`

Last updated: 2026-07-03

## Operating Rules

- Work slices in dependency order.
- Keep the CBT corpus separate from the medical `literature_corpus`.
- Never stage or commit CBT literature payload, `_serving` corpus output, or
  compiled Docling corpus directories into git.
- Transfer corpus payload to Strix only over SSH/rsync or equivalent SSH-based
  copy.
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
| S3 | Commit repo-tracked execution/docs and canonical builder copy before Strix deploy | completed | Required by project operating rule before pushing to the box | Commit `0a8109432` |
| S4 | Copy CBT corpus to separate Strix root | completed | Requires S2 evidence and S3 commit | `rsync` transferred 1,275 regular files to `/home/deshev/open-webui/cbt_corpus` |
| S5 | Verify CBT corpus on Strix | completed | Requires S4 copy | Remote catalog has 6 CBT rows, no missing required fields, no absolute path values, 0 missing selected retrieval files, and medical root has no CBT domain |
| S6 | Add Ariadne backend CBT corpus root, working mode, and persona runtime defaults | completed | Requires corpus shape to be known and verified | `CBT_CORPUS_ROOT`, `working_mode=cbt`, `cbt_root`, and persona `runtime_defaults`; 12 targeted tests passed |
| S7 | Add CBT tool and middleware wiring | completed | Requires S6 runtime selection | CBT-specific wrappers, tool injection, selector guidance, native prompt, narration phases; 12 targeted tests passed |
| S8 | Add frontend CBT working-mode surface and persona-selected corpus reflection | completed | Requires backend mode contract | Frontend accepts `working_mode=cbt`, applies persona runtime defaults into chat params once per persona/default set, shows CBT in the working-mode control, and focused Vitest/format/diff checks passed |
| S9 | Seed CBT therapist persona | pending | Requires CBT working mode and model binding path | Pending |
| S10 | Add focused tests and CBT smoke eval | pending | Requires backend/frontend/persona implementation | Pending |

## Completed

- S0: Created execution ledger and run log.
- S1: Made the CBT serving builder emit relative paths and Ariadne-compatible
  metadata fields, then rebuilt `_serving`.
- S2: Smoke tested the rebuilt CBT corpus through Ariadne's local corpus loader
  and retrieval path.
- S3: Committed repo-tracked execution docs and the canonical CBT serving
  builder copy before Strix deploy.
- S4: Copied the CBT corpus to the separate Strix root
  `/home/deshev/open-webui/cbt_corpus`.
- S5: Verified the remote CBT corpus on Strix.
- S6: Added backend CBT runtime selection and a persona runtime defaults
  primitive.
- S7: Added CBT-specific corpus tools and middleware guidance.
- S8: Added frontend CBT working-mode controls and reflected persona-selected
  runtime/corpus defaults in chat params.

## In Progress

- None.

## Blocked

- None.

## Next

Start S9.

S9 should seed a CBT therapist persona bound to `Qwen3.6-27B-MTP-Q6_K` and set
persona runtime defaults so the frontend opens the CBT lane with
`local_corpus_mode=prefer`.
