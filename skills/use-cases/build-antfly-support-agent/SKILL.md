---
name: build-antfly-support-agent
description: Design, build, review, or evaluate a documentation and knowledge support agent grounded by Antfly retrieval. Use when implementing support Q&A, choosing semantic versus hybrid retrieval, enforcing evidence and citation rules, defining escalation behavior, selecting an agent harness, or adapting the Antfly support-agent starter applications.
---

# Build an Antfly Support Agent

Use Antfly as the evidence layer while allowing the selected harness to own
conversation, generation, user identity, and business actions.

## Inputs

Collect:

- product and agent names;
- support escalation address;
- table, embeddings index, and chunk text field;
- private source prefix and public documentation base URL;
- selected source connector and agent harness;
- generation provider;
- deployment and audience requirements.

## Workflow

1. Verify ingestion, extraction, chunking, full-text indexing, and embeddings readiness.
2. Test broad semantic and exact-term hybrid retrieval directly in Antfly.
3. Create an instance-scoped read-only key and enforce `references/read-only-policy.json`.
4. Apply the selected harness Skill and keep generation credentials separate.
5. Implement the rules in `references/retrieval-contract.md`.
6. Normalize private source paths into public citations before returning an answer.
7. Run the portable cases in `assets/support-agent-evals.json` and the preserved Claude direct-chunk regression in `assets/claude-code-regression-evals.json`, then add product-specific cases.
8. Measure first-query success, fallback rate, retrieval/generation latency, evidence quality, and citation accuracy separately.
9. Publish only after failure injection and permission-boundary tests pass.

## Starters

Use `antflydb/knowledge-support` for a complete customer-owned knowledge product
or `antflydb/nextjs-support-agent` for a focused Next.js support experience.
Starters implement a UI; this Skill remains the behavior contract.

## Boundaries

- Do not answer required factual questions from model memory.
- Do not expose write/admin Antfly tools to the support agent.
- Do not combine business actions with the Antfly retrieval key.
- Do not treat filenames, links, scores, or metadata without content as evidence.
- Do not claim that one failed query proves the documentation is absent.
