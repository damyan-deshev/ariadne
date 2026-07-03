# vLLM Strix Halo Qwen3.6 27B Canary

Date: 2026-05-09

Remote box: `deshev@192.168.1.117`

Local Ariadne repo: `/Users/damyandeshev/projects/ariadne`

Remote state directory: `/home/deshev/.local/state/ariadne-vllm`

## Why This Exists

The vLLM lane was explored because the dual llama.cpp profile showed persistent GPU activity from the user's point of view when both resident models were loaded and warmed, especially after the 27B lane received and answered a request. That was the immediate operational trigger.

There was also a strategic reason to keep investigating vLLM: the current llama.cpp daily path depends on a moving MTP PR for Qwen3.6 27B dense speculative decoding. vLLM has a native Qwen MTP path and may eventually be a cleaner inference backend for Ariadne, especially for batching. The narrow question in this canary was:

- Can vLLM run Qwen3.6 27B on Strix Halo with sane memory use?
- Can it preserve the 128k-context target?
- Can it plausibly replace or complement the llama.cpp 27B MTP lane?

Current result: not yet, with the tested Kyuz0 vLLM image. Memory can be made sane with official FP8 weights, but the Qwen3.6 27B FP8 engine does not reach API readiness in this image.

## Runtime Tested

Toolbox:

- `ariadne-vllm`
- image: `docker.io/kyuz0/vllm-therock-gfx1151:stable`
- image id: `4723cfafb369defa1980f5a5ae49757008c1d1da7a751f041cddc428974682b8`
- digest: `sha256:f89c8c689ade28877ade980ba0f29b3142af16c6ebb7f3f285311d38bc81a8a2`
- created: `2026-04-22 08:20:04 UTC`

Versions inside toolbox:

- vLLM: `0.19.2rc1.dev113+g6aa057c9d.d20260422.rocm713`
- Torch: `2.13.0a0+rocm7.13.0a20260422`
- HIP: `7.13.26154`

Model files downloaded:

- `/home/deshev/models/hf/Qwen--Qwen3.6-27B` - 52G, BF16 baseline. This was too heavy for the intended lane.
- `/home/deshev/models/hf/Qwen--Qwen3.6-27B-FP8` - 29G, official FP8 canary.
- `/home/deshev/models/hf/Qwen--Qwen3.6-35B-A3B-FP8` - 35G, downloaded but not tested further in this phase because the relevant pain point is 27B dense.

## Important Memory Finding

The first 27B vLLM run used the BF16 HF checkpoint:

```bash
vllm serve /home/deshev/models/hf/Qwen--Qwen3.6-27B \
  --max-model-len 131072 \
  --gpu-memory-utilization 0.90 \
  --max-num-seqs 1 \
  --dtype auto
```

That was the wrong production-shaped lane for Strix Halo:

- GTT reached about `116,876,005,376 B` (~108.8 GiB).
- Host RAM was around `119 GiB` used.
- Swap started at about `765 MiB`.
- vLLM reported `Available KV cache memory: 54.31 GiB`.
- vLLM reported `GPU KV cache size: 221,872 tokens`.
- It eventually opened API after a long startup, but the machine was memory-pressured and the result is not useful for production decisions.

Interpretation: this was not "just how vLLM works". It was BF16 27B weights plus aggressive KV reservation. It is not comparable to the llama.cpp GGUF daily lane, where the resident footprint was around the 40GB class with GGUF quantization and q8/q8 KV cache.

## FP8 27B Memory Was Sane

The official `Qwen/Qwen3.6-27B-FP8` checkpoint fixed the gross memory shape:

- Model loading reported about `33.27 GiB` model memory.
- GTT stabilized around `36-39 GiB` depending on KV mode and context.
- Swap stayed at `0`.
- Idle GPU after stopping canaries returned to ~`0.28 GiB` GTT and ~5-7W.

This means the memory problem was mostly the BF16 lane selection, not an unavoidable vLLM property.

## FP8 27B Engine Did Not Reach API Readiness

All FP8 27B tests below loaded weights successfully and then stalled before `/v1/models` became reachable.

Common endpoint check:

```bash
curl -fsS http://127.0.0.1:8001/v1/models
```

Common stall point in logs:

```text
Model loading took 33.27 GiB memory
Setting attention block size to ... tokens to ensure that attention page size is >= mamba page size.
Padding mamba page size by 0.13% ...
Using default W8A8 Block FP8 kernel config. Performance might be sub-optimal!
```

The active process then sat CPU-bound in `VLLM::EngineCore`, usually one hot thread, with no GPU work and no API listener.

