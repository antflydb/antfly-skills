# Configuration — Reference

## CLI Flags That Affect Configuration

| Flag | Env var | Default | Description |
|------|---------|---------|-------------|
| `--config <path>` | — | — | Common config file, **JSON only**. No env-var equivalent. |
| `--data-dir <path>` | — | `~/.antfly` | Local data directory root |
| `--secret-store-path <path>` | `ANTFLY_SECRET_STORE_PATH` (`antfly serverless` only) | — | Legacy `secrets.json` path. Repeatable for fallback layers on `standalone`/`metadata`/`data`, which read the flag only; `antfly serverless` takes a single value (last wins). Startup rejects it alongside a config `secrets` section. |
| `--auth <true\|false>` | — | `false` | `standalone`: enable built-in auth (same as `enable_auth`). First start needs `ANTFLY_BOOTSTRAP_ADMIN_PASSWORD`; see `standalone.md` |

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

  "inference": { "keep_alive": "5m", "max_loaded_models": 3 },

  "resources": {
    "inference": { "admission": { "max_concurrent_requests": 8 } }
  },

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
| `cors.allowed_origins` | none | Omitted or empty allows **no** origin. `"*"` must be listed explicitly, and startup rejects `"*"` (or `"null"`) combined with `allow_credentials: true` |
| `enable_auth` | `false` | Built-in users/roles/API keys; `--auth true` is the CLI form |
| `public_inference.enabled` | `false` | Standalone `/ai/v1` execution returns 403 until this is `true`; no CLI flag |
| `pgwire.enabled` | `false` | Optional PostgreSQL wire listener (`bind_host` `127.0.0.1`, `bind_port` 5432, `max_connections` 32). Requires auth (built-in or trusted principal). It has no TLS: a non-loopback bind requires `externally_protected_transport: true` |
| `resources` | — | `memory.max_bytes`; `query`/`write`/`inference` `.admission.max_concurrent_requests` (defaults 32/16/32); `inference.admission.max_work_units`; `inference.memory.max_{host,device,combined,kv,scratch}_bytes`; `inference.request_limits.*`; `query.request_limits.graph.*`. Bytes, not MiB. Unknown fields rejected |
| `hot_standby` | — | Primary/standby replication config (`ha` still read as an alias for one minor release); see `standalone.md` |
| `secrets` | — | Explicit secret sources (`native`, `sources[]`, `environment`); see `secrets.md` |
| `lake_cache` | enabled | Node-local disposable cache for Parquet/Iceberg reads; `root` defaults to `cache/lake-ranges` under local storage. See `storage.md` |
| `log.level` | `info` | `debug` \| `info` \| `warn` \| `error` |
| `log.style` | `terminal` | `terminal` \| `json` \| `logfmt` \| `noop` |
| `inference.api_url` | unset (embedded inference) | Remote `antfly inference run` endpoint. Setting it **disables** embedded inference — standalone keeps no in-process provider, loads no preloads, and serves no `/ai/v1` on its own port |
| `inference.keep_alive` | `"5m"` | Idle-unload duration string; `"0"` disables idle unloading |
| `storage.engine` | `local` | `lite` \| `local` \| `object`; required when the `storage` block is present |
| `storage.local.base_dir` | schema default `antflydb`; unset resolves to `$HOME/.antfly` at runtime | Root directory for local storage |

There is no top-level `s3` block, no `storage.keyvalue`, and no `storage.metadatakv`. Unknown **top-level** keys are generally ignored rather than rejected, with one important exception: removed keys fail config load with an `unsupported config field '<key>'; use '<replacement>'` log line:

| Removed key | Replacement |
|-------------|-------------|
| `admission` | `resources.<query\|write\|inference>.admission` |
| `graph_execution` | `resources.query.request_limits.graph` |
| `memory`, `request_limits`, `max_concurrent_requests` | `resources.inference.*` (memory in bytes) |
| `process_memory_budget_mb` | `resources.memory.max_bytes` (bytes) |
| top-level `models_dir`, `ml_dir`, `preload`, `max_loaded_models`, `keep_alive`, `prompt_cache`, `kernel_jit`, `generation_batching`, `cooperative_execution`, … | `inference.<same key>` |
| `inference.keep_alive_ms` | `inference.keep_alive` (duration string, e.g. `"5m"`; `"0"` disables idle unload) |

`inference.admission`, `inference.memory`, `inference.request_limits`, and `inference.max_concurrent_requests` are rejected the same way. Strict unknown-key rejection applies inside the `storage.*` blocks (`storage` itself — `engine`, `lite`, `local`, `object`, `artifacts` — plus each engine member when selected and each `object.lanes` entry), `resources`, `mcp`, `pgwire`, `public_inference`, `backup`, `connectors`, `lake_cache`, and every `connections.*` sub-block (`inference`, `web_search`, `external_io` and its `credentials`, `cdc`). The `connections` map itself is not strict: connection ids are arbitrary.

## Secret References

Values may use `${secret:key.name}`. Resolution order:

- with a `secrets` config section: `secrets.native`, then each `secrets.sources[]` entry in order, then the environment (unless `secrets.environment: false`);
- without one: each `--secret-store-path` file in command-line order (standalone with no flag uses `<data-dir>/secrets.json`, opened before the config is parsed), then the environment.

The environment variable name is the key uppercased with punctuation replaced by `_`.

`openai.api_key` → `OPENAI_API_KEY`. Confirmed provider mappings: `OPENAI_API_KEY`, `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, `COHERE_API_KEY`.

References also resolve in foreign-source and CDC DSNs supplied in API request bodies, not just in the config file. See `secrets.md`.

## Environment Detection

`KUBERNETES_SERVICE_HOST` is never read. The hot-standby lease API host comes from `ANTFLY_HA_LEASE_API_HOST` (this env name was not renamed with the rest of the standby surface), defaulting to the constant `kubernetes.default.svc`; only the port is taken from the environment, via `KUBERNETES_SERVICE_PORT_HTTPS` and then `KUBERNETES_SERVICE_PORT` — with neither set, lease setup fails rather than defaulting. Nothing in the environment changes log style or any other default.

## Sharp Edges

- Config is **JSON only** — the Zig runtime has no YAML parser
- `storage.engine` is required whenever `storage` is present, and exactly the matching engine member may be set (`lite`/`local`/`object` are mutually exclusive)
- `storage.engine: object` requires `deployment_mode: serverless`; `lite` requires a standalone/embedded topology
- With `lite`, `replication_factor` and `default_shards_per_table` must be 1 and `disable_shard_alloc` must stay `true`
- `max_shard_size_bytes` is inert while `disable_shard_alloc` is `true` (the default)
- `tls` is rejected outright — terminate TLS at a proxy or load balancer
- Pre-0.3 configs carrying `admission`, `graph_execution`, flat inference keys, or `inference.keep_alive_ms` now fail to load — migrate them per the table above
- `cors` with no `allowed_origins` grants no cross-origin access; it is not a wildcard
- Setting `inference.api_url` disables embedded inference in standalone (no in-process provider and no `/ai/v1` on its port) — it is not a fallback
- The Kubernetes operator now lives in Colony, outside the Antfly repo; operator-specific claims in `kubernetes.md` are unverified against it
- Standalone lowers `default_shards_per_table` to 1 — see `standalone.md`
