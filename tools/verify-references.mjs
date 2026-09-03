#!/usr/bin/env node
/**
 * Verify the skill's factual claims against the Antfly contract.
 *
 * Two layers:
 *  1. Token rules — strings that must not appear (retired names, removed enum
 *     values, nonexistent endpoints/flags) and enum literals that must belong
 *     to their current value sets.
 *  2. Endpoint existence — every /db/v1, /auth/v1, /ai/v1 path mentioned in
 *     the docs must exist in openapi.yaml (path params compared positionally).
 *
 * Usage:
 *   node tools/verify-references.mjs                 # token rules only
 *   ANTFLY_OPENAPI=/path/to/openapi.yaml node tools/verify-references.mjs
 *   node tools/verify-references.mjs --require-openapi   # fail if spec missing (CI)
 */

import { readFileSync, readdirSync, statSync, existsSync } from "node:fs";
import { join, relative } from "node:path";

const ROOT = new URL("..", import.meta.url).pathname;
const requireOpenapi = process.argv.includes("--require-openapi");

// ---------------------------------------------------------------- files
function mdFiles(dir) {
  const out = [];
  for (const name of readdirSync(dir)) {
    if (name === "node_modules" || name.startsWith(".git")) continue;
    const p = join(dir, name);
    const st = statSync(p);
    if (st.isDirectory()) out.push(...mdFiles(p));
    else if (/\.(md|cursorrules|yaml)$/.test(name) || name === ".cursorrules") out.push(p);
  }
  return out;
}
const files = [
  ...mdFiles(ROOT).filter((p) => !p.includes("/tools/")),
];

