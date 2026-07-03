# llama.cpp ROCm gfx1151 Dual-Resident Idle Workaround

Date: 2026-05-09

Remote box: `deshev@192.168.1.117`

Runtime profile under test:

- `run_llama.sh restart-profile dual`
- backend: `/home/deshev/.local/opt/ariadne-llama/current/bin/llama-server`
- build: `20260509T010638-pinned-5d5f1b46e4f5-llama-rocm-7.2.2-imported`
- host kernel: `7.0.4-100.fc43.x86_64`
- ROCm toolbox: `llama-rocm-7.2.2`
- models:
  - `Qwen3.6-27B-MTP-Q6_K`
  - `Qwen3.6-35B-A3B-MTP-UD-Q8_K_XL`
- `CTX=131072`, `MODELS_MAX=2`, KV cache `q8_0/q8_0`

## Problem

With both Qwen3.6 models resident in the router, the GPU stayed at `100%`
activity and high clocks while llama.cpp reported all slots idle. Single-model
resident runs idled correctly. The problem reproduced after model load and
after real requests.

The behavior matches the family of ROCm/HIP idle-queue bugs discussed in:

- llama.cpp issue: <https://github.com/ggml-org/llama.cpp/issues/20482>
- ROCm issue: <https://github.com/ROCm/ROCm/issues/5706>
- amdgpu module parameter docs:
  <https://www.kernel.org/doc/html/next/gpu/amdgpu/module-parameters.html>

## Boot Safety Check

Before testing boot parameters, the LUKS auto-unlock path was checked.

Findings:

- root is on `luks-3a3507c1-9dc4-47f4-bdc0-924082e7c33a`
- current and previous boots show `clevis-luks-askpass` unlocking the root
  device successfully in initramfs
- the LUKS2 Clevis token is TPM2-bound with `pcr_bank=sha256` and `pcr_ids=7`
- prior kernel changes had already survived the auto-unlock path

No LUKS, `rd.luks`, `amd_iommu`, `amdgpu.gttsize`, or `ttm.pages_limit`
parameters were changed.

## Tested Paths

### Kernel/firmware update

The host was upgraded from Fedora kernel `6.19.11-200.fc43` to
`7.0.4-100.fc43`, with firmware packages updated to `20260410`.

Result:

- single 27B resident idle became quiet
- single 35B resident idle remained quiet
- dual resident still burned at idle

### `amdgpu.uni_mes=0`

`amdgpu.uni_mes=0` was added temporarily with `grubby`, rebooted, verified via
`/proc/cmdline` and `/sys/module/amdgpu/parameters/uni_mes`, then removed after
testing.

Result:

- boot and clevis auto-unlock worked
- dual resident still burned at idle without queue limiting
- performance was not better than the final no-boot-param path
- the parameter was removed; current boot is back to default `uni_mes=1`

### Runtime environment matrix

Dual profile was restarted repeatedly under `amdgpu.uni_mes=0` with these
environment variants:

| Case | Result |
| --- | --- |
| default | bad, `sclk 2900MHz` |
| `GPU_MAX_HW_QUEUES=1` | good, `sclk 600MHz` |
| `ROCBLAS_USE_HIPBLASLT=0` | bad, `sclk 2900MHz` |
| `GPU_MAX_HW_QUEUES=1 ROCBLAS_USE_HIPBLASLT=0` | good, `sclk 600MHz` |
| `HSA_ENABLE_SDMA=0` | bad, `sclk 2900MHz` |
| `HSA_ENABLE_SDMA=0 GPU_MAX_HW_QUEUES=1` | good, `sclk 600MHz` |
| reversed preload order | bad, `sclk 2900MHz` |

Conclusion: the meaningful knob is `GPU_MAX_HW_QUEUES=1`.

The same `GPU_MAX_HW_QUEUES=1` test was then repeated after removing
`amdgpu.uni_mes=0` and rebooting back to default `uni_mes=1`.

Result:

- both models loaded
- child processes inherited `GPU_MAX_HW_QUEUES=1`
- idle stayed at `GPU use 0%`, `sclk 600MHz`, around `5-8W`

## Performance Results

Harness prompt:

- LogHub-based Apache/HDFS/OpenSSH context
- `90348` prompt characters
- `47311` prompt tokens
- `max_tokens=160`
- `temperature=0`
- strict JSON instruction; `json_ok=false` in these runs because the output
  budget was too small for the requested schema, not because of the idle fix

