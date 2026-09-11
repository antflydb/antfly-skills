# Configuration — Reference

## CLI Flags That Affect Configuration

| Flag | Env var | Default | Description |
|------|---------|---------|-------------|
| `--config <path>` | — | — | Common config file, **JSON only**. No env-var equivalent. |
| `--data-dir <path>` | — | `~/.antfly` | Local data directory root |
| `--secret-store-path <path>` | `ANTFLY_SECRET_STORE_PATH` (`antfly serverless` only) | — | `secrets.json` path. Repeatable for fallback layers on `standalone`/`metadata`/`data`, which read the flag only; `antfly serverless` takes a single value (last wins). |

There are no `--log-level` / `--log-style` flags and no `ANTFLY_LOG_*` environment variables. Logging is configured under the `log` key.

## Config File Structure

```json
{
  "metadata": {
    "orchestration_urls": {
      "1": "http://127.0.0.1:12377",
      "2": "http://127.0.0.1:12378",
      "3": "http://127.0.0.1:12379"
    }
  },
  "replication_factor": 3,
  "max_shards_per_table": 20,
  "max_shard_size_bytes": 67108864,
  "disable_shard_alloc": true,

  "log": { "level": "info", "style": "json" },

  "cors": {
    "enabled": true,
    "allowed_origins": ["https://app.example.com"]
  },

  "inference": { "api_url": "http://127.0.0.1:8090" },

  "storage": {
    "engine": "local",
    "local": { "base_dir": "antflydb" }
  }
}
```

`metadata` also accepts `raft_urls` with the same node-id → URL shape.

## Key Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `replication_factor` | schema default 3 (min 1, max 5) | Schema-only today: the Zig runtime reads it solely to reject a non-1 value under `lite`, and no code places replicas from it |
| `max_shards_per_table` | 20 | Max shards per table |
| `max_shard_size_bytes` | 67108864 (64 MiB) | Auto-split threshold; only applies when `disable_shard_alloc` is `false` |
| `default_shards_per_table` | 3; 1 in `standalone` and `embedded` | Consumed nowhere in the Zig runtime beyond the `lite` non-1 rejection |
| `disable_shard_alloc` | `true` | Disables automatic shard split/merge |
| `deployment_mode` | `distributed` | `embedded` \| `distributed` \| `standalone` \| `serverless`; must match the command |
| `health_enabled` | `true` | Health/metrics server |
| `health_port` | 4200 | Health/metrics port |
| `cors.enabled` | `true` *within a `cors` block* | With no `cors` block in the config, no CORS middleware is installed at all |
| `cors.allowed_origins` | `["*"]` | Applied when omitted or empty and `enabled` is true |
| `log.level` | `info` | `debug` \| `info` \| `warn` \| `error` |
| `log.style` | `terminal` | `terminal` \| `json` \| `logfmt` \| `noop` |
| `inference.api_url` | required when `inference` is present | Antfly inference endpoint |
| `storage.engine` | `local` | `lite` \| `local` \| `object`; required when the `storage` block is present |
| `storage.local.base_dir` | schema default `antflydb`; unset resolves to `$HOME/.antfly` at runtime | Root directory for local storage |

There is no top-level `s3` block, no `storage.keyvalue`, and no `storage.metadatakv`. Unknown **top-level** keys are silently ignored rather than rejected; strict unknown-key rejection applies inside the `storage.*` blocks (`storage` itself plus `lite`, `local`, `object`, and each `object.lanes` entry — each engine member checked only when that engine is the selected one), the `admission` and `mcp` blocks, and every `connections.*` sub-block (`inference`, `web_search`, `external_io` and its `credentials`, `cdc`). The `connections` map itself is not strict: connection ids are arbitrary.

## Secret References

Values may use `${secret:key.name}`. Resolution order:

1. each `--secret-store-path` file, in command-line order;
2. the environment variable named by uppercasing the key and replacing punctuation with `_`.

`openai.api_key` → `OPENAI_API_KEY`. Confirmed provider mappings: `OPENAI_API_KEY`, `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, `COHERE_API_KEY`.

References also resolve in foreign-source and CDC DSNs supplied in API request bodies, not just in the config file. See `secrets.md`.

## Environment Detection

`KUBERNETES_SERVICE_HOST` is never read. The HA lease API host comes from `ANTFLY_HA_LEASE_API_HOST`, defaulting to the constant `kubernetes.default.svc`; only the port is taken from the environment, via `KUBERNETES_SERVICE_PORT_HTTPS` and then `KUBERNETES_SERVICE_PORT` — with neither set, HA lease setup fails rather than defaulting. Nothing in the environment changes log style or any other default.

## Sharp Edges

- Config is **JSON only** — the Zig runtime has no YAML parser
- `storage.engine` is required whenever `storage` is present, and exactly the matching engine member may be set (`lite`/`local`/`object` are mutually exclusive)
- `storage.engine: object` requires `deployment_mode: serverless`; `lite` requires a standalone/embedded topology
- With `lite`, `replication_factor` and `default_shards_per_table` must be 1 and `disable_shard_alloc` must stay `true`
- `max_shard_size_bytes` is inert while `disable_shard_alloc` is `true` (the default)
- `tls` is rejected outright — terminate TLS at a proxy or load balancer
- `spec.metadataNodes.replicas` is immutable after cluster creation in the operator — plan the metadata replica count ahead; see `kubernetes.md`
- Standalone lowers `default_shards_per_table` to 1 — see `standalone.md`
