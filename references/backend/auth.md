# Auth — Users, API Keys, Permissions

## User Management

`POST /auth/v1/users/{userName}` — create user
`GET /auth/v1/users/{userName}` — get user
`DELETE /auth/v1/users/{userName}` — delete user
`GET /auth/v1/users` — list users
`PUT /auth/v1/users/{userName}/password` — update password
`GET /auth/v1/me` — identity of the calling credential

Users are the identity primitive. Each user can have multiple API keys, a set of permissions, and row filters.

`CreateUserRequest` takes `password` (required) plus optional `initial_policies` (an array of permissions) and `metadata` — so a user *can* be created with permissions in one call. Without `initial_policies`, a new user has none.

`metadata` is trusted server-side auth context that stored row-filter policies can reference through `$auth` paths (e.g. `{"term": {"tenant_id": {"$auth": "metadata.tenant_id"}}}`).

## API Keys

`POST /auth/v1/users/{userName}/api-keys` — create API key
`GET /auth/v1/users/{userName}/api-keys` — list API keys
`DELETE /auth/v1/users/{userName}/api-keys/{keyId}` — delete API key

**Creating a key** returns `key_id`, `key_secret`, and `encoded` — the pre-computed `base64(key_id:key_secret)` ready to paste into the `Authorization` header. The secret is **only shown once**; store it immediately.

`CreateApiKeyRequest` **requires `name`** (a human-readable label). Keys can also be scoped at creation with `permissions` (each must be a subset of the creator's) and `row_filter`, and expire via `expires_in` (e.g. `"720h"`). An unscoped key inherits its owner's permissions.

**Using a key**: `Authorization: ApiKey base64(key_id:key_secret)`

## Permissions (RBAC)

`GET /auth/v1/users/{userName}/permissions` — list permissions
`POST /auth/v1/users/{userName}/permissions` — add permission
`DELETE /auth/v1/users/{userName}/permissions?resource=&resourceType=` — remove permission (both query params are **required**; they are not path segments)

A permission is an object, not a string:

```json
{ "resource": "orders", "resource_type": "table", "type": "read" }
```

### Resource Types

| `resource_type` | `resource` means |
|-----------------|------------------|
| `table` | table name, or `*` for all tables |
| `user` | target username, or `*` |
| `inference` | `*` — grants the unified `/ai/v1` inference routes |
| `*` | global grant; pair with `resource: "*"` |

There is no `cluster` resource type. A full global grant is `{"resource": "*", "resource_type": "*", "type": "admin"}`.

### Permission Types

- `read` — query, lookup, scan
- `write` — insert, update, delete, batch, merge
- `admin` — create/drop tables, manage indexes, manage users

Route authorization is coarse-grained and permission-based; document-level read narrowing is enforced separately by row filters.

## Row Filters

`GET|PUT|DELETE /auth/v1/users/{userName}/row-filters/{table}` (and the `/auth/v1/subjects/{subject}/row-filters/{table}` equivalents for roles and groups).

A row filter is stored query JSON per table name, with `*` as a wildcard entry.

**Selection is first-match on the exact table name, with `*` only as a fallback.** A table-specific filter therefore *replaces* the wildcard for that table rather than combining with it — and can be **wider** than the wildcard. Granting a table its own entry is a way to widen access relative to `*`, so treat a per-table entry as the complete policy for that table.

Conjunction (`{"conjuncts": [a, b]}`) applies only between filters that resolve to the same table key:
- entries for the same table coming from the user's own subject, its roles, and its groups are conjoined together (the `*` entries likewise conjoin with each other)
- the owner's resolved filter for a table is conjoined with the API key's own filter for that table

At read time the server resolves `$auth` references in the selected filter and conjoins it with the client's own `filter_query`. Clients can narrow their own results; they cannot widen past the stored filter.

## Auth Methods Summary

| Method | Header | Use case |
|--------|--------|----------|
| API Key | `Authorization: ApiKey base64(key_id:key_secret)` | Programmatic access, SDKs |
| Bearer | `Authorization: Bearer base64(key_id:key_secret)` | Same credential, bearer-shaped clients |
| Basic | `Authorization: Basic base64(user:pass)` | Simple auth, dev/testing |

## Sharp Edges

1. **API key secret shown once** — if you lose it, delete the key and create a new one. Prefer the `encoded` field over re-deriving the header.
2. **API key header format** — common mistakes are sending just the secret, skipping base64, or omitting the key ID. Format: `ApiKey base64(key_id + ":" + key_secret)`.
3. **Bearer is not OAuth** — it carries the same base64 API-key credential.
4. **Permission delete uses query params** — `?resource=&resourceType=`, both required. A path-segment form is a **404** (no such route); the 400 is what you get on the real route when the query params are missing.
5. **Permissions are objects** — `{resource, resource_type, type}`. `resource_type` is one of `table`, `user`, `inference`, `*`.
6. **Grants are additive; row filters resolve per table, then conjoin** — a table-specific filter replaces the `*` wildcard for that table and can be wider than it, so `*` is a fallback, not a floor. Conjunction happens only among same-table entries: across subject/role/group, and across the owner and API-key layers. Against the client's own `filter_query`, the resolved filter can only narrow.
7. **A user created without `initial_policies` can authenticate but do nothing** until permissions are granted.