### Variants Tested

1. `128k`, FP8 weights, FP8 KV, compiled path:

```bash
--max-model-len 131072
--gpu-memory-utilization 0.78
--max-num-seqs 1
--kv-cache-dtype fp8
--calculate-kv-scales
--language-model-only
--enable-prefix-caching
--attention-backend TRITON_ATTN
```

Result:

- GTT around `38.7 GiB`.
- Swap `0`.
- Did not reach API readiness.
- `--calculate-kv-scales` was disabled by vLLM for the hybrid recurrent model; scales defaulted to `1.0`.

Remote logs:

- `/home/deshev/.local/state/ariadne-vllm/server-27b-fp8-128k-nospec.log`
- `/home/deshev/.local/state/ariadne-vllm/server-27b-fp8-128k-nospec.stuck-snapshot.txt`

2. `128k`, FP8 weights, FP8 KV, eager:

```bash
--max-model-len 131072
--gpu-memory-utilization 0.78
--max-num-seqs 1
--kv-cache-dtype fp8
--language-model-only
--enable-prefix-caching
--enforce-eager
--attention-backend TRITON_ATTN
```

Result:

- Model loaded.
- GTT around `36-37 GiB`.
- Swap `0`.
- Did not reach API readiness.

Remote logs:

- `/home/deshev/.local/state/ariadne-vllm/server-27b-fp8-128k-eager-nospec.log`
- `/home/deshev/.local/state/ariadne-vllm/server-27b-fp8-128k-eager-nospec.stuck-snapshot.txt`

3. `32k`, FP8 weights, FP8 KV, eager:

```bash
--max-model-len 32768
--gpu-memory-utilization 0.60
--max-num-seqs 1
--kv-cache-dtype fp8
--language-model-only
--no-enable-prefix-caching
--enforce-eager
--attention-backend TRITON_ATTN
```

Result:

- Same stall point.
- Therefore the stall is not specific to 128k.

Remote logs:

- `/home/deshev/.local/state/ariadne-vllm/server-27b-fp8-32k-eager-nospec.log`
- `/home/deshev/.local/state/ariadne-vllm/server-27b-fp8-32k-eager-nospec.stuck-snapshot.txt`

4. `32k`, FP8 weights, FP8 KV, eager, GDN batching workaround:

```bash
--max-model-len 32768
--gpu-memory-utilization 0.60
--max-num-seqs 1
--max-num-batched-tokens 2096
--kv-cache-dtype fp8
--language-model-only
--no-enable-prefix-caching
--enforce-eager
--attention-backend TRITON_ATTN
```

Result:

- `max_num_batched_tokens=2096` was accepted.
- vLLM log changed to `Chunked prefill is enabled with max_num_batched_tokens=2096`.
- Still stalled at the same model/page sizing stage.

Remote logs:

- `/home/deshev/.local/state/ariadne-vllm/server-27b-fp8-32k-eager-mbt2096.log`
- `/home/deshev/.local/state/ariadne-vllm/server-27b-fp8-32k-eager-mbt2096.stuck-snapshot.txt`

5. `32k`, FP8 weights, KV auto, eager, GDN batching workaround:

```bash
--max-model-len 32768
--gpu-memory-utilization 0.60
--max-num-seqs 1
--max-num-batched-tokens 2096
--language-model-only
--no-enable-prefix-caching
--enforce-eager
--attention-backend TRITON_ATTN
```

Result:

- This removed explicit FP8 KV.
- Attention block size changed from `1568` to `784`.
- Still stalled before API readiness.

Remote logs:

- `/home/deshev/.local/state/ariadne-vllm/server-27b-fp8-32k-eager-kvauto-mbt2096.log`
- `/home/deshev/.local/state/ariadne-vllm/server-27b-fp8-32k-eager-kvauto-mbt2096.stuck-snapshot.txt`

## Process Hygiene Notes

Do process inventory before and after every vLLM run:

```bash
pgrep -af 'vllm serve|VLLM::EngineCore|vllm serve --help'
free -h
rocm-smi --showuse --showmeminfo gtt --showpower
```

Avoid running `vllm serve --help=...` during active canaries in this image. One help invocation spawned many Python helper/import processes and made `htop` misleading. It did not persist after cleanup, but it is a bad habit for this stack.

All canary processes were stopped at the end of this session. Final observed idle state:

- GTT around `280,928,256 B`
- swap `0`
- GPU power around `5-7W`

Production llama.cpp was intentionally left stopped because the user said the vLLM work was more important at the time. Do not assume production is running after this handoff.

