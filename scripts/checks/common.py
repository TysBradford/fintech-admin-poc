"""Shared helpers for the repository guardrail checks.

Every check accepts an optional list of file paths (pre-commit passes the staged files).
With no arguments, a check inspects the files changed against ``--base`` (CI) or the
staged files (local). Findings are printed in ``path:line: message`` form so editors and
GitHub annotations can pick them up.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

BINARY_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".woff", ".woff2", ".pdf", ".lock"}


@dataclass(frozen=True)
class Finding:
    path: Path
    line: int
    message: str

    def render(self) -> str:
        rel = self.path.relative_to(REPO_ROOT) if self.path.is_absolute() else self.path
        location = f"{rel}:{self.line}" if self.line else str(rel)
        return f"{location}: {self.message}"


def build_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("files", nargs="*", help="Files to check (default: changed files)")
    parser.add_argument(
        "--base",
        help="Git ref to diff against instead of the index (used in CI, e.g. origin/main)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Check every tracked file rather than only changed ones",
    )
    return parser


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=REPO_ROOT, check=True, capture_output=True, text=True
    )
    return result.stdout


def changed_files(base: str | None) -> list[Path]:
    if base:
        merge_base = _git("merge-base", base, "HEAD").strip()
        output = _git("diff", "--name-only", "--diff-filter=ACMR", merge_base, "HEAD")
    else:
        output = _git("diff", "--cached", "--name-only", "--diff-filter=ACMR")
    return [REPO_ROOT / line for line in output.splitlines() if line.strip()]


def tracked_files() -> list[Path]:
    return [REPO_ROOT / line for line in _git("ls-files").splitlines() if line.strip()]


def resolve_files(args: argparse.Namespace) -> list[Path]:
    if args.files:
        paths = [Path(f) if Path(f).is_absolute() else REPO_ROOT / f for f in args.files]
    elif args.all:
        paths = tracked_files()
    else:
        paths = changed_files(args.base)
    return [p for p in paths if p.is_file()]


def is_text_file(path: Path) -> bool:
    if path.suffix.lower() in BINARY_SUFFIXES:
        return False
    try:
        path.read_bytes()[:1024].decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True


def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def relative(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def matches_any(rel_path: str, patterns: Iterable[str]) -> bool:
    from fnmatch import fnmatch

    return any(fnmatch(rel_path, pattern) for pattern in patterns)


def report(check_name: str, findings: Sequence[Finding], remedy: str) -> int:
    if not findings:
        print(f"[{check_name}] ok")
        return 0
    print(f"[{check_name}] {len(findings)} finding(s):", file=sys.stderr)
    for finding in findings:
        print(f"  {finding.render()}", file=sys.stderr)
    print(f"\n{remedy}", file=sys.stderr)
    return 1