// ---------------------------------------------------------------- rules
// Each rule: pattern (RegExp, applied per line), message, optional allow
// (RegExp — a line matching allow is exempt, e.g. a "not X" correction).
const forbidden = [
  { pattern: /\/api\/v1/, message: "no /api/v1 base exists — use /db/v1, /auth/v1, or /ai/v1" },
  { pattern: /["'`]aknn["'`]|sync_level:\s*"?aknn/, message: 'sync_level "aknn" was removed — use "full_index"' },
  { pattern: /["'`]provider["'`]\s*:\s*["'`]termite["'`]/, message: 'provider "termite" does not exist — use "antfly"' },
  { pattern: /["'`]provider["'`]\s*:\s*["'`]google["'`]/, message: 'provider "google" does not exist — use "gemini"' },
  { pattern: /antfly\s+termite\b/, message: "the CLI namespace is `antfly inference`" },
  { pattern: /antfly\s+store\b/, message: "the data-node command is `antfly data`" },
  { pattern: /agent\.json/, message: "the A2A card is /.well-known/agent-card.json", allow: /agent-card\.json/ },
  { pattern: /\bRAGResults\b/, message: "the exported component is AnswerResults", allow: /AnswerResults/ },
  { pattern: /linear-merge/, message: "the endpoint path segment is /merge" },
  { pattern: /\/keys\/\{key\}/, message: "key lookup is /db/v1/tables/{tableName}/documents/{key}" },
  { pattern: /ANTFLY_KEYSTORE|antfly\s+keystore\b|keystore password/i, message: "there is no keystore — the secret store is a JSON file via --secret-store-path" },
  { pattern: /antfly:omni|:omni\b/, message: "no :omni image tag is published" },
  { pattern: /\bTermitePool\b/, message: "the CRD kind is InferencePool" },
  { pattern: /\bconjuncts\(|\bdisjuncts\(|\{\s*conjuncts\b|\{\s*disjuncts\b/, message: "SDK helpers are conjunction()/disjunction() (raw query JSON keys conjuncts/disjuncts are fine — this flags the JS helpers)" },
  { pattern: /\bonAnswer\b|\bonFollowUpQuestion\b/, message: "streaming callbacks are onGeneration / onFollowup" },
  { pattern: /--termite\b|--log-level\b|--log-style\b|--keystore-path\b/, message: "flag does not exist on any Antfly runtime" },
  { pattern: /~\/\.termite/, message: "models live under ~/.antfly/inference/models" },
  { pattern: /antfly\s+swarm\b/, message: "the canonical command is `antfly standalone` (swarm is a legacy alias)" },
  { pattern: /\.claude\/settings\.json/, message: "Claude Code MCP config lives in .mcp.json or ~/.claude.json, not .claude/settings.json" },
  { pattern: /"type"\s*:\s*"url"/, message: 'MCP transport type value is "http", not "url"' },
  { pattern: /\bHNSW\b/, message: "dense ANN is HBC (hierarchical balanced clustering), not HNSW" },
  { pattern: /silently returns? (?:nothing|zero results|no results)/i, message: "missing indexes is rejected with HTTP 422, never a silent empty result" },
];

// Enum membership: capture value, must be in set.
const enums = [
  {
    pattern: /sync_level"?\s*[:=]\s*"([a-z_]+)"/gi,
    set: new Set(["propose", "write", "full_text", "enrichments", "full_index"]),
    label: "sync_level",
  },
  {
    pattern: /"provider"\s*:\s*"([a-z_]+)"/g,
    set: new Set(["gemini", "vertex", "ollama", "openai", "openrouter", "bedrock", "anthropic", "cohere", "antfly", "mock"]),
    label: "provider",
  },
];

// A line that explicitly negates the stale token is a correction, not a claim.
const negation =
  /\bnever\b|no longer exists?|removed alias|legacy alias|deprecated alias|there (?:is|are) no\b|does(?:n'| no)t exist|no such\b|not published|servers? rejects?/i;

// ---------------------------------------------------------------- scan
const problems = [];
for (const file of files) {
  const rel = relative(ROOT, file);
  const lines = readFileSync(file, "utf8").split("\n");
  lines.forEach((line, i) => {
    const negated = negation.test(line);
    for (const rule of forbidden) {
      if (rule.pattern.test(line) && !negated && !(rule.allow && rule.allow.test(line))) {
        problems.push(`${rel}:${i + 1}: ${rule.message}\n    ${line.trim()}`);
      }
    }
    for (const en of enums) {
      if (negated) continue;
      for (const m of line.matchAll(en.pattern)) {
        if (!en.set.has(m[1])) {
          problems.push(`${rel}:${i + 1}: ${en.label} "${m[1]}" is not a valid value`);
        }
      }
    }
  });
}

// ---------------------------------------------------------------- endpoints
const specPath = process.env.ANTFLY_OPENAPI;
if (specPath && existsSync(specPath)) {
  const spec = readFileSync(specPath, "utf8");
  const specPaths = new Set();
  for (const m of spec.matchAll(/^ {2}(\/(?:db|auth|ai|ml|extensions)\/v1[^\s:]*):\s*$/gm)) {
    specPaths.add(m[1].replace(/\{[^}]+\}/g, "{}"));
  }
  // Live surfaces that are intentionally outside the OpenAPI contract.
  const specExempt = new Set();
  const pathRe = /(\/(?:db|auth|ai)\/v1\/[A-Za-z0-9_\-.{}/]*[A-Za-z0-9_\-{}])/g;
  // A doc path matches a spec path when every spec `{}` segment absorbs the
  // doc's concrete segment (examples use real values in param positions).
  const segMatch = (specPath, docPath) => {
    const s = specPath.split("/");
    const d = docPath.split("/");
    if (s.length !== d.length) return false;
    return s.every((seg, i) => seg === "{}" || seg === d[i] || d[i].startsWith("{"));
  };
  for (const file of files) {
    const rel = relative(ROOT, file);
    const lines = readFileSync(file, "utf8").split("\n");
    lines.forEach((line, i) => {
      for (const m of line.matchAll(pathRe)) {
        const normalized = m[1].replace(/\{[^}]+\}/g, "{}");
        if (specExempt.has(normalized)) continue;
        // Accept exact/segment-wise spec matches and prefixes of spec paths
        // (docs often name endpoint groups).
        const ok = [...specPaths].some(
          (p) => p === normalized || p.startsWith(normalized + "/") || segMatch(p, normalized),
        );
        if (!ok) problems.push(`${rel}:${i + 1}: endpoint not in openapi.yaml: ${m[1]}`);
      }
    });
  }
  console.log(`endpoint check: compared against ${specPaths.size} spec paths`);
} else if (requireOpenapi) {
  console.error("ANTFLY_OPENAPI not set or file missing; --require-openapi demands it");
  process.exit(2);
} else {
  console.log("endpoint check skipped (set ANTFLY_OPENAPI=/path/to/openapi.yaml)");
}

// ---------------------------------------------------------------- report
if (problems.length) {
  console.error(`\n${problems.length} problem(s):\n`);
  for (const p of problems) console.error("  " + p + "\n");
  process.exit(1);
}
console.log(`ok: ${files.length} files clean`);
