#!/usr/bin/env python3
"""Fail on likely committed credentials while allowing documented placeholders."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKIP_PARTS = {".git", "node_modules", ".venv", "venv"}
PATTERNS = {
    "Antfly Cloud key": re.compile(r"\bantflydb_(?!<|\{|placeholder\b)[A-Za-z0-9_-]{16,}\b"),
    "OpenAI API key": re.compile(r"\bsk-(?!proj-<|<|\{|placeholder\b)[A-Za-z0-9_-]{20,}\b"),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "literal Bearer token": re.compile(r"Authorization\s*[:=]\s*[\"']?Bearer\s+(?!<|\{|\$|antflydb_<)[A-Za-z0-9._-]{20,}"),
}

findings: list[str] = []
for path in ROOT.rglob("*"):
    if not path.is_file() or any(part in SKIP_PARTS for part in path.parts):
        continue
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        continue
    for label, pattern in PATTERNS.items():
        for match in pattern.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            findings.append(f"{path.relative_to(ROOT)}:{line}: possible {label}")

if findings:
    print("Secret scan failed:", file=sys.stderr)
    for finding in findings:
        print(f"- {finding}", file=sys.stderr)
    raise SystemExit(1)

print("No likely credential literals found.")
