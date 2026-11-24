# Antfly Inference — ML Engine & Model Management

## What It Is

Antfly inference is the ML engine inside Antfly. It runs embedding, chunking, reranking, extraction, and generation models in the same process as the database, so enrichers and query processors call it without a network hop. External providers plug into the same interface.

In standalone mode it is served on the API port (8080) under `/ai/v1` (and `/ml/v1` for traditional-ML predictors). Public `/ai/v1` execution returns **403** until the config sets `{"public_inference": {"enabled": true}}`; internal indexing and query-time inference need no opt-in.

- A CPU-only build runs models inside the database process. A build with a GPU/driver backend (Metal — on by default on macOS — CUDA, or PJRT) starts a supervised `antfly inference _worker` child and sends **all** embedded inference to it, so a wedged driver call is killed and respawned without taking the database down.
- Setting `inference.api_url` **disables** embedded inference: standalone keeps no in-process provider, loads no preloads, serves no `/ai/v1` on its own port, and sends every `provider: antfly` call to that URL.
- Run as a separate process, `antfly inference run` listens on `127.0.0.1:8090` by default and refuses a non-loopback `--host` unless `--allow-insecure-public-bind` is passed (it has no built-in auth or TLS).
- CUDA requires the `_gnu` (glibc ≥ 2.28) Linux build or the container image; the unsuffixed Linux archives are CPU-only musl builds.

## CLI

```
antfly inference list|pull|run|export|convert|quantize
```

(The full subcommand set also includes `embed`, `classify`, `rerank`, `decisions`, `generate`, `chat`, `transcribe`, `read`, `extract`, `compare`, `finetune`, `smoke`, `cuda-info`, `metal-info`, `bench-cuda`, `compile-artifact`, `run-artifact`, `a4b-pack`, `quant-kernel-codegen`, and `version`; all appear in the packaged shell completions.)

### Pull

```
antfly inference pull [--variants <csv>] <model-ref>...
```

```bash
antfly inference pull BAAI/bge-small-en-v1.5
antfly inference pull --variants i8 BAAI/bge-small-en-v1.5
antfly inference pull hf:mixedbread-ai/mxbai-rerank-base-v1
antfly inference pull --variants i8 \
  BAAI/bge-small-en-v1.5 \
  mixedbread-ai/mxbai-rerank-base-v1
```

Models are referenced by full `owner/name`; the `hf:` prefix is accepted. A variant may also be appended to the reference (`BAAI/bge-small-en-v1.5:i8`, `antflydb/clipclap:gguf:Q4_K`), and a Hub revision with `@` (`BAAI/bge-m3@main`, `BAAI/bge-m3:onnx@<commit>`; default `main`). Each pull resolves the revision to one immutable commit. `--projector` (GGUF sidecar) defaults to `auto`; it also takes `none`, a quant suffix, or a filename.

Other pull options: `--token` (or `HF_TOKEN`), `--tasks`, `--capabilities`, `--projector`, `--models-dir`, `--max-artifact-bytes`, `--max-model-bytes`, `--type`, `--name`, `--ml-dir`, `--file`, `--framework`, `--optimize`, `--dead-leaf-threshold`.

`--ml-dir`, `--type`, `--name`, `--file`, `--framework`, `--optimize`, and `--dead-leaf-threshold` are predictor-only and are rejected on an AI-model pull; `--variants`, `--models-dir`, `--tasks`, `--capabilities`, `--projector`, and the byte caps are rejected on a predictor pull.

### Variants

Variants are free-form strings, not a fixed enum. With no `:variant` on the reference the variant is `auto`. The advertised pull variants are `gguf`, `gguf:Q4_K` (any quant suffix), `onnx`, `hybrid`, and `safetensors`; `f32` and `i8` are still recognized and map onto the ONNX artifact selection. There is no `i4`.

### List

```bash
antfly inference list [models-dir]
antfly inference list --models-dir /models
```

Takes the models directory either as one positional or via `--models-dir` (not both, not twice). Any other `--` flag is an `InvalidArguments` error. There is no `--remote` flag.

