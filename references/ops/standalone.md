# Standalone — Local Development & Single-Node

## Starting Standalone

```bash
antfly standalone
```

Runs metadata, data, the public API, and in-process inference in a single process.
`antfly swarm` is a deprecated legacy alias for the same command.

### Core Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--id` | `1` | Local node id |
| `--host` | `127.0.0.1` | Public API bind host |
| `--port` | `8080` | Public API bind port |
| `--health-port` | `4200` | Dedicated health/metrics port on `--host` |
| `--health <true\|false>` | `true` | Enable the health/metrics server |
| `--config <file>` | — | Common config file, **JSON only** |
| `--data-dir <path>` | `~/.antfly` | Local Antfly data directory root |
| `--secret-store-path <path>` | — | Legacy `secrets.json` path; repeat for fallback layers (not with a config `secrets` section) |
| `--auth <true\|false>` | `false` | Built-in authentication (same as `enable_auth`) |
| `--admin-token-env <name>` | — | Require `Authorization: Bearer` from this env var on admin and hot-standby APIs |
| `--models-dir` / `--ml-dir` | `~/.antfly/inference/{models,ml}` | Embedded inference model / traditional-ML directories |
| `--process-memory-budget-mb <n>` | `0` (cgroup, else host) | Whole-process memory envelope shared by storage, caches, and inference (`ANTFLY_PROCESS_MEMORY_BUDGET_MB`) |
| `--preload-model <kind:name\|kind:backend:name>` | — | Preload and warm a model before serving; repeatable, replaces the config preload list |
| `--storage-engine lite --storage-path <f.aflite>` | — | Serve a Lite file instead of a data directory (`--fsync <bool>`, default `true`) |

`antfly standalone --help` lists the rest: `--hot-standby-*` replication flags (the `--ha-*` spellings are deprecated aliases for one minor release), per-inference-budget overrides (`--inference-{host,backend,combined,kv,scratch}-budget-mb`), `--kernel-jit-mode`, `--experimental` (A2A), ARD catalog flags, `--control-tick-ms`, and replica/snapshot/extension roots.

### Ports

Standalone binds **two** ports by default: the API port (8080) and the health port (4200).
In-process inference is served on the API port — there is no separate inference listener.
`/healthz` and `/readyz` are served on both ports; `/metrics` is health-port only.

A third listener is opt-in: `{"pgwire": {"enabled": true}}` starts a PostgreSQL wire listener on `127.0.0.1:5432` (`bind_host`, `bind_port`, `max_connections` default 32). It refuses to start without authentication (built-in `enable_auth` or a trusted-principal verifier) and has no TLS, so a non-loopback `bind_host` additionally requires `externally_protected_transport: true` with a TLS proxy or private transport in front.

`12380` (data API), `9017` (metadata raft), and `9021` (data raft) are conventional distributed-mode ports used in examples, not runtime defaults. Started by hand, `antfly data` defaults `--api-port` and `--raft-port` to `0` — an OS-assigned ephemeral port — and `antfly metadata` does the same unless the port for its node id can be read out of `metadata.raft_urls` / `metadata.orchestration_urls` in a config file. Standalone binds none of them.

A separate inference server (`antfly inference run`) defaults to `127.0.0.1:8090` (`--host` / `--port`).

### Standalone Defaults

- `default_shards_per_table = 1` (schema default in other modes: 3)
- `disable_shard_alloc = true` (global default — auto-split/merge is off)
- No CORS middleware unless the config carries a `cors` block; inside one, `enabled` defaults to `true`, but an omitted or empty `allowed_origins` allows **no** origin. `"*"` must be listed explicitly and is rejected at startup together with `allow_credentials: true`
- Public `/ai/v1` execution is off: it returns 403 until the config sets `{"public_inference": {"enabled": true}}` (no CLI flag). Internal indexing and query-time inference need no opt-in
- Authentication is off (`--auth false`)
- `replication_factor` schema default is 3 (min 1, max 5); set `1` explicitly for a single node

### Data Directory Layout

`--data-dir` (default `~/.antfly`) is the root of all durable local state:

```text
<data-dir>/
  ANTFLY_FORMAT
  secrets.json
  cache/      lake-ranges/   (disposable Parquet/Iceberg read cache)
  metadata/   replicas, catalog.txt, snapshots, auth, local-metadata.json
  data/       replicas, catalog.txt, snapshots
  standby/    primary.wal, slots, log.wal, progress.wal, fence.wal   (only with hot standby)
```

