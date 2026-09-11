# Antfly Inference — ML Engine & Model Management

## What It Is

Antfly inference is the ML engine inside Antfly. It runs embedding, chunking, reranking, extraction, and generation models in the same process as the database, so enrichers and query processors call it without a network hop. External providers plug into the same interface.

In standalone mode it is served on the API port (8080) under `/ai/v1`. Run as a separate process, `antfly inference run` listens on `127.0.0.1:8090` by default.

## CLI

```
antfly inference list|pull|run|export|convert|quantize
```

(The full subcommand set also includes `embed`, `classify`, `generate`, `chat`, `transcribe`, `read`, `extract`, `compare`, `finetune`, `smoke`, `cuda-info`, `compile-artifact`, `run-artifact`. `cuda-info` dispatches and appears in `--help`, but it is the one subcommand missing from the packaged shell completions.)

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

Models are referenced by full `owner/name`; the `hf:` prefix is accepted. A variant may also be appended to the reference (`BAAI/bge-small-en-v1.5:i8`, `antflydb/clipclap:gguf:Q4_K`).

Other pull options: `--token` (or `HF_TOKEN`), `--tasks`, `--capabilities`, `--projector`, `--models-dir`, `--max-artifact-bytes`, `--max-model-bytes`, `--type`, `--name`, `--ml-dir`, `--file`, `--framework`, `--optimize`, `--dead-leaf-threshold`.

`--ml-dir`, `--type`, `--name`, `--file`, `--framework`, `--optimize`, and `--dead-leaf-threshold` are predictor-only and are rejected on an AI-model pull; `--variants`, `--models-dir`, `--tasks`, `--capabilities`, `--projector`, and the byte caps are rejected on a predictor pull.

### Variants

Variants are free-form strings, not a fixed enum. With no `:variant` on the reference the variant is `auto`. The advertised pull variants are `gguf`, `gguf:Q4_K` (any quant suffix), `onnx`, `hybrid`, and `safetensors`; `f32` and `i8` are still recognized and map onto the ONNX artifact selection. There is no `i4`.

### List

```bash
antfly inference list [models-dir]
```

Takes an optional models-directory positional, which must be the first argument and must not start with `--`. There is no `--remote` flag.

### Run

```bash
antfly inference run --host 127.0.0.1 --port 8090
```

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

Traditional ML predictors live separately under `--ml-dir` / `ANTFLY_INFERENCE_ML_DIR`, discovered as `{ml_dir}/{name}/tabular_model.json`. Unlike the models directory, this one *is* data-root-dependent: a runtime started with a data directory resolves it to `<data-dir>/inference/ml`. `~/.antfly/inference/ml` is the standalone-CLI default (`./ml` when `HOME` is unset), and the `--ml-dir` help text advertises it unconditionally, which is wrong for a server started with `--data-dir`.

## Model Roles

The registry classifies models as `embedder`, `chunker`, `reranker`, `generator`, `recognizer`, `classifier`, `rewriter`, `reader`, `transcriber`, or `extractor`. Multimodal models (text + image + audio) are embedders with multimodal capabilities.

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

Config key for a remote inference endpoint:

```json
{ "inference": { "api_url": "http://127.0.0.1:8090" } }
```

## Kubernetes — InferencePool

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

`spec.image` must provide the `/antfly inference ...` runtime contract. `spec.config` accepts a JSON string merged into the pool's runtime config (`admission`, `prompt_cache`, `kernel_jit`, `keep_alive_ms`, `max_loaded_models`); accelerator backends are selected from `spec.hardware`.

## Sharp Edges

- First request against a model is slow unless `loadingStrategy: eager` preloads it
- `antfly inference list` reads exactly one argument, the first, and only if it does not start with `--`: a flag in that slot consumes it, so `antfly inference list --models-dir /x` silently lists the default directory. `--help` is not handled either
- Bare model names without an owner are rejected on pull
- Generation is limited to a specific set of supported architectures — check before pulling a generator
- Hugging Face predictor pulls accept only safe native formats (`tabular_model.json`, ONNX-ML, XGBoost JSON, LightGBM text); pickle/joblib/skops artifacts are detected and refused
- Model names in index config must match what was downloaded — verify with `antfly inference list`
- For custom ONNX exports, `scripts/export_reranker_to_onnx_static.py` is the one bundled script; otherwise use the `export`, `convert`, and `quantize` subcommands