### Run

```bash
antfly inference run --host 127.0.0.1 --port 8090 --config inference.json \
  --preload-model embedder:BAAI/bge-small-en-v1.5
```

`--config` reads model settings under `inference` and resource policy under `resources`; flat keys and `keep_alive_ms` are rejected at startup:

```json
{
  "resources": { "inference": { "admission": { "max_concurrent_requests": 8 } } },
  "inference": { "models_dir": "/models", "keep_alive": "60s", "max_loaded_models": 3 }
}
```

CLI flags override config regardless of order; one or more `--preload-model kind:name` (or `kind:backend:name`) flags **replace** the config preload list. Client-only `inference.api_url` / `api_key` are accepted and ignored by the server.

## Capacity and Memory

- **Admission**: `resources.inference.admission.max_concurrent_requests` (default 32; `--max-concurrent-requests`; 0 disables) and `max_work_units` (`--max-work-units`). Requests are never queued: exhaustion returns `503` with `Retry-After: 1` and `retryable: true`. Standalone shares one budget across enrichment, query calls, `/ai/v1`, and `/ml/v1`.
- **Residency**: `inference.max_loaded_models` (default 10; 0 unlimited), LRU idle eviction, `inference.keep_alive` (default `"5m"`; `"0"` disables idle unload).
- **Memory**: one process envelope shared with storage and caches — `--process-memory-budget-mb` / `ANTFLY_PROCESS_MEMORY_BUDGET_MB` on `standalone` or `inference run`, else the cgroup limit, else host memory. Set it below the container limit in Burstable pods. Per-class ceilings in bytes under `resources.inference.memory.max_{host,device,combined,kv,scratch}_bytes` (CLI overrides `--{host,backend,combined,kv,scratch}-budget-mb` on `inference run`, `--inference-*-budget-mb` on `standalone`). A request that can never fit returns `MODEL_RESOURCE_LIMIT`; transient pressure returns retryable `MODEL_RESOURCE_BUSY`.
- **Request ceilings**: `resources.inference.request_limits.{max_items_per_request,max_input_tokens_per_item,max_output_tokens_per_item,max_decoded_pixels_per_batch}`.
- **Metrics**: `/ml/v1/metrics` on the inference listener exposes `antfly_inference_generation_*` (active/queued gauges, queue rejections, `queue_wait_seconds`, `first_content_seconds`, `prefill_seconds`, `decode_seconds`), `antfly_inference_cuda_managed_{live,peak,limit}_bytes`, and `antfly_inference_admission_{host,backend}_{weight,kv,scratch}_bytes`.

## Model Storage

Default: `$ANTFLY_INFERENCE_MODELS_DIR`, else `$HOME/.antfly/inference/models`, else `./models` when `HOME` is unset; `--models-dir` overrides all three. Model discovery is deliberately independent of the database data root, so `--data-dir` never moves it.

A variant-less (`auto`) pull installs flat at `owner/name`:

```text
~/.antfly/inference/models/
  BAAI/bge-small-en-v1.5/
  mixedbread-ai/mxbai-rerank-base-v1/
  openai/clip-vit-base-patch32/
```

An explicit variant gets its own leaf directory instead — `{models_dir}/{owner}/{name}--antfly-{first 16 hex characters of sha256(variant)}`. So `--variants i8 BAAI/bge-small-en-v1.5`, which pulls the reference `BAAI/bge-small-en-v1.5:i8`, lands beside `BAAI/bge-small-en-v1.5/` rather than inside it.

Legacy per-task subdirectories (`embedders/`, `chunkers/`, `rerankers/`, …) are still discovered.

Traditional ML predictors live separately under `--ml-dir`, else `$ANTFLY_INFERENCE_ML_DIR`, else `$HOME/.antfly/inference/ml`, else `./ml` — discovered as `{ml_dir}/{name}/tabular_model.json`. Like the models directory, it is independent of `--data-dir`.

## Model Roles

