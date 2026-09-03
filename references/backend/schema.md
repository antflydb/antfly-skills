# Schema — Tables, JSON Schema, Field Types

## Creating Tables

`POST /db/v1/tables/{tableName}` — the table name lives in the **path**; there is no `name` body field.

Body fields:
- `num_shards` — number of horizontal partitions (1 for dev, higher for production parallelism)
- `indexes` — map of index name → index config (the map key owns the name; see [indexes.md](indexes.md)). Every table gets the default full-text index `full_text_index_v0`: it is added whether `indexes` is omitted, `null`, or an empty `{}`. A plain `full_text` entry you declare yourself is folded into that default rather than creating a second index (artifact-backed full-text entries — those carrying `artifact_name` or `enrichments` — are kept), and index names beginning with `full_text_index` are reserved
- `description` — human-readable description (the spec's `maxLength: 500` is not enforced by the server)
- `schema` — a `TableSchema` object holding `document_schemas`, `default_type`, `enforce_types`, `ttl_field`, `ttl_duration_ns`, `index_sort`, `dynamic_templates`

`TableSchema` details the spec understates:
- `ttl_duration_ns` is the field the implementation reads — an unsigned integer count of **nanoseconds**. The spec's Go-duration string `ttl_duration` is never read
- `index_sort` is an array of `{"field": "...", "order": "asc" | "desc"}`, or `{"field": "...", "desc": true}` — `order` and `desc` on the same entry are rejected, as is an empty array
- `version` is backend-managed and read-only; omit it from create and update requests
- `replication_sources` — Postgres CDC sources (see [integrations.md](integrations.md))

`document_schemas` and `default_type` are **nested under `schema`**, not top-level.

Tables can be created with or without a schema. Without one, documents are schemaless JSON and fields are dynamically inferred. With one, the JSON Schema compiles into full-text field mappings.

## JSON Schema with x-antfly-* Extensions

Antfly extends standard JSON Schema with annotations that control indexing behavior.

### `x-antfly-types` (array)

Compact declaration of how a field is indexed. **This is an array**, not a string.

The validator accepts exactly these names, and **rejects anything else** (`InvalidSchemaUpdateRequest`):

| Type | Purpose |
|------|---------|
| `text` | Full-text searchable (tokenized, stemmed) |
| `keyword` | Exact match, not tokenized |
| `numeric` (also `number`, `integer`) | Numeric range queries |
| `boolean` | Boolean filtering |
| `datetime` | Date/time range queries |
| `html` | HTML content (stripped for indexing) |
| `blob` | Accepted, but the compiler emits no mapping — inert |
| `link` | Reference/link to another document |
| `search_as_you_type` | Autocomplete/prefix matching |
| `string`, `object`, `array`, `null` | Plain JSON Schema type names, accepted here too |

`geopoint`, `geoshape`, and `embedding` are **not** valid `x-antfly-types` values. They are `x-antfly-field` mapping types — declare them there (see below).

A field can carry multiple types: `"x-antfly-types": ["text", "keyword"]` indexes the analyzed text at the field path and an exact variant at `field.keyword`.

### `x-antfly-field` (object)

Fine-grained mapping control on a single property: `type`, `analyzer`, `index`, `store`, `include_in_all`, `sortable`, `missing_null_policy`, and `fields` (named one-level multifields).

`x-antfly-field.type` is the full mapping-type set — it adds `geopoint`, `geoshape`, and `embedding` on top of the `x-antfly-types` names, and accepts JSON-schema-oriented aliases that normalize to the canonical types: `number`/`integer` → `numeric`, `bool` → `boolean`, `date`/`timestamp` → `datetime`, `geo_point` → `geopoint`, `geo_shape` → `geoshape`.

**Sortability comes from a `sortable: true` mapping**, either here or on a `dynamic_templates[].mapping`. `sortable: true` is only accepted on an exact scalar mapping (keyword, numeric/number/integer, boolean/bool, datetime/date/timestamp, link); an `x-antfly-types` shorthand declaration alone is not sortable, and sorting on an undeclared field returns **HTTP 422**. `_id` is always sortable.

```json
{
  "title": {
    "type": "string",
    "x-antfly-field": {
      "type": "text",
      "fields": { "keyword": { "type": "keyword", "sortable": true } }
    }
  }
}
```

Analyzed `text`, `search_as_you_type`, geo, embedding, blob, html, object, and array fields are never directly sortable — sort on an exact scalar subfield such as `title.keyword`.

### `x-antfly-index` (boolean)

Set to `false` to disable indexing for that field. It is a boolean toggle, not a mapping object — use `x-antfly-field` for mapping detail.

### `x-antfly-analyzer` (string)

Analyzer name for the primary text field. Builtins: `standard` (alias `default`), `simple`, `keyword`, `html` (alias `html_analyzer`), `search_as_you_type`, and the language analyzers `german`, `french`, `spanish`, `italian`, `portuguese`, `dutch`, `swedish`, `norwegian`, `danish`, `finnish`. There is no `en` analyzer — English text uses `standard`.

### `x-antfly-include-in-all` (array)

Named on the **object**, listing which of its own properties join the default `_all` search field. Only text-based mappings participate: `text`, `html`, `keyword`, `search_as_you_type`, and `link`. Numeric, boolean, datetime, geo, embedding, and blob fields are never in `_all`.

A bare boolean (`"x-antfly-include-in-all": true`) passes validation but is **silently ignored** — only the array form is consumed.

Nested objects do not inherit the parent's list; each object declares its own. Arrays of objects are the exception: when the array's `items` declares no list of its own, the item's properties are matched against the list declared on the array property itself.

## Example Schema

```json
{
  "num_shards": 3,
  "schema": {
    "document_schemas": {
      "product": {
        "schema": {
          "type": "object",
          "properties": {
            "name": {
              "type": "string",
              "x-antfly-types": ["text", "keyword"]
            },
            "description": {
              "type": "string",
              "x-antfly-types": ["text"]
            },
            "price": {
              "type": "number",
              "x-antfly-field": { "type": "numeric", "sortable": true }
            },
            "category": {
              "type": "string",
              "x-antfly-types": ["keyword"]
            },
            "in_stock": {
              "type": "boolean",
              "x-antfly-types": ["boolean"]
            }
          },
          "x-antfly-include-in-all": ["name", "description"]
        }
      }
    },
    "default_type": "product"
  }
}
```

This schema:
- Makes `name` full-text searchable, with an exact variant at `name.keyword`
- Includes `name` and `description` in default `_all` search
- Enables numeric range queries on `price`, and `order_by` on it because it is declared sortable

## Table Operations

- `GET /db/v1/tables` — list tables; supports `?prefix=`. `?pattern=` is in the spec but rejected with **400** (`unsupported table pattern`)
- `GET /db/v1/tables/{tableName}` — table details (schema, indexes, shard info)
- `DELETE /db/v1/tables/{tableName}` — drop table
- `PUT /db/v1/tables/{tableName}/schema` — update the schema (body is a `TableSchema`)

There is no `PUT` on the table itself — schema changes go through the `/schema` sub-resource.

## Sharp Edges

- `x-antfly-types` is an **array**: `["text"]` not `"text"`, and `geopoint`/`geoshape`/`embedding` belong in `x-antfly-field`, not here
- Table name goes in the URL path; `document_schemas`/`default_type` go under `schema`
- Sortability requires a `sortable: true` mapping — `x-antfly-field` or `dynamic_templates[].mapping`; `_id` is always sortable, otherwise `order_by` returns 422
- `x-antfly-index` is a boolean that turns indexing **off**; mapping detail belongs in `x-antfly-field`
- `x-antfly-include-in-all` is set on the **object**, not on individual fields, and only text-based types can join `_all`
- Tables without indexes still serve `match_all`, filter-only, and `filter_prefix` requests over stored documents; only full-text, semantic, and graph queries need a matching index
- `num_shards` is set at creation, but shard count is not frozen — Antfly supports online shard reallocation via `POST /internal/v1/reallocate` on the metadata service, without downtime
- Schema is optional — schemaless documents work fine and are dynamically inferred, but explicit mappings give type safety and sortability
