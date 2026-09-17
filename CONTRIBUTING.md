# Contributing

Contributions that improve accuracy, clarity, or a reproducible Antfly workflow
are welcome. Open an issue for substantial new Guides or Skills before building
them so maintainers can help settle scope.

## Where changes belong

- `SKILL.md`: the flagship skill and router.
- `references/`: shared backend, frontend, and operations facts.
- `skills/foundations/`: reusable Antfly operations.
- `skills/connectors/`: source setup and verification.
- `skills/harnesses/`: runtime configuration and security boundaries.
- `skills/use-cases/`: outcomes that compose other Skills.
- `guides/`: human-facing playbooks and composition manifests.
- `catalog.yaml`: the canonical inventory; update it when adding packages.
- `schemas/`, `scripts/`, and `tools/`: contracts and validation.

Read [AGENTS.md](AGENTS.md), the selected SKILL.md in full, and
[the taxonomy](docs/taxonomy.md) before changing a package. Keep Skill frontmatter
to `name` and `description`, use verb-led hyphen-case names, and put detailed
variants in one-level references.

## Verify facts

Check factual changes against the current Antfly implementation, not only spec
prose. In your PR, identify the source revision and relevant implementation
paths. Record the tested Antfly and harness versions for runtime claims.
Distinguish static validation from live verification; do not mark a workflow
verified based only on a schema check.

Preserve read-only defaults for retrieval agents, discover current MCP
capabilities instead of fixing tool counts, and never commit credentials or
private source content. Use placeholders in examples.

## Validate locally

Use Python 3.13 and Node.js 22 to match CI:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements-dev.txt
node tools/verify-references.mjs
python3 scripts/validate_library.py
python3 scripts/scan_secrets.py
find skills -type f -name '*.sh' -exec bash -n {} +
```

The reference check above checks known stale tokens and repository paths. To
also check documented endpoints against an Antfly checkout:

```bash
ANTFLY_OPENAPI=/path/to/antfly/openapi.yaml node tools/verify-references.mjs --require-openapi
```

CI fetches the API contract from Antfly's `main` branch. These checks do not
execute the Guide evaluations or prove that a live integration works. For
behavior changes, describe the relevant smoke tests and results in your PR.
The credential scanner checks current files, not Git history.

## Submit a change

Keep the PR focused, explain the user-visible improvement, and include validation
results and any remaining limitations. Use issues for bugs and feature requests;
follow [SECURITY.md](SECURITY.md) for sensitive reports.

Contributions are made under this repository's [MIT license](LICENSE).