Inference files are not under the data directory, and `--data-dir` never moves them. Models resolve
to `--models-dir`, else `$ANTFLY_INFERENCE_MODELS_DIR`, else `$HOME/.antfly/inference/models`, else
`./models`; traditional-ML predictors to `--ml-dir`, else `$ANTFLY_INFERENCE_ML_DIR`, else
`$HOME/.antfly/inference/ml`, else `./ml`.

Pre-0.3 nodes kept hot-standby state under `ha/` (`standby.wal`, `standby-progress.wal`). A 0.3 server
whose `--hot-standby-*` flags point into a not-yet-existing `standby/` renames a sibling `ha/` once at
startup (and the two WAL files to `log.wal` / `progress.wal`).

Delete the directory to start fresh.

### With Config File

```bash
antfly standalone --config config.json
```

```json
{
  "replication_factor": 1,
  "default_shards_per_table": 1,
  "log": { "level": "debug", "style": "terminal" },
  "cors": {
    "enabled": true,
    "allowed_origins": ["http://localhost:3000"]
  },
  "public_inference": { "enabled": true }
}
```

Add `"inference": { "api_url": "http://127.0.0.1:8090" }` only to send all `provider: antfly` work to a separate `antfly inference run` process — it turns embedded inference off rather than acting as a fallback.

## Authentication

```bash
export ANTFLY_BOOTSTRAP_ADMIN_PASSWORD="$(openssl rand -base64 24)"   # store it safely
antfly standalone --auth true
```

- `--auth true` or `"enable_auth": true` enables users, roles, and API keys. The admin user is `admin`.
- The first auth-enabled start requires `ANTFLY_BOOTSTRAP_ADMIN_PASSWORD` (12–72 bytes); later starts keep the stored password even if the variable changes — rotate through the user-management API.
- An auth-enabled instance still holding the legacy `admin:admin` credential **refuses to start** until the variable supplies a new password.
- Built-in TLS is rejected (`tls` config fails startup). Keep listeners on loopback until auth is on and TLS terminates at a trusted reverse proxy.
- A configured trusted-principal verifier (`antfly.trusted_principal.*`, see `secrets.md`) also makes public requests require auth, independently of `enable_auth`.

## Hot Standby

Availability for standalone is a WAL-streaming hot standby: a primary (`--hot-standby-primary-log`, `--hot-standby-primary-slots`, `--hot-standby-fence-wal`, …) streams to read-only standbys (`--hot-standby-log`, `--hot-standby-progress`, `--hot-standby-upstream-url`, `--hot-standby-slot`, …), or configure the same through the `hot_standby` config section (`ha` still read).

- `hot_standby.sync.mode`: `async` | `remote-write` (default) | `remote-apply`; `hot_standby.sync.failure`: `block` (default) | `fail-closed` | `degrade-to-async`.
- `antfly standby <status|slot|seed|fence|promote|rejoin|follow|switchover|stream|commit|artifact>` targets a running node via `--admin-url` / `ANTFLY_STANDBY_ADMIN_URL`, or local files via `--data-dir`. `antfly ha` is a hidden deprecated alias.
- `antfly standby switchover --to <standby-admin-url>` is the planned, zero-loss handover (fence old primary, promote standby, repoint followers) and the online upgrade path; `antfly standby follow` repoints a standby without restart. Promotion is explicit and fenced.
- Admin API: `/admin/v1/standby/...` plus `/standby/v1/health` and `/standby/v1/ready`. `/admin/v1/ha/...`, `/ha/v1/*`, `ANTFLY_HA_ADMIN_URL`, and `ANTFLY_HA_ADMIN_TOKEN` (preferred: `ANTFLY_STANDBY_ADMIN_TOKEN`) remain aliases for one minor release, scheduled for removal in 0.4.
- No point-in-time recovery or WAL archive — keep taking backups alongside a standby.

## Lite Files

`antfly lite <init|status|info|batch|lookup|scan|query|index|enrichment|schema|run-until-idle|backup|export|snapshot|restore|import|promote|check|compact|vacuum>` manages single-file `.aflite` databases in-process. One writer handle at a time (file locking required), no replication.

`antfly standalone --storage-engine lite --storage-path app.aflite` serves a Lite file over HTTP. Direct adoption takes only the file's `default` table with its schema, full-text indexes, and supported enrichments; dense, sparse, graph, and algebraic indexes are rejected before adoption — use `antfly lite promote app.aflite --target <url> --table <t> --connection <c> --location <uri>` instead. Upstream: `docs/guides/lite.mdx`, `docs/guides/deployment-options.mdx`.

## Backup, Restore, and Upgrades

Backups go through a named connection with `backup.write` / `restore.read` capabilities:

```json
{ "connections": { "archive-writer": {
  "kind": "external_io", "capabilities": ["backup.write", "restore.read"],
  "external_io": { "protocol": "filesystem", "root": "/" } } } }
```