## Post-Canary llama.cpp Rollback Smoke

After stopping all vLLM canaries, the llama.cpp dual profile was restarted with:

```bash
cd /home/deshev/models
./run_llama.sh restart-profile dual
```

Result:

- router PID: `59706`
- profile: `dual`
- port: `1234`
- backend: `20260509T010638-pinned-5d5f1b46e4f5-llama-rocm-7.2.2-imported`
- `GPU_MAX_HW_QUEUES=1`
- resident models:
  - `Qwen3.6-27B-MTP-Q6_K`
  - `Qwen3.6-35B-A3B-MTP-UD-Q8_K_XL`

Short OpenAI-compatible smoke requests both succeeded:

| Model | Result | Wall Time | Tokens |
| --- | --- | ---: | ---: |
| `Qwen3.6-27B-MTP-Q6_K` | `I am online.` | 1.32s | 30 prompt / 7 completion |
| `Qwen3.6-35B-A3B-MTP-UD-Q8_K_XL` | `I am online.` | 0.28s | 30 prompt / 5 completion |

The llama.cpp logs showed:

- 27B MTP smoke: `draft acceptance rate = 1.00000 (4 accepted / 4 generated)`
- 35B multimodal lane loaded `mmproj-Qwen3.6-35B-A3B-Q6_K.gguf`
- both child servers returned to `all slots are idle`

Idle polling after the smoke:

- GPU use stayed at `0%` over three 30-second polls.
- power dropped from about `7W` to `5W`.
- GTT stayed around `71.8GB`, which is expected because both models remain resident.
- swap counter showed about `536MiB`, but no active swap pressure was observed during the idle polls.

This smoke did not reproduce the earlier persistent idle-GPU-load symptom in the short window tested. It only validates that the dual profile was restored and both models answer.

## Interpretation

The vLLM direction is not dead, but this exact tested lane is not a daily candidate:

- BF16 27B is too memory-heavy for the desired 128k local lane.
- Official 27B FP8 has sane memory footprint.
- The Kyuz0 `stable` and `latest` tags currently resolve to the same image.
- That image stalls before serving `Qwen/Qwen3.6-27B-FP8`, even at 32k, even with eager mode, even with `max_num_batched_tokens=2096`, and even without explicit FP8 KV.
- The missing gfx1151 W8A8 FP8 kernel config is a performance concern, but the immediate blocker is earlier: API readiness is not reached.

The strongest current hypothesis is not "FP8 is bad". It is:

> This Kyuz0 vLLM/ROCm/TheRock build is not yet a working runtime for Qwen3.6 27B FP8 dense/hybrid on gfx1151.

## Follow-Up Options

Preferred next steps, in order:

1. Test a newer self-built vLLM from upstream source or a newer known-good image, not the current 2026-04-22 Kyuz0 image.
2. Re-test `Qwen/Qwen3.6-27B-FP8` with the minimal documented Qwen/vLLM recipe:
   - `--max-num-batched-tokens 2096`
   - no Ariadne-specific tool parser flags initially
   - no forced FP8 KV initially
   - no forced attention backend initially, unless ROCm chooses a known-bad backend
3. If the model reaches API readiness, then add back:
   - `--kv-cache-dtype fp8`
   - 128k context
   - `--speculative-config '{"method":"qwen3_next_mtp","num_speculative_tokens":2}'`
   - tool calling parser / logprobs / streaming tests for Ariadne.
4. Investigate gfx1151 FP8 kernel config only after API readiness exists. It is likely a speed ceiling, not the current boot blocker.
5. Keep llama.cpp GGUF as the daily 27B lane for now. It is currently the more mature local path on Strix Halo.

## Sources

- vLLM GGUF support is experimental / under-optimized: <https://docs.vllm.ai/en/stable/features/quantization/gguf/>
- vLLM FP8 docs: <https://docs.vllm.ai/en/stable/features/quantization/fp8/>
- vLLM Qwen MTP docs: <https://docs.vllm.ai/en/latest/features/speculative_decoding/mtp/>
- Qwen3.6 27B FP8 model: <https://huggingface.co/Qwen/Qwen3.6-27B-FP8>
- Qwen3.6 35B A3B FP8 model: <https://huggingface.co/Qwen/Qwen3.6-35B-A3B-FP8>
- Hugging Face GGUF docs: <https://huggingface.co/docs/hub/gguf>
- Kyuz0 Strix Halo vLLM toolbox: <https://github.com/kyuz0/amd-strix-halo-vllm-toolboxes>
