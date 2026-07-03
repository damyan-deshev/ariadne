# llama.cpp Prompt Cache / Prefix Reuse Handoff

Date: 2026-05-10

Absolute path:

```text
/Users/damyandeshev/projects/ariadne/docs/llama-prompt-cache-reuse-handoff.md
```

Remote box:

```text
deshev@192.168.1.117
models dir: /home/deshev/models
runner: /home/deshev/models/run_llama.sh
log: /home/deshev/.local/state/llama-server/llama-server.log
```

SSH from the local Mac:

```bash
ssh -i ~/.ssh/ariadne_192_168_1_117_ed25519 deshev@192.168.1.117
```

Useful one-shot status command:

```bash
ssh -i ~/.ssh/ariadne_192_168_1_117_ed25519 deshev@192.168.1.117 \
  'cd /home/deshev/models && ./run_llama.sh status --json'
```

If entering the ROCm toolbox manually:

```bash
ssh -i ~/.ssh/ariadne_192_168_1_117_ed25519 deshev@192.168.1.117
cd /home/deshev/models
toolbox enter llama-rocm-7.2.2
cd /home/deshev/models
./run_llama.sh
```

## Why This Exists

The next investigation should focus on a possible prompt/cache reuse regression
after moving daily operation from the old BEAST-style single-model flow to the
new DUAL resident profile.

User observation:

- BEAST used to hit cache/reuse often.
- After the recent DUAL profile work, cache reuse appears to have dropped.
- We need to understand whether this is caused by DUAL routing, MTP, mmproj,
  model switching, prompt-template changes, Ariadne payload changes, or a
  misunderstanding of llama.cpp's different cache mechanisms.

Do not start by assuming "prompt cache is broken". The logs show several
different mechanisms with similar names.

## Critical Terminology Correction

The user's target behavior is:

```text
same chat + same model + long shared history -> process only the new suffix
```

In this llama.cpp server path, that maps primarily to `cache_prompt` /
`--cache-prompt`: the request prompt is compared with the previous completion
prompt, the common prefix is kept in the KV/slot state, and only the unseen
suffix has to be evaluated. In OpenAI-compatible responses, the useful counter
to watch is:

```text
usage.prompt_tokens_details.cached_tokens
```

This is **not** the same thing as `cache_reuse` / `n_cache_reuse`.

`cache_reuse` is a separate chunk/KV-shifting optimization controlled by
`--cache-reuse`. It may matter for some prompt-edit scenarios, but it is not the
main mechanism behind "I pasted the same long chat history and only the new
input should be processed".

As of this handoff, live DUAL is launched with:

```text
--no-cache-prompt --cache-reuse 256
```

That means the main prefix-reuse behavior the user cares about is currently
disabled. Treat this as the first thing to verify before chasing MTP/mmproj
limitations.

## Current Live Runtime

As of the handoff, production is:

```text
profile: dual
port: 1234
backend: /home/deshev/.local/opt/ariadne-llama/current/bin/llama-server
backend build: 20260509T010638-pinned-5d5f1b46e4f5-llama-rocm-7.2.2-imported
llama.cpp version: b9032 / 5d5f1b46e
GPU_MAX_HW_QUEUES=1
CTX=131072
MODELS_MAX=2
KV cache: q8_0/q8_0
router args: --models-preset /home/deshev/models/models.ini --parallel 1 --metrics
```

Current resident models:

```text
Qwen3.6-27B-MTP-Q6_K
Qwen3.6-35B-A3B-MTP-UD-Q8_K_XL
```

`run_llama.sh status --json` currently reports:

```json
"cache_prompt": false,
"cache_reuse": 256,
"preload_models": "Qwen3.6-27B-MTP-Q6_K,Qwen3.6-35B-A3B-MTP-UD-Q8_K_XL"
```

Important cache finding:

- `run_llama.sh` passes `--no-cache-prompt --cache-reuse 256`.
- Child logs still say `prompt cache is enabled, size limit: 8192 MiB`.

Interpret this carefully. The "prompt cache is enabled, size limit: 8192 MiB"
log line appears to refer to the newer host-memory/server prompt cache
machinery controlled by `--cache-ram`. It does not mean request-level
`cache_prompt` prefix reuse is enabled. `run_llama.sh status --json` reports
`"cache_prompt": false`, and the live command line has `--no-cache-prompt`.

