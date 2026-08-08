# Ariadne llama.cpp Patch

This directory contains the downstream patches and tooling for Ariadne's
llama.cpp backend.

The primary server patch supports Ariadne's `stream + native tools + logprobs`
experiment. The UI patches keep the embedded llama.cpp web UI compatible with
newer llama.cpp server schemas while the patched image is built from source.

The kyuz0 toolboxes contain compiled llama.cpp binaries. This workflow does
not patch those binaries in place. It builds a derivative image from the
fresh kyuz0 image, recompiles `llama-server` with the Ariadne patch, and only
then uses that derivative image for the toolbox.

No host OS packages are installed by these scripts. Build dependencies are
installed inside the derivative container image layer.

## Files

- `patches/0001-server-allow-streamed-tool-calls-with-content-logprobs.patch`
  is a normal `git format-patch` patch against upstream `llama.cpp`.
- `patches/0002-ui-migrate-dry-penalty-last-n-default.patch` migrates older
  browser state that stored `dry_penalty_last_n = -1` and omits negative values
  from the UI request payload. Current llama.cpp server schemas reject negative
  values; upstream defaults use `64`, and `0` disables the DRY scan.
- `patches/0003-ui-build-without-pwa-asset-generation.patch` disables the PWA
  asset generation step inside the toolbox image build. The UI bundle still
  builds with Vite; this avoids asset-generator failures unrelated to Ariadne's
  server patch.
- `Containerfile.patched-llama` builds a patched derivative image.
- `build-patched-image.sh` wraps `podman build`.
- `refresh-toolboxes.sh` is a small compatibility wrapper.
- `refresh-toolboxes.patched.sh` is a kyuz0-style refresh script that builds
  patched images for every known llama.cpp toolbox before recreating toolboxes.
- `smoke-test-logprobs-tools.py` validates the OpenAI-compatible streaming API.
- `ariadne-llama-backend.sh` manages versioned `llama-server` backend builds,
  canary smoke tests, atomic symlink promotion, and rollback.

## Build A Patched Image

Example for the RADV toolbox:

```bash
scripts/llama_patch/build-patched-image.sh \
  --base-image docker.io/kyuz0/amd-strix-halo-toolboxes:vulkan-radv \
  --toolbox-name llama-vulkan-radv \
  --tag localhost/ariadne-llama-vulkan-radv:latest
```

Example for ROCm:

```bash
scripts/llama_patch/build-patched-image.sh \
  --base-image docker.io/kyuz0/amd-strix-halo-toolboxes:rocm-7.14 \
  --toolbox-name llama-rocm-7.14 \
  --tag localhost/ariadne-llama-rocm-7.14:latest
```

Then create the toolbox from the local patched image instead of the upstream
image:

```bash
toolbox create llama-vulkan-radv \
  --image localhost/ariadne-llama-vulkan-radv:latest \
  -- --device /dev/dri --group-add video --security-opt seccomp=unconfined
```

## Refresh Script Integration

For the full patched refresh flow, use:

```bash
bash scripts/llama_patch/refresh-toolboxes.sh
```

No arguments means `all`. The script uses kyuz0's toolbox image repository by
default, pulls the latest configured images, builds local Ariadne-patched
derivative images, and recreates the toolboxes from those local images.

By default, the script resolves the configured llama.cpp branch to an exact
upstream SHA before building and passes that SHA into the container build. This
keeps floating branch builds from silently reusing an older cached clone layer.
The checked-out upstream SHA is also written inside the image at:

```bash
/usr/local/share/ariadne-llama-upstream-ref
```

It supports these llama.cpp toolboxes:

- `llama-vulkan-amdvlk`
- `llama-vulkan-radv`
- `llama-rocm-6.4.4`
- `llama-rocm-6.4.4-rocwmma`
- `llama-rocm-7.2`
- `llama-rocm-7.2.1`
- `llama-rocm-7.2.1-pr21344`
- `llama-rocm-7.2.2`
- `llama-rocm-7.2.2-pr21344`
- `llama-rocm-7.2.3`
- `llama-rocm-7.14`
- `llama-rocm7-nightlies`

It does not patch non-llama toolboxes such as ComfyUI.