Raw result files on the box:

- `/home/deshev/.local/state/ariadne-llama-bench/results/20260509T125535-dual-uni-mes0-e2e.json`
- `/home/deshev/.local/state/ariadne-llama-bench/results/20260509T131428-dual-uni-mes0-queues1-e2e.json`
- `/home/deshev/.local/state/ariadne-llama-bench/results/20260509T132949-dual-default-unimes1-queues1-e2e.json`
- `/home/deshev/.local/state/ariadne-llama-bench/results/20260509T125901-dual-uni-mes0-idle-env-matrix.jsonl`

Comparable long-prompt results:

| Runtime | Mode | Model | Wall | Prompt tok/s | Decode tok/s | MTP acceptance |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| `uni_mes=0`, no queue limit | sequential | 27B MTP | 245.51s | 202.09 | 14.12 | 78.23% |
| `uni_mes=0`, no queue limit | sequential | 35B | 99.50s | 502.08 | 30.84 | n/a |
| `uni_mes=0`, no queue limit | parallel | 27B MTP | 321.65s | 154.58 | 10.29 | 78.23% |
| `uni_mes=0`, no queue limit | parallel | 35B | 342.82s | 140.15 | 30.64 | n/a |
| `uni_mes=0`, `GPU_MAX_HW_QUEUES=1` | sequential | 27B MTP | 244.88s | 202.69 | 14.02 | 78.23% |
| `uni_mes=0`, `GPU_MAX_HW_QUEUES=1` | sequential | 35B | 100.08s | 499.20 | 30.48 | n/a |
| `uni_mes=0`, `GPU_MAX_HW_QUEUES=1` | parallel | 27B MTP | 324.81s | 153.09 | 10.17 | 78.23% |
| `uni_mes=0`, `GPU_MAX_HW_QUEUES=1` | parallel | 35B | 340.22s | 141.26 | 30.45 | n/a |
| default `uni_mes=1`, `GPU_MAX_HW_QUEUES=1` | sequential | 27B MTP | 245.70s | 202.00 | 14.05 | 78.23% |
| default `uni_mes=1`, `GPU_MAX_HW_QUEUES=1` | sequential | 35B | 100.47s | 497.12 | 30.38 | n/a |
| default `uni_mes=1`, `GPU_MAX_HW_QUEUES=1` | parallel | 27B MTP | 326.59s | 152.24 | 10.14 | 78.23% |
| default `uni_mes=1`, `GPU_MAX_HW_QUEUES=1` | parallel | 35B | 341.93s | 140.55 | 30.40 | n/a |

Interpretation:

- `GPU_MAX_HW_QUEUES=1` fixes the dual-resident idle burn.
- No boot scheduler parameter is needed.
- The queue limit did not produce a meaningful additional throughput regression
  in the long-prompt A/B runs.
- The long-prompt numbers are lower than earlier shorter-prompt tests, so do
  not compare them directly against the old 22k-token run as a performance
  regression claim.

## Implemented Runtime Change

`/home/deshev/models/run_llama.sh` now defaults llama launches to:

```bash
GPU_MAX_HW_QUEUES=1
```

The change is scoped to llama-server startup:

- inherited by router and child model processes
- shown in human status as `GPU_MAX_HW_QUEUES: 1`
- shown in JSON status as `llama_rocm_gpu_max_hw_queues`
- logged on startup

Override behavior:

```bash
# use another queue count
LLAMA_ROCM_GPU_MAX_HW_QUEUES=2 ./run_llama.sh restart-profile dual

# disable the wrapper setting and use ROCm default/inherited environment
LLAMA_ROCM_GPU_MAX_HW_QUEUES= ./run_llama.sh restart-profile dual
```

Remote backup:

```text
/home/deshev/models/run_llama.sh.bak.20260509-133149-before-gpu-queues
```

## Current Expected State

After:

```bash
cd /home/deshev/models
./run_llama.sh restart-profile dual
```

Expected:

- both Qwen3.6 models loaded
- `GPU_MAX_HW_QUEUES=1` visible in both child process environments
- `rocm-smi` idle samples around:
  - `GPU use (%): 0`
  - `sclk clock level: 0: (600Mhz)`
  - `Current Socket Graphics Package Power`: roughly `5-8W`

If the issue returns after a future ROCm/kernel/llama.cpp refresh, retest this
matrix before changing boot parameters again.
