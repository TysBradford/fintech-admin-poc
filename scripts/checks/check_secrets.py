"""Fail when credential-like material or a real env file is about to be committed."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from common import (
    Finding,
    build_parser,
    is_text_file,
    read_lines,
    relative,
    report,
    resolve_files,
)

SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("private key block", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY")),
    ("AWS access key id", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b")),
    ("Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b")),
    ("Stripe key", re.compile(r"\b[sr]k_(?:live|test)_[A-Za-z0-9]{16,}\b")),
    (
        "JSON Web Token",
        re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    ),
    (
        "connection string with embedded password",
        re.compile(r"\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|amqp)://[^:\s/]+:[^@\s]+@"),
    ),
    (
        "hard-coded credential assignment",
        re.compile(
            r"(?i)\b(?:api[_-]?key|secret(?:[_-]?key)?|client[_-]?secret|password|passwd|"
            r"auth[_-]?token|access[_-]?token|private[_-]?key)\b\s*[:=]\s*[\"'][^\"'\s]{12,}[\"']"
        ),
    ),
]

PLACEHOLDER = re.compile(
    r"(?i)(?:^\s*$|<[^>]+>|\$\{[^}]+\}|\bchange[-_ ]?me\b|\bplaceholder\b|\bexample\b|"
    r"\bdummy\b|\byour[-_ ]|xxx+|\*{3,}|\.{3})"
)

ENV_FILE = re.compile(r"(^|/)\.env(\..+)?$")
ENV_KEY_VALUE = re.compile(r"^\s*(?:export\s+)?([A-Z0-9_]+)\s*=\s*(.*)$")
ENV_SAFE_VALUE = re.compile(
    r"^(?:|\"\"|''|https?://localhost[:/].*|demo|development|test|true|false|\d+)$"
)
ENV_SENSITIVE_KEY = re.compile(r"(?i)(secret|token|password|passwd|key|credential)")


def _looks_like_placeholder(line: str, match: re.Match[str]) -> bool:
    value = match.group(0)
    return bool(PLACEHOLDER.search(value)) or "pragma: allowlist secret" in line


def scan_file(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    rel = relative(path)

    if ENV_FILE.search(rel) and not rel.endswith(".env.example"):
        return [
            Finding(
                path,
                0,
                "real environment file must not be committed (only .env.example is allowed)",
            )
        ]

    if not is_text_file(path):
        return findings

    lines = read_lines(path)
    if rel.endswith(".env.example"):
        for number, line in enumerate(lines, start=1):
            kv = ENV_KEY_VALUE.match(line)
            if (
                kv
                and ENV_SENSITIVE_KEY.search(kv.group(1))
                and not ENV_SAFE_VALUE.match(kv.group(2).strip())
            ):
                findings.append(
                    Finding(path, number, f"{kv.group(1)} in .env.example must be left empty")
                )
        return findings

    for number, line in enumerate(lines, start=1):
        for label, pattern in SECRET_PATTERNS:
            match = pattern.search(line)
            if match and not _looks_like_placeholder(line, match):
                findings.append(Finding(path, number, f"possible {label}"))
                break
    return findings


def main(argv: list[str] | None = None) -> int:
    args = build_parser(__doc__ or "").parse_args(argv)
    findings = [f for path in resolve_files(args) for f in scan_file(path)]
    return report(
        "secrets",
        findings,
        "Remove the credential, rotate it if it was ever real, and read configuration via "
        "backend/app/config.py with an empty key in .env.example. False positive? Append "
        "'# pragma: allowlist secret' to the line.",
    )


if __name__ == "__main__":
    sys.exit(main())