```bash
antfly backup --table docs --backup-id docs-2026 --connection archive-writer \
  --format portable --location file:///var/backups/antfly --url http://127.0.0.1:8080
antfly backup inspect --input docs.afb      # offline JSON report
antfly restore ...            # see `antfly restore --help`
```

`--format portable` is required for anything Lite must read. Moves between Lite, standalone, and other deployments are always logical backup/restore; storage-engine files (text indexes, vector segments) are rebuilt on the target.

Upgrades:

- A new release may migrate table files in place, and that can be one-way — an older binary may then fail with `InvalidTableFile`. Take and verify a portable backup first; roll back by restoring into a fresh data directory, never by swapping the binary back onto a directory a newer release opened.
- Enabling new catalog features can make state unreadable by older binaries: cascade decisions require reader epoch 30 and agreement guards epoch 31.
- For standalone with a standby, `antfly standby switchover` is the online upgrade path.

## Open-File Limits

Standalone checks `RLIMIT_NOFILE` at startup: below 256 it refuses to start; below 65536 it logs a warning. In Docker use `--ulimit nofile=65536:65536`.

## Distributed Roles

```bash
antfly metadata --id 1 --raft-host 0.0.0.0 --raft-port 9017 \
  --api-host 0.0.0.0 --api-port 12377 \
  --cluster '{"1":{"raft_url":"http://node1:9017","orchestration_url":"http://node1:12377"}}'

antfly data --node-id 1 --store-id 1 \
  --api-host 0.0.0.0 --api-port 12380 \
  --raft-host 0.0.0.0 --raft-port 9021 \
  --metadata-api http://node1:12377
```

- `antfly metadata`: `--id`, `--raft-host`, `--raft-port`, `--api-host`, `--api-port`, `--cluster`
- `antfly data`: `--node-id`, `--store-id`, `--raft-host`, `--raft-port`, `--api-host`, `--api-port`, `--metadata-api` (repeatable)
- Metadata node count must be odd — any odd count works; 1, 3, or 5 are the practical choices

There is no `antfly store` command.

## Install

```bash
curl -fsSL https://releases.antfly.io/antfly/latest/install.sh | sh     # or: ... | sh -s -- <version>
brew install antflydb/taps/antfly                                       # macOS/Linux
```

- Linux archives: unsuffixed archives are portable CPU-only musl builds; `_gnu` archives (glibc ≥ 2.28) are required for CUDA and for the `libantfly` C ABI. No native Windows archives — use the container image or WSL2.
- The `antfly` archive holds the CLI plus `lib/libantfly` and `include/antfly.h`. The separate `antfly-embedded` archive is library-only (no executable).
- npm `@antfly/cli` repackages the same native archive (published for stable releases). A PyPI `antfly-cli` package exists but PyPI publication is currently disabled for every release channel.
- The shell installer uses `/usr/local` for root and `$HOME/.local` for user installs.

## CLI Agent Mode

Remote client commands (`query`, `sql`, `schema`, `lookup`, `table`, `index`, `backup`, …) share an agent output contract. Selection precedence: `--agent` / `--no-agent`; then `ANTFLY_AGENT_MODE=1|0`; then a non-false `CODEX_THREAD_ID`, `CLAUDECODE`, `CURSOR_AGENT`, or `CLINE_ACTIVE` **combined with stdout being a pipe or file**; else human tables. `--output auto|json|compact|table` picks the format (`json`/`compact` keep the original result shape). `antfly capabilities` describes the contract. Server startup, `lite`, `standby`, and `inference` keep their own interfaces and reject these options. Upstream: `docs/reference/cli-agent-mode.md`.

## Build & Run (Development)

The server is a Zig binary.

```bash
make build      # outputs ./antfly at the repo root
./antfly standalone
```

There is no `cmd/antfly` Go package and no `./bin` output directory.

## Sharp Edges

- `--config` is JSON only — a YAML file is rejected regardless of extension
- Default bind host is `127.0.0.1`; pass `--host 0.0.0.0` to accept off-host traffic
- `disable_shard_alloc` defaults to `true`, so tables do not auto-split until you set it to `false`
- Log level/style are config keys (`log.level`, `log.style`) — there are no `--log-level` / `--log-style` flags
- Inference models download on first use — the first embedding request can be slow
- CORS is off until you add a `cors` block; even then no origin is allowed until you list it in `allowed_origins`
- `/ai/v1` returns 403 until `public_inference.enabled` is `true`
- Setting `inference.api_url` disables embedded inference entirely
- `RLIMIT_NOFILE` below 256 is a startup failure
