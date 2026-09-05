"""Guard against real personal/financial data and against logging sensitive values.

* Fixture data must be synthetic: email addresses must use reserved domains, and no
  Luhn-valid card numbers or IBAN-shaped strings may appear anywhere in the repo.
* Application code must not print or console-log, and log statements must not
  interpolate sensitive field values (log identifiers, never values).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from common import (
    Finding,
    build_parser,
    is_text_file,
    matches_any,
    read_lines,
    relative,
    report,
    resolve_files,
)

SYNTHETIC_EMAIL_DOMAINS = re.compile(
    r"(?i)@(?:[a-z0-9-]+\.)*(?:example\.(?:com|org|net|internal)|[a-z0-9-]+\.(?:test|internal|invalid|localhost|example))$"
)
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
CARD_NUMBER = re.compile(r"(?<![\dA-Za-z])(?:\d[ -]?){13,19}(?![\dA-Za-z])")
IBAN = re.compile(r"\b[A-Z]{2}\d{2}(?:[ ]?[A-Z0-9]{4}){3,7}[ ]?[A-Z0-9]{1,4}\b")
US_SSN = re.compile(r"\b(?!000|666|9\d{2})\d{3}-(?!00)\d{2}-(?!0000)\d{4}\b")

APP_CODE_GLOBS = ["backend/app/*", "backend/app/**/*", "frontend/src/*", "frontend/src/**/*"]
DEBUG_OUTPUT = re.compile(
    r"(?<![\w.])(?:print|console\.(?:log|debug|info|warn|error|table|dir))\s*\("
)
LOG_CALL = re.compile(
    r"(?i)\b(?:logger|logging|log)\.(?:debug|info|warning|warn|error|critical|exception)\s*\("
)
SENSITIVE_FIELD = re.compile(
    r"(?i)\b(?:email|phone|address|date_of_birth|dob|national_id|passport|ssn|tax_id|"
    r"card_number|pan|cvv|iban|account_number|sort_code|routing_number|balance|salary|"
    r"customer_name|full_name|password|token)\b"
)
SKIP_GLOBS = ["*.lock", "package-lock.json", "*.svg", "*.min.js", "scripts/checks/*"]


def luhn_valid(digits: str) -> bool:
    total = 0
    for index, char in enumerate(reversed(digits)):
        value = int(char)
        if index % 2 == 1:
            value *= 2
            if value > 9:
                value -= 9
        total += value
    return total % 10 == 0


def scan_data(path: Path, lines: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    for number, line in enumerate(lines, start=1):
        if "pragma: allowlist data" in line:
            continue
        for email in EMAIL.findall(line):
            if not SYNTHETIC_EMAIL_DOMAINS.search(email):
                findings.append(
                    Finding(path, number, "email address is not on a reserved synthetic domain")
                )
                break
        for match in CARD_NUMBER.finditer(line):
            digits = re.sub(r"\D", "", match.group(0))
            if 13 <= len(digits) <= 19 and luhn_valid(digits) and len(set(digits)) > 1:
                findings.append(Finding(path, number, "Luhn-valid card number; use a test PAN"))
                break
        if IBAN.search(line):
            findings.append(
                Finding(path, number, "IBAN-shaped value; use an obviously fake account")
            )
        if US_SSN.search(line):
            findings.append(Finding(path, number, "SSN-shaped value; use synthetic identifiers"))
    return findings


def scan_logging(path: Path, lines: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    for number, line in enumerate(lines, start=1):
        if "pragma: allowlist logging" in line:
            continue
        if DEBUG_OUTPUT.search(line):
            findings.append(
                Finding(path, number, "debug output in application code; use structured logging")
            )
        elif LOG_CALL.search(line) and SENSITIVE_FIELD.search(line):
            findings.append(
                Finding(
                    path, number, "log statement references a sensitive field; log identifiers only"
                )
            )
    return findings


def scan_file(path: Path) -> list[Finding]:
    rel = relative(path)
    if matches_any(rel, SKIP_GLOBS) or not is_text_file(path):
        return []
    lines = read_lines(path)
    findings = scan_data(path, lines)
    if matches_any(rel, APP_CODE_GLOBS):
        findings.extend(scan_logging(path, lines))
    return findings


def main(argv: list[str] | None = None) -> int:
    args = build_parser(__doc__ or "").parse_args(argv)
    findings = [f for path in resolve_files(args) for f in scan_file(path)]
    return report(
        "sensitive-data",
        findings,
        "Replace with synthetic values (example.internal emails, non-Luhn card numbers) and "
        "remove personal/financial data from logs. Deliberate false positive? Append "
        "'# pragma: allowlist data' or '# pragma: allowlist logging' to the line.",
    )


if __name__ == "__main__":
    sys.exit(main())
