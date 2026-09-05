"""Verify the pull request description covers what AGENTS.md section 5 requires.

The body is read from ``--body-file`` or the ``PR_BODY`` environment variable, the title
from ``--title`` or ``PR_TITLE``. Each required heading must be present and followed by
at least one sentence of content.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

from common import Finding, report

REQUIRED_SECTIONS: dict[str, str] = {
    "Summary": "what changed and why, in language the requester can follow",
    "Data-security surface": (
        "auth, roles, permissions, masking, audit, logging, config, external calls, or 'none'"
    ),
    "Not done": "anything requested but deliberately left out, and why (or 'nothing')",
}
MIN_SECTION_CHARS = 12
MAX_TITLE_CHARS = 72
CHECKLIST_UNCHECKED = re.compile(r"^\s*[-*]\s+\[ \]", re.MULTILINE)
HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)

DESCRIPTION = Path("PR_DESCRIPTION")


def sections(body: str) -> dict[str, str]:
    result: dict[str, str] = {}
    current: str | None = None
    for line in HTML_COMMENT.sub("", body).splitlines():
        heading = re.match(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$", line)
        if heading:
            current = heading.group(1).strip().lower()
            result.setdefault(current, "")
        elif current is not None:
            result[current] += line + "\n"
    return result


def check(title: str, body: str) -> list[Finding]:
    findings: list[Finding] = []
    if not title.strip():
        findings.append(Finding(DESCRIPTION, 0, "title is empty"))
    elif len(title) > MAX_TITLE_CHARS:
        findings.append(Finding(DESCRIPTION, 0, f"title longer than {MAX_TITLE_CHARS} characters"))
    if re.match(r"(?i)^(wip|draft|fixup|tmp|test)\b", title.strip()):
        findings.append(Finding(DESCRIPTION, 0, "title marks the PR as work in progress"))

    found = sections(body)
    for name, hint in REQUIRED_SECTIONS.items():
        content = found.get(name.lower(), "").strip()
        if name.lower() not in found:
            findings.append(Finding(DESCRIPTION, 0, f"missing '## {name}' section ({hint})"))
        elif len(content) < MIN_SECTION_CHARS:
            findings.append(Finding(DESCRIPTION, 0, f"'## {name}' section is empty ({hint})"))
    if CHECKLIST_UNCHECKED.search(body):
        findings.append(Finding(DESCRIPTION, 0, "description still has unchecked checklist items"))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--title", default=os.environ.get("PR_TITLE", ""))
    parser.add_argument("--body-file", type=Path)
    args = parser.parse_args(argv)
    body = (
        args.body_file.read_text(encoding="utf-8")
        if args.body_file
        else os.environ.get("PR_BODY", "")
    )
    return report(
        "pr-description",
        check(args.title, body),
        "Fill in the pull request template (.github/pull_request_template.md): a Summary, an "
        "explicit Data-security surface statement, and a Not done section.",
    )


if __name__ == "__main__":
    sys.exit(main())