If you prefer to keep your existing `refresh-toolboxes.sh`, add this after
`podman pull "$image"` and before `toolbox create`:

```bash
patched_image="localhost/ariadne-${name}:latest"

~/models/ariadne/scripts/llama_patch/build-patched-image.sh \
  --base-image "$image" \
  --toolbox-name "$name" \
  --tag "$patched_image"

image="$patched_image"
```

The included patched refresh script builds the patched image before removing
the existing toolbox. If a patch no longer applies, compilation fails, or the
`llama-server` binary is not produced, the script fails closed and leaves the
existing toolbox intact.

Refresh/build logs are written under:

```bash
${XDG_STATE_HOME:-$HOME/.local/state}/ariadne-llama-patch/logs
```

Override with:

```bash
ARIADNE_PATCH_LOG_DIR=/path/to/logs bash scripts/llama_patch/refresh-toolboxes.sh
```

For full shell tracing:

```bash
ARIADNE_PATCH_TRACE=1 bash scripts/llama_patch/refresh-toolboxes.sh
```

Optional llama.cpp source overrides:

```bash
ARIADNE_LLAMA_REPO=https://github.com/ggml-org/llama.cpp.git
ARIADNE_LLAMA_BRANCH=master
ARIADNE_LLAMA_REF=<exact-sha-or-ref>
ARIADNE_PATCH_NO_CACHE=1
```

When `ARIADNE_LLAMA_REF` is omitted, the refresh script resolves
`ARIADNE_LLAMA_BRANCH` to an exact SHA automatically.

## Smoke Test

After the patched toolbox is running a `llama-server`, run:

```bash
scripts/llama_patch/smoke-test-logprobs-tools.py \
  --endpoint http://192.168.1.117:1234 \
  --model MiniMax-M2.7-UD-IQ3_S
```

Optional forced tool-call check:

```bash
scripts/llama_patch/smoke-test-logprobs-tools.py \
  --endpoint http://192.168.1.117:1234 \
  --model MiniMax-M2.7-UD-IQ3_S \
  --force-tool-call
```

The smoke test checks that:

- `stream + logprobs` still returns content token logprobs.
- `stream + tools + logprobs` is accepted.
- `logprobs.content` is not attached to non-content deltas.

## Patch Semantics

The patched image applies every `*.patch` file in `patches/`, sorted by file
name.

The server patch intentionally does not claim OpenAI-compatible logprobs for
tool-call delta chunks. It only emits logprobs on visible `delta.content`
chunks. Tool call chunks either omit logprobs or leave them null, avoiding
misleading token telemetry.

The `dry_penalty_last_n` UI patch is a client-side migration, not a server
schema relaxation. Keep the server contract strict and sanitize legacy UI
payloads at the source.

## Versioned Backend Promotion

The patched toolbox image and the production `llama-server` backend are related
but intentionally separate. The toolbox refresh updates the ROCm/runtime image.
The backend manager builds or imports a candidate `llama-server` under:

```bash
${ARIADNE_LLAMA_STORE:-$HOME/.local/opt/ariadne-llama}
```

Production should point at:

```bash
$HOME/.local/opt/ariadne-llama/current/bin/llama-server
```

`current` and `previous` are symlinks. Promotion and rollback are locked and
atomic, so a failed candidate build cannot replace the live backend.

Common operations on the inference box:

```bash
~/models/ariadne-llama-backend.sh status
~/models/ariadne-llama-backend.sh list
~/models/ariadne-llama-backend.sh import-current --promote
~/models/ariadne-llama-backend.sh build --lane main --toolbox llama-rocm-7.14
~/models/ariadne-llama-backend.sh smoke --candidate <build-id> --profile dual --port 1235
~/models/ariadne-llama-backend.sh promote --candidate <build-id>
~/models/ariadne-llama-backend.sh rollback
```

The lanes are:

- `pinned`: exact known-good MTP commit, backed by a cached local source copy.
- `mtp-pr`: floating canary for the current MTP PR branch.
- `main`: upstream llama.cpp `master`, intended for after MTP lands upstream.

The manager does not auto-promote, does not replace `/usr/local/bin/llama-server`,
and does not delete promoted builds. Canary smoke tests run on a separate port
and do not require stopping production.
