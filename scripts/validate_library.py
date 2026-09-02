#!/usr/bin/env python3
"""Validate Antfly Guide, Skill, and catalog contracts."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import jsonschema
import yaml


ROOT = Path(__file__).resolve().parents[1]
NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
errors: list[str] = []


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def fail(path: Path, message: str) -> None:
    errors.append(f"{relative(path)}: {message}")


def load_yaml(path: Path):
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        fail(path, f"invalid YAML: {exc}")
        return None


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        fail(path, f"invalid JSON: {exc}")
        return None


def load_frontmatter(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n(.*)\Z", text, re.DOTALL)
    if not match:
        fail(path, "missing or unterminated YAML frontmatter")
        return {}, text
    try:
        values = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError as exc:
        fail(path, f"invalid frontmatter YAML: {exc}")
        return {}, match.group(2)
    if not isinstance(values, dict):
        fail(path, "frontmatter must be a mapping")
        return {}, match.group(2)
    return values, match.group(2)


skill_files = sorted((ROOT / "skills").glob("*/*/SKILL.md"))
skill_names: set[str] = set()
skill_paths: set[str] = set()

if not skill_files:
    errors.append("skills: no skills found")

for skill_file in skill_files:
    values, body = load_frontmatter(skill_file)
    if set(values) != {"name", "description"}:
        fail(skill_file, "frontmatter must contain only name and description")

    name = values.get("name", "")
    description = values.get("description", "")
    if not isinstance(name, str) or not NAME.fullmatch(name) or len(name) >= 64:
        fail(skill_file, "invalid skill name")
    if name != skill_file.parent.name:
        fail(skill_file, "skill name must match directory")
    if not isinstance(description, str) or len(description) < 40:
        fail(skill_file, "description is too short to trigger reliably")
    if name in skill_names:
        fail(skill_file, "duplicate skill name")
    skill_names.add(name)
    skill_paths.add(relative(skill_file.parent))

    if "TODO" in body:
        fail(skill_file, "contains an unresolved TODO")
    if len(skill_file.read_text(encoding="utf-8").splitlines()) > 500:
        fail(skill_file, "SKILL.md exceeds 500 lines")

    openai = skill_file.parent / "agents" / "openai.yaml"
    if not openai.exists():
        fail(skill_file, "missing agents/openai.yaml")
    else:
        interface = load_yaml(openai)
        default_prompt = (interface or {}).get("interface", {}).get("default_prompt", "")
        if f"${name}" not in default_prompt:
            fail(openai, "default prompt must mention the skill")

    for resource in sorted(skill_file.parent.rglob("*")):
        if not resource.is_file() or resource == skill_file or resource == openai:
            continue
        resource_path = resource.relative_to(skill_file.parent).as_posix()
        if resource_path not in body and resource.name not in body:
            fail(resource, "resource is not named in SKILL.md")

catalog_path = ROOT / "catalog.yaml"
catalog = load_yaml(catalog_path)
if not isinstance(catalog, dict):
    fail(catalog_path, "catalog must be a mapping")
    catalog = {}

catalog_skill_paths: set[str] = set()
skill_groups = catalog.get("skills", {})
if not isinstance(skill_groups, dict):
    fail(catalog_path, "skills must be a mapping of categories")
else:
    for category, paths in skill_groups.items():
        if not isinstance(paths, list):
            fail(catalog_path, f"skills.{category} must be a list")
            continue
        for value in paths:
            if not isinstance(value, str):
                fail(catalog_path, f"skills.{category} contains a non-string path")
                continue
            catalog_skill_paths.add(value)
            if not (ROOT / value / "SKILL.md").is_file():
                fail(catalog_path, f"unknown skill path {value}")

for path in sorted(skill_paths - catalog_skill_paths):
    fail(catalog_path, f"missing skill path {path}")
for path in sorted(catalog_skill_paths - skill_paths):
    fail(catalog_path, f"unknown skill path {path}")

guide_schema_path = ROOT / "schemas" / "guide.schema.json"
guide_schema = load_json(guide_schema_path)
catalog_guides = catalog.get("guides", [])
catalog_manifest_paths: set[str] = set()
if not isinstance(catalog_guides, list):
    fail(catalog_path, "guides must be a list")
else:
    for entry in catalog_guides:
        if not isinstance(entry, dict) or not isinstance(entry.get("manifest"), str):
            fail(catalog_path, "every Guide entry needs a manifest path")
            continue
        manifest_path = entry["manifest"]
        catalog_manifest_paths.add(manifest_path)
        if not (ROOT / manifest_path).is_file():
            fail(catalog_path, f"Guide manifest does not exist: {manifest_path}")

disk_manifests = {relative(path) for path in (ROOT / "guides").glob("*/guide.yaml")}
for path in sorted(disk_manifests - catalog_manifest_paths):
    fail(catalog_path, f"missing Guide manifest {path}")
for path in sorted(catalog_manifest_paths & disk_manifests):
    manifest_path = ROOT / path
    manifest = load_yaml(manifest_path)
    if manifest is None or guide_schema is None:
        continue
    try:
        jsonschema.Draft202012Validator(guide_schema, format_checker=jsonschema.FormatChecker()).validate(manifest)
    except jsonschema.ValidationError as exc:
        fail(manifest_path, f"schema violation at {'/'.join(str(p) for p in exc.path) or '<root>'}: {exc.message}")
    if manifest.get("id") != manifest_path.parent.name:
        fail(manifest_path, "id must match Guide directory")
    if not (manifest_path.parent / "guide.md").is_file():
        fail(manifest_path, "missing human-facing guide.md")
    selected = manifest.get("skills", {})
    for names in selected.values() if isinstance(selected, dict) else []:
        for name in names if isinstance(names, list) else []:
            if name not in skill_names:
                fail(manifest_path, f"references unknown skill {name}")
    policy = manifest.get("security", {}).get("tool_policy")
    if isinstance(policy, str) and not (ROOT / policy).is_file():
        fail(manifest_path, f"tool policy does not exist: {policy}")
    for evaluation in manifest.get("evaluations", []):
        if isinstance(evaluation, str) and not (ROOT / evaluation).is_file():
            fail(manifest_path, f"evaluation file does not exist: {evaluation}")

for path in sorted(ROOT.glob("schemas/*.json")) + sorted(ROOT.glob("skills/**/*.json")):
    load_json(path)

if errors:
    print("Library validation failed:", file=sys.stderr)
    for error in errors:
        print(f"- {error}", file=sys.stderr)
    raise SystemExit(1)

guide_count = len(catalog_manifest_paths)
print(f"Validated {len(skill_files)} skills and {guide_count} guide(s).")