So the likely immediate regression is simple: DUAL currently disables the
prefix reuse path that the user expects for long same-chat prompts.

## Recent Relevant Changes

These are the changes most likely to matter for cache behavior:

1. DUAL profile became the daily path.

```text
DUAL_PROFILE_MODELS_MAX=2
DUAL_PROFILE_CTX=131072
DUAL_PROFILE_PRELOAD_MODELS=Qwen3.6-27B-MTP-Q6_K,Qwen3.6-35B-A3B-MTP-UD-Q8_K_XL
```

2. DUAL runs one router plus two child `llama-server` processes.

Cache state is per child process. A conversation that moves between 27B and
35B cannot reuse the same child slot/cache state.

3. 27B resident lane uses MTP.

`models.ini`:

```ini
[Qwen3.6-27B-MTP-Q6_K]
model = /home/deshev/models/Qwen3.6-27B-MTP-Q6_K.gguf
spec-type = mtp
spec-draft-n-max = 2
spec-draft-n-min = 1
jinja = true
chat-template-file = /home/deshev/models/templates/qwen36-27b-official-think-toggle.jinja
chat-template-kwargs = {"enable_thinking": false}
```

Current logs show:

```text
srv load_model: cache_reuse is not supported with MTP, it will be disabled
slot load_model: speculative decoding context initialized
srv load_model: prompt cache is enabled, size limit: 8192 MiB
```

This is relevant, but it is not the first-order explanation for the user's
complaint. MTP disables `cache_reuse`; it does not automatically imply
`cache_prompt` prefix reuse must be disabled. Verify by enabling
`CACHE_PROMPT=on` and checking `cached_tokens`.

4. 35B resident lane is multimodal.

`models.ini`:

```ini
[Qwen3.6-35B-A3B-MTP-UD-Q8_K_XL]
model = /home/deshev/models/Qwen3.6-35B-A3B-MTP-UD-Q8_K_XL.gguf
mmproj = /home/deshev/models/mmproj-Qwen3.6-35B-A3B-Q6_K.gguf
jinja = true
chat-template-file = /home/deshev/models/templates/qwen36-35b-a3b-official-think-toggle.jinja
chat-template-kwargs = {"enable_thinking": false}
```

Current logs show:

```text
srv load_model: cache_reuse is not supported by multimodal, it will be disabled
srv load_model: prompt cache is enabled, size limit: 8192 MiB
```

This is relevant, but secondary for this investigation. Multimodal disables
`cache_reuse`; it does not by itself prove request-level `cache_prompt` prefix
reuse cannot work. The current global `--no-cache-prompt` is the more direct
problem.

5. Official Qwen3.6 Jinja templates were installed.

Remote files:

```text
/home/deshev/models/templates/qwen36-27b-official-think-toggle.jinja
/home/deshev/models/templates/qwen36-35b-a3b-official-think-toggle.jinja
```

Both were downloaded from official Qwen HF repos and have the same SHA256:

```text
c726bb991c3150f3ee3d690930f43ed1e7c28dcef27cfbc6de3400db1da2a9a6
```

The old `hauhau-aggressive` template files differed only by final newline from
the official templates. So template file replacement is unlikely to explain a
large cache regression by itself.

6. Ariadne thinking toggle path matters.

Frontend sets:

```text
params.custom_params.chat_template_kwargs.enable_thinking
```

Relevant repo file:

```text
/Users/damyandeshev/projects/ariadne/src/lib/components/chat/Chat.svelte
```

Backend merges `custom_params` into outgoing provider params:

```text
/Users/damyandeshev/projects/ariadne/backend/open_webui/utils/payload.py
/Users/damyandeshev/projects/ariadne/backend/open_webui/utils/middleware.py
```

If `enable_thinking=true` is sent, the Qwen template changes the generation
prompt suffix from an empty `<think></think>` block to an open `<think>`.
That changes the exact prompt token suffix and may reduce reuse when toggled
mid-chat. Default server kwargs are still `{"enable_thinking": false}`.

## What The Logs Currently Show

Useful current log patterns:

```bash
grep -nE 'cache_reuse|prompt cache|selected slot by LCP|LCP similarity|proxying request' \
  /home/deshev/.local/state/llama-server/llama-server.log
```

Observed examples:

```text
[56065] srv load_model: cache_reuse is not supported with MTP, it will be disabled
[35119] srv load_model: cache_reuse is not supported by multimodal, it will be disabled
[56065] srv load_model: prompt cache is enabled, size limit: 8192 MiB
[35119] srv load_model: prompt cache is enabled, size limit: 8192 MiB
```

Slot/LCP reuse still happens:

```text
selected slot by LCP similarity, sim_best = 0.941 (> 0.100 thold), f_keep = 0.727
selected slot by LCP similarity, sim_best = 0.704 (> 0.100 thold), f_keep = 0.711
selected slot by LCP similarity, sim_best = 0.490 (> 0.100 thold), f_keep = 0.499
selected slot by LCP similarity, sim_best = 0.242 (> 0.100 thold), f_keep = 0.702
```

So the regression may not be "zero reuse". It may be:

- `cache_prompt` disabled by the current launch flags,
- old `cache_reuse` disabled because of MTP/mmproj,
- LCP slot reuse still working but with lower `f_keep`,
- prompt cache updating but not producing the same hit behavior the user saw
  in BEAST.

## Strong Hypotheses For Next Chat

### Hypothesis 1: DUAL disables the actual prefix reuse flag

Live status reports `cache_prompt: false`, and `run_llama.sh` passes
`--no-cache-prompt`. This directly disables the behavior the user means by
"prompt cache": repeated same-chat prompts should keep the common prefix and
only evaluate the new suffix.

Test:

- Start a canary or short prod test with `CACHE_PROMPT=on`.
- Send the same long prompt twice to the same model id.
- Confirm `usage.prompt_tokens_details.cached_tokens` rises on the second
  request.
- Compare prompt eval time, wall time, and server logs.

### Hypothesis 2: BEAST did not load 35B with mmproj

If old BEAST was a single 35B text path without `mmproj`, `cache_reuse` may
have behaved differently. In DUAL, the daily 35B lane now always has `mmproj`,
because multimodality is important to the user. This is a secondary diagnostic
after `CACHE_PROMPT=on` has been tested.

Test:

- Start a canary 35B text-only lane without `mmproj`.
- Compare cache logs and repeated prompt latency against current 35B mmproj
  child.
- Do not break current prod unless user explicitly permits.

### Hypothesis 3: 27B MTP disables old `cache_reuse`

Current 27B fast lane uses MTP. Logs explicitly say `cache_reuse is not
supported with MTP`.

Test:

- Start a canary 27B no-MTP server on another port with same model, same
  template, same `--cache-reuse 256`.
- Compare repeated prompt behavior and logs.
- This is a diagnostic, not a recommendation to remove MTP. MTP is valuable
  for decode speed.

### Hypothesis 4: DUAL model routing splits the cache

The router spawns separate children. Reuse is per model child. If Ariadne
routes requests between 27B and 35B, even within one conceptual chat, there is
no shared slot/cache state.

Test:

- Repeat same long prompt N times to the same model id.
- Then alternate 27B/35B with same prompt.
- Parse prompt eval time, `f_keep`, and `prompt cache update took`.

### Hypothesis 5: Prompt shape changed due to thinking/tool payloads

The official Qwen3.6 templates are functionally the same as the previous files,
except final newline. But Ariadne can send `chat_template_kwargs.enable_thinking`
per request, and the backend can inject tools / native tool-call shape.

Test:

- Capture exact outgoing OpenAI-compatible payload from Ariadne for two
  consecutive messages in the same chat.
- Compare `messages`, `tools`, `chat_template_kwargs`, and model id.
- Verify whether any per-turn metadata, tool schema ordering, timestamps, or
  working-mode system prompt changes alter the prompt prefix.

### Hypothesis 6: The user is looking at prompt cache behavior, but the real
regression is slot prompt similarity / LCP retention.

The logs expose `sim_best` and `f_keep`, but not necessarily a clean "cache hit"
counter in the current output. The user remembers frequent "hits" from BEAST;
we need to identify which exact log line used to indicate that.

Test:

- Find old BEAST logs around successful cache behavior.
- Search for terms beyond `cache_reuse`: `cache hit`, `tokens_cached`,
  `cached_tokens`, `n_past`, `n_keep`, `f_keep`, `prompt cache`.

## Suggested First Commands For Next Chat

Check live status:

```bash
ssh -i ~/.ssh/ariadne_192_168_1_117_ed25519 deshev@192.168.1.117 \
  'cd /home/deshev/models && ./run_llama.sh status --json'
```

Pull cache-related logs:

```bash
ssh -i ~/.ssh/ariadne_192_168_1_117_ed25519 deshev@192.168.1.117 \
  'grep -nE "cache_prompt|cache_reuse|prompt cache|selected slot by LCP|LCP similarity|cached_tokens|prompt eval|proxying request" \
  /home/deshev/.local/state/llama-server/llama-server.log | tail -300'
```

Compare profile definitions:

```bash
ssh -i ~/.ssh/ariadne_192_168_1_117_ed25519 deshev@192.168.1.117 \
  'cd /home/deshev/models && nl -ba run_llama.sh | sed -n "44,78p;560,604p;692,855p"'
```

Find old BEAST evidence:

```bash
ssh -i ~/.ssh/ariadne_192_168_1_117_ed25519 deshev@192.168.1.117 \
  'grep -HnE "cache_prompt|cache_reuse|prompt cache|cache hit|cached_tokens|LCP similarity|f_keep|prompt eval" \
  /home/deshev/.local/state/llama-server/*.log | less'
```

Directly verify the current launch flag:

```bash
ssh -i ~/.ssh/ariadne_192_168_1_117_ed25519 deshev@192.168.1.117 \
  'pgrep -af llama-server | grep -E -- "--cache-prompt|--no-cache-prompt|--cache-reuse"'
```

Canary the actual desired behavior:

```bash
ssh -i ~/.ssh/ariadne_192_168_1_117_ed25519 deshev@192.168.1.117 \
  'cd /home/deshev/models && CACHE_PROMPT=on ./run_llama.sh'
```

Then run two same-model long-prompt requests and inspect
`usage.prompt_tokens_details.cached_tokens`. The expected healthy result is:
first request has few/no cached tokens; second request has a large cached token
count and much lower prompt eval cost.

## What Not To Do First

- Do not immediately disable MTP: it is probably responsible for the 27B speed
  win.
- Do not remove `mmproj` from the daily 35B lane without an alternative vision
  routing plan.
- Do not conflate `--cache-prompt`, `--cache-reuse`, server prompt cache, and
  LCP slot reuse. The user's use case is primarily `cache_prompt` prefix reuse.
- Do not restart production casually if the user is actively using it. Canary
  on another port is preferable for cache experiments.

## Likely Direction

The most likely immediate explanation is that the current DUAL daily path
passes `--no-cache-prompt`, so the request-level prefix reuse behavior is off.
Fix/test that first.

After `CACHE_PROMPT=on` is verified, the remaining secondary explanation is
that the DUAL daily path combines two features that disable the old
`cache_reuse` mechanism:

```text
27B: MTP -> cache_reuse disabled
35B: mmproj/multimodal -> cache_reuse disabled
```

Those facts may still matter, but they are not the same problem as long-chat
prefix reuse.

The next useful engineering decision depends on the `CACHE_PROMPT=on` test:

```text
if cached_tokens returns and latency improves:
  make CACHE_PROMPT=on the default for DUAL/BEAST unless a specific bug appears
else:
  investigate model routing, prompt shape changes, slot/LCP retention, then
  MTP/mmproj cache_reuse limitations
```

Explicit lanes may still be useful later:

```text
35B vision lane: mmproj enabled, accept cache_reuse limitations
35B text lane: no mmproj, optimized for cache reuse if confirmed
27B fast lane: MTP enabled, accept cache_reuse limitations unless upstream changes
optional 27B no-MTP diagnostic/cached lane: only if workload benefits
```

Then Ariadne's router can choose based on:

```text
vision -> 35B mmproj lane
same long text chat needing cache -> 35B text/cache lane
fast dense generation -> 27B MTP lane
do not switch model mid-chat unless explicitly worth losing cache locality
```
