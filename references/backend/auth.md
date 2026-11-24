# Auth — Users, API Keys, Permissions

## Enabling Auth

Auth is off by default (local quickstarts bind to loopback). Enable it with `--auth true` or
`"enable_auth": true`. On first auth-enabled start, set `ANTFLY_BOOTSTRAP_ADMIN_PASSWORD` (12–72 bytes);
it becomes the password of user `admin`. Later starts keep an existing non-default password even if
the variable changes — rotate through the user API. An auth-enabled instance still on the legacy
`admin:admin` credential **refuses to start** until the variable supplies a unique password.

```sh
export ANTFLY_BOOTSTRAP_ADMIN_PASSWORD="$(openssl rand -base64 24)"
antfly standalone --auth true
```

Bootstrap is per node's local auth store, not a cluster-wide password update.

## User Management

`POST /auth/v1/users/{userName}` — create user
`GET /auth/v1/users/{userName}` — get user
`DELETE /auth/v1/users/{userName}` — delete user
`GET /auth/v1/users` — list users
`PUT /auth/v1/users/{userName}/password` — update password
`GET /auth/v1/me` — identity of the calling credential

Users are the identity primitive. Each user can have multiple API keys, a set of permissions, and row filters.

`CreateUserRequest` takes `password` (required) plus optional `initial_policies` (an array of permissions) and `metadata` — so a user *can* be created with permissions in one call. Without `initial_policies`, a new user has none.

