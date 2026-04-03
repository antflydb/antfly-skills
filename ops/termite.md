# Termite — ML Inference Service

## What Termite Is

Termite is Antfly's built-in ML inference service. It runs embedding models, chunkers, and rerankers locally using ONNX Runtime. No external API calls needed.

Enabled by default in swarm mode. Runs on port `11433`.

## Model Management

```bash
# List local models
antfly termite list

# List available models in registry
antfly termite list --remote

# Download models
antfly termite pull BAAI/bge-small-en-v1.5
antfly termite pull mixedbread-ai/mxbai-rerank-base-v1

# Download with quantization
antfly termite pull --variants i8 BAAI/bge-small-en-v1.5

# Multiple models
antfly termite pull --variants i8 \
  BAAI/bge-small-en-v1.5 \
  mixedbread-ai/mxbai-rerank-base-v1

# From HuggingFace
antfly termite pull hf:onnxruntime/Gemma-3-ONNX
```

## Model Types

| Type | Purpose | Examples |
|------|---------|---------|
| Embedders | Generate embedding vectors | bge-small-en-v1.5, mxbai-embed-large-v1 |
| Chunkers | Semantic document splitting | chonky-mmbert-small-multilingual-1 |
| Rerankers | Cross-encoder reranking | mxbai-rerank-base-v1 |
| Multimodal | Image+text embeddings (CLIP) | clip-vit-base-patch32 |

## Model Variants (Quantization)

| Variant | Size | Speed | Accuracy | Recommended |
|---------|------|-------|----------|-------------|
| `f32` | Largest | Slowest | Best | Baseline/testing |
| `f16` | ~50% smaller | Fast | Near-best | GPU inference |
| `i8` | Smallest | Fastest CPU | Good | **Yes — production CPU** |
| `i4` | Tiny | Fastest | Lower | Edge/constrained |

## Storage

Models stored in `~/.termite/models/`:
- `embedders/` — embedding models
- `chunkers/` — chunking models
- `rerankers/` — reranking models

Auto-discovered by Antfly on startup. No config needed — just download and go.

## Running Standalone

```bash
antfly termite run --health-port 4200
```

Or pointed to by Antfly config:
```yaml
termite:
  api_url: "http://127.0.0.1:11433"
```

## Kubernetes — TermitePool CRD

For production ML scaling, the TermitePool CRD manages pools of Termite replicas:

```yaml
apiVersion: antfly.io/v1alpha1
kind: TermitePool
metadata:
  name: embedders
spec:
  workloadType: read-heavy
  image: ghcr.io/antflydb/termite:xla-tpu
  models:
    preload: [{ name: bge-small-en-v1.5, priority: high }]
    loadingStrategy: eager
  replicas:
    min: 2
    max: 8
  hardware:
    accelerator: tpu-v5-lite-podslice
    spot: false
  autoscaling:
    enabled: true
    metrics:
      - type: latency-p99
        target: "100ms"
```

Workload types: `read-heavy` (always-on), `burst` (scale-to-zero with spot).

## Using Termite as an Embedding Provider

In index config, reference Termite as the provider:

```json
{
  "provider": "termite",
  "model": "bge-small-en-v1.5"
}
```

Antfly discovers the model automatically from the local Termite instance.

## Sharp Edges

- First embedding request is slow — model loading happens on demand (unless `eager` loading configured)
- Models are large files — `i8` variant of bge-small-en-v1.5 is ~33MB, `f32` is ~130MB
- Termite on CPU is fine for small-medium workloads; GPU/TPU needed for high throughput
- `--termite=false` on swarm mode disables ML entirely — no embeddings, no chunking, no reranking
- HuggingFace models must be ONNX-exported — not all HF models work. Use `scripts/export_model_to_registry.py` for custom exports.
- Model names in index config must match exactly what's downloaded (check with `antfly termite list`)