The registry classifies models as `embedder`, `chunker`, `reranker`, `generator`, `classifier`, `rewriter`, `reader`, `transcriber`, or `extractor` (there is no `recognizer` role; GLiNER-style entity models are `extractor`). Multimodal models (text + image + audio) are embedders with multimodal capabilities.

Verified example models:
- `BAAI/bge-small-en-v1.5` — embedder
- `mixedbread-ai/mxbai-rerank-base-v1` — reranker
- `openai/clip-vit-base-patch32` — multimodal embedder

Chunker `model` is an open string defaulting to `"fixed"`; `/ai/v1/models` advertises the built-in `fixed_bert` and `fixed_bpe` chunkers, which need no download. Sizing parameters nest under `text`: `text.target_tokens`, `text.overlap_tokens`.

## Using Antfly Inference as a Provider

The provider name in index and query configs is `antfly`:

```json
{ "provider": "antfly", "model": "BAAI/bge-small-en-v1.5" }
```

```json
{ "provider": "antfly", "model": "mixedbread-ai/mxbai-rerank-base-v1", "field": "body" }
```

```json
{ "provider": "antfly", "model": "fixed_bert", "text": { "target_tokens": 512, "overlap_tokens": 50 } }
```

Config key for a remote inference endpoint (this turns embedded inference off — it is not a fallback):

```json
{ "inference": { "api_url": "http://127.0.0.1:8090" } }
```

## Kubernetes — InferencePool

> **Unverified:** `InferencePool` is a Kubernetes operator CRD, and the operator moved to Colony (Antfly commit `871c143788`). The spec below reflects the operator as of Antfly `ab8d9fc119`. What the Antfly repo still documents: Colony's operator emits the canonical nested runtime config for every pool, so pools and the operator must be upgraded together to a compatible runtime.

```yaml
apiVersion: antfly.io/v1alpha1
kind: InferencePool
metadata:
  name: embedders
spec:
  workloadType: read-heavy        # read-heavy | write-heavy | burst | general
  image: ghcr.io/antflydb/antfly:latest
  models:
    preload:
      - name: BAAI/bge-small-en-v1.5:i8
        tasks: ["embed"]
        priority: high            # high | medium | low
    loadingStrategy: eager        # eager | lazy | bounded
  replicas:
    min: 2
    max: 8
  hardware:
    accelerator: tpu-v5-lite-podslice
    spot: false
  autoscaling:
    enabled: true
    metrics:
      - type: latency-p99         # queue-depth | latency-p99 | latency-p95 |
                                  # requests-per-second | cpu | memory | throughput
        target: "100ms"
```

`spec.image` must provide the `/antfly inference ...` runtime contract; accelerator backends are selected from `spec.hardware`. Whatever `spec.config` carries must use the current runtime shape — model settings nested under `inference` (`prompt_cache`, `kernel_jit`, `keep_alive` as a duration string, `max_loaded_models`, `preload`) and limits under `resources.inference` (`admission`, `memory`, `request_limits`). The runtime rejects the old flat keys and `keep_alive_ms`; there is no legacy fallback. For eager preloads, give each model a recognized task (`tasks: [embed]`, `tasks: [generate]`) or an explicit `kind`.

## Sharp Edges

- First request against a model is slow unless `loadingStrategy: eager` preloads it
- `antfly inference list` errors on any flag other than `--models-dir`, including `--help`
- `antfly inference run --host 0.0.0.0` refuses to start without `--allow-insecure-public-bind`
- Standalone `/ai/v1` is 403 until `public_inference.enabled: true`
- Bare model names without an owner are rejected on pull
- Generation is limited to a specific set of supported architectures — check before pulling a generator
- Hugging Face predictor pulls accept only safe native formats (`tabular_model.json`, ONNX-ML, XGBoost JSON, LightGBM text); pickle/joblib/skops artifacts are detected and refused
- Model names in index config must match what was downloaded — verify with `antfly inference list`
- For custom ONNX exports, `scripts/export_reranker_to_onnx_static.py` is the one bundled script; otherwise use the `export`, `convert`, and `quantize` subcommands
