# Auth — Users, API Keys, Permissions

## User Management

`POST /api/v1/users/{userName}` — create user
`GET /api/v1/users/{userName}` — get user
`PUT /api/v1/users/{userName}/password` — update password

Users are the identity primitive. Each user can have multiple API keys and a set of permissions.

The default admin user has full access to everything. Created users start with **no permissions** — you must explicitly grant them.

## API Keys

`POST /api/v1/users/{userName}/api-keys` — create API key
`GET /api/v1/users/{userName}/api-keys` — list API keys
`DELETE /api/v1/users/{userName}/api-keys/{keyId}` — delete API key

**Creating a key** returns both `key_id` and `key_secret`. The secret is **only shown once** — it cannot be retrieved later. Store it immediately.

**Using a key**: `Authorization: ApiKey base64(keyID:keySecret)`

The header value is the string `ApiKey ` followed by base64 encoding of `keyID:keySecret` (colon-joined, then base64).

## Permissions (RBAC)

`GET /api/v1/users/{userName}/permissions` — list permissions
`POST /api/v1/users/{userName}/permissions` — add permission
`DELETE /api/v1/users/{userName}/permissions/{resource}/{resourceType}` — remove permission

### Resource Scoping

| Resource | Scope |
|----------|-------|
| `table:*` | All tables |
| `table:products` | Specific table |
| `cluster:*` | Cluster-level operations |

### Permission Types

- `read` — query, lookup, search
- `write` — insert, update, delete, batch, linear merge
- `admin` — create/drop tables, manage indexes, manage users

Permissions are additive. A user with `read` on `table:products` and `write` on `table:orders` can search products and write to orders.

## Auth Methods Summary

| Method | Header | Use case |
|--------|--------|----------|
| API Key | `Authorization: ApiKey base64(keyID:keySecret)` | Programmatic access, SDKs |
| Bearer | `Authorization: Bearer <token>` | OAuth tokens |
| Basic | `Authorization: Basic base64(user:pass)` | Simple auth, dev/testing |
| OAuth 2.0 | Standard OAuth flow | Cloud web apps |

## Sharp Edges

1. **API key secret shown once** — if you lose it, delete the key and create a new one.
2. **New users have zero permissions** — they can authenticate but can't do anything until permissions are granted.
3. **API key header format** — common mistake is to send just the secret, or forget to base64 encode, or forget to include the keyId. Format: `ApiKey base64(keyID + ":" + keySecret)`.
4. **Permission changes are immediate** — no cache delay. But existing connections may need to re-authenticate.
5. **Default admin** has implicit full access — cannot be restricted via RBAC.