`metadata` is trusted server-side auth context that stored row-filter policies can reference through `$auth` paths (e.g. `{"term": {"tenant_id": {"$auth": "metadata.tenant_id"}}}`). `$auth` also accepts `username` and `roles` (the user's inherited role and group subjects, for array-aware operators such as `terms`).

## API Keys

`POST /auth/v1/users/{userName}/api-keys` — create API key
`GET /auth/v1/users/{userName}/api-keys` — list API keys
`DELETE /auth/v1/users/{userName}/api-keys/{keyId}` — delete API key

**Creating a key** returns `key_id`, `key_secret`, and `encoded` — the pre-computed `base64(key_id:key_secret)` ready to paste into the `Authorization` header. The secret is **only shown once**; store it immediately.

`CreateApiKeyRequest` **requires `name`** (a human-readable label). Keys can also be scoped at creation with `permissions` (each must be a subset of the creator's), `row_filter` (table name → filter), and `scoped_row_filters` (`[{ table_target: {database, namespace, table}, filter }]` — a missing `table` targets the whole namespace), and expire via `expires_in` (e.g. `"720h"`). An unscoped key inherits its owner's permissions. Every use re-applies the owner's *current* permissions and row filters plus the key's own restrictions.

**Using a key**: `Authorization: ApiKey base64(key_id:key_secret)`

## Permissions (RBAC)

`GET /auth/v1/users/{userName}/permissions` — list permissions
`POST /auth/v1/users/{userName}/permissions` — add permission
`DELETE /auth/v1/users/{userName}/permissions?resource=&resourceType=` — remove permission (both query params are **required**; they are not path segments)

A permission is an object, not a string:

```json
{ "resource": "orders", "resource_type": "table", "type": "read" }
```

Instead of the literal `resource`, a table permission can carry a structured `table_target`
(`{ "database": "default", "namespace": "public", "table": "orders" }`; omit `table` for every table in
the namespace). Send exactly one of `resource` or `table_target`; `table_target` requires
`resource_type: "table"`.

### Resource Types

| `resource_type` | `resource` means |
|-----------------|------------------|
| `table` | table name, or `*` for all tables |
| `database` / `namespace` / `tablespace` | catalog object name (see the catalog APIs) |
| `graph` | named graph |
| `user` | target username, or `*` |
| `inference` | `*` — grants the unified `/ai/v1` inference routes (standalone also needs `public_inference.enabled`; see [connect.md](connect.md)) |
| `*` | global grant; pair with `resource: "*"` |

There is no `cluster` resource type. A full global grant is `{"resource": "*", "resource_type": "*", "type": "admin"}`.

### Permission Types

- `read` — query, lookup, scan
- `write` — insert, update, delete, batch, merge
- `curator` — read plus native agent-memory curation (proposals, verdicts, entity curation, team pins); not arbitrary writes
- `admin` — create/drop tables, manage indexes, manage users; includes `curator` and `replicate`
- `replicate` — changefeed / PostgreSQL logical-replication export only. Grants no ordinary read or write, and `read`/`write`/`curator` do not imply it. Row policies still apply to exported data

Route authorization is coarse-grained and permission-based; document-level read narrowing is enforced separately by row filters.

## Row Filters

`GET|PUT|DELETE /auth/v1/users/{userName}/row-filters/{table}` (and the `/auth/v1/subjects/{subject}/row-filters/{table}` equivalents for roles and groups).

A row filter is stored query JSON per table name, with `*` as a wildcard entry.

At read time the server:

1. ANDs **every** matching filter — global (`*`), namespace, and table. A table-specific entry
   narrows the wildcard; it never replaces or widens it. A `null` filter adds no restriction and never
   removes a broader one.
2. ANDs across principals: the user's own filters, every inherited role and group, and the API key's
   own filters.
3. Resolves `$auth` references against the authenticated identity (missing or incompatible values
   deny the whole predicate).
4. ANDs the result with the client's own query. Clients can narrow their own results; they cannot
   widen past the stored filters.

Each stored policy is capped at 16,384 nodes and 64 levels of nesting; an effective conjunction over
32,768 JSON values denies the request with 403. Queries, scans, lookups, retrieval-agent queries, and
both sides of a join apply these filters.

## Auth Methods Summary

| Method | Header | Use case |
|--------|--------|----------|
| API Key | `Authorization: ApiKey base64(key_id:key_secret)` | Programmatic access, SDKs |
| Bearer | `Authorization: Bearer base64(key_id:key_secret)` | Same credential, bearer-shaped clients |
| Basic | `Authorization: Basic base64(user:pass)` | Simple auth, dev/testing |
| Trusted principal | `X-Antfly-Trusted-Principal: <HS256 JWT>` | A trusted gateway in front of Antfly |

**Trusted-principal tokens** are accepted only when a verifier is configured: keystore secrets
`antfly.trusted_principal.secret` and `antfly.trusted_principal.issuer` must both be set (one without
the other is a startup config error), and the token's `iss` must match. Claims: `sub` and `exp`
required (`iat` more than 60 s in the future is rejected); `admin: true`, or `operations` granted on
each table in `tables` (all tables when absent); `row_filter` (table or `*` → filter); `metadata` for
`$auth`. Configuring the secret turns auth on.

## CORS

CORS is a browser access policy, not authentication. Enabling CORS with empty `allowed_origins`
grants **no** cross-origin access. List exact trusted origins; `"*"` must be set explicitly and cannot
be combined with credentialed CORS.

## Sharp Edges

1. **API key secret shown once** — if you lose it, delete the key and create a new one. Prefer the `encoded` field over re-deriving the header.
2. **API key header format** — common mistakes are sending just the secret, skipping base64, or omitting the key ID. Format: `ApiKey base64(key_id + ":" + key_secret)`.
3. **Bearer is not OAuth** — it carries the same base64 API-key credential.
4. **Permission delete uses query params** — `?resource=&resourceType=`, both required. A path-segment form is a **404** (no such route); the 400 is what you get on the real route when the query params are missing.
5. **Permissions are objects** — `{resource | table_target, resource_type, type}`. `resource_type` is one of `table`, `database`, `namespace`, `tablespace`, `graph`, `user`, `inference`, `*`; `type` is one of `read`, `write`, `curator`, `admin`, `replicate`.
6. **Grants are additive; row filters only narrow** — every matching `*`, namespace, and table filter is ANDed, across subject, roles, groups, and the API key, and then with the client's query. A per-table entry cannot widen past `*`.
7. **A user created without `initial_policies` can authenticate but do nothing** until permissions are granted.
8. **Legacy `admin:admin` blocks startup** — set `ANTFLY_BOOTSTRAP_ADMIN_PASSWORD` before upgrading an auth-enabled instance.
