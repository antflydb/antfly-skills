# Schema — Tables, JSON Schema, Field Types

## Creating Tables

`POST /api/v1/tables` with body:
- `name` (required) — table name
- `num_shards` — number of horizontal partitions (1 for dev, higher for production parallelism)
- `indexes` — map of index name → index config (see [indexes.md](indexes.md))
- `description` — human-readable description
- `document_schemas` — named JSON Schema definitions for document types
- `default_type` — which document schema to use by default

Tables can be created with or without a schema. Without a schema, documents are schemaless JSON. With a schema, the JSON Schema maps automatically to full-text index field mappings.

## JSON Schema with x-antfly-* Extensions

Antfly extends standard JSON Schema with custom annotations that control indexing behavior.

### `x-antfly-types` (array)

Declares how a field should be indexed. **This is an array**, not a string.

Available types:
| Type | Purpose |
|------|---------|
| `text` | Full-text searchable (tokenized, stemmed) |
| `keyword` | Exact match, not tokenized. Required for facets. |
| `numeric` | Numeric range queries and sorting |
| `boolean` | Boolean filtering |
| `datetime` | Date/time range queries |
| `geopoint` | Geographic point for distance queries |
| `embedding` | Vector field |
| `html` | HTML content (stripped for indexing) |
| `blob` | Binary data (stored, not indexed) |
| `link` | Reference/link to another document |
| `search_as_you_type` | Autocomplete/prefix matching |

A field can have multiple types: `"x-antfly-types": ["text", "keyword"]` makes it both full-text searchable and facetable.

### `x-antfly-include-in-all` (array)

Lists fields that should be included in the default full-text search (when no specific field is targeted in a query). Defined at the object level, not field level.

### `x-antfly-index`

Field-level index directives for fine-grained control over how a specific field is indexed.

## Example Schema

```json
{
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
            "x-antfly-types": ["numeric"]
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
```

This schema:
- Makes `name` both full-text searchable and exact-match filterable
- Makes `category` facetable (keyword only)
- Includes `name` and `description` in default search
- Enables numeric range queries on `price`

## Table Operations

- `GET /api/v1/tables` — list all tables
- `GET /api/v1/tables/{name}` — get table details (schema, indexes, shard info)
- `DELETE /api/v1/tables/{name}` — drop table
- `PUT /api/v1/tables/{name}` — update table (schema, description)

## Sharp Edges

- `x-antfly-types` is an **array**: `["text"]` not `"text"`
- Tables without indexes can store documents but cannot be searched
- `num_shards` is set at creation and cannot be changed later (resharding is a separate operation)
- `keyword` type is required for facets — `text` type alone won't work for aggregations
- `x-antfly-include-in-all` is set on the **object**, not on individual fields
- Schema is optional — unstructured documents work fine, but full-text index mappings won't be auto-generated without it
