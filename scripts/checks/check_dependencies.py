"""Vet dependency manifest changes.

Every dependency must be pinned to an exact version, and any version that is new relative
to ``--base`` must have been published at least ``MIN_AGE_DAYS`` ago (supply-chain
cool-off). Registry lookups need network access, so this check runs in CI; pass
``--offline`` to only enforce pinning.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import urllib.request
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from pathlib import Path

from common import REPO_ROOT, Finding, build_parser, report

MIN_AGE_DAYS = 7
FRONTEND_MANIFEST = REPO_ROOT / "frontend" / "package.json"
ROOT_MANIFEST = REPO_ROOT / "package.json"
BACKEND_MANIFEST = REPO_ROOT / "backend" / "pyproject.toml"
EXACT_NPM = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
EXACT_PY = re.compile(r"^\d+(?:\.\d+)*(?:[a-z]+\d*)?$")
POETRY_DEP_SECTION = re.compile(
    r"^\[tool\.poetry\.(?:dependencies|group\.[^.\]]+\.dependencies)\]\s*$"
)
TOML_SECTION = re.compile(r"^\[.*\]\s*$")
POETRY_DEP_LINE = re.compile(
    r'^([A-Za-z0-9_.-]+)\s*=\s*(?:"([^"]*)"|\{[^}]*\bversion\s*=\s*"([^"]*)"[^}]*\})'
)

Parser = Callable[[str], dict[str, str]]
ReleaseDate = Callable[[str, str], datetime | None]
UTC = timezone.utc


def npm_dependencies(text: str) -> dict[str, str]:
    data = json.loads(text)
    deps: dict[str, str] = {}
    for section in ("dependencies", "devDependencies"):
        deps.update(data.get(section, {}))
    return deps


def poetry_dependencies(text: str) -> dict[str, str]:
    deps: dict[str, str] = {}
    in_section = False
    for line in text.splitlines():
        if TOML_SECTION.match(line):
            in_section = bool(POETRY_DEP_SECTION.match(line))
            continue
        if not in_section:
            continue
        match = POETRY_DEP_LINE.match(line.strip())
        if match and match.group(1) != "python":
            deps[match.group(1)] = match.group(2) or match.group(3) or ""
    return deps


def file_at(base: str | None, path: Path) -> str | None:
    if base is None:
        return None
    rel = path.relative_to(REPO_ROOT).as_posix()
    result = subprocess.run(
        ["git", "show", f"{base}:{rel}"], cwd=REPO_ROOT, capture_output=True, text=True
    )
    return result.stdout if result.returncode == 0 else None


def fetch_json(url: str) -> dict[str, object]:
    with urllib.request.urlopen(url, timeout=15) as response:  # noqa: S310
        data = json.load(response)
    if not isinstance(data, dict):
        raise ValueError(f"unexpected registry response from {url}")
    return data


def npm_release_date(name: str, version: str) -> datetime | None:
    data = fetch_json(f"https://registry.npmjs.org/{name}")
    times = data.get("time")
    if isinstance(times, dict) and version in times:
        return _parse_timestamp(str(times[version]))
    return None


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def pypi_release_date(name: str, version: str) -> datetime | None:
    data = fetch_json(f"https://pypi.org/pypi/{name}/{version}/json")
    urls = data.get("urls")
    if isinstance(urls, list) and urls:
        stamps = [_parse_timestamp(str(u["upload_time_iso_8601"])) for u in urls]
        return min(stamps)
    return None


def check_manifest(
    path: Path,
    parse: Parser,
    exact: re.Pattern[str],
    release_date: ReleaseDate,
    base: str | None,
    offline: bool,
) -> list[Finding]:
    findings: list[Finding] = []
    current = parse(path.read_text(encoding="utf-8"))
    previous_text = file_at(base, path)
    previous = parse(previous_text) if previous_text else {}
    cutoff = datetime.now(UTC) - timedelta(days=MIN_AGE_DAYS)

    for name, version in sorted(current.items()):
        if not exact.match(version):
            findings.append(
                Finding(path, 0, f"{name} must be pinned to an exact version (got '{version}')")
            )
            continue
        if offline or base is None or previous.get(name) == version:
            continue
        try:
            published = release_date(name, version)
        except Exception as error:  # noqa: BLE001
            findings.append(
                Finding(path, 0, f"could not verify release date for {name}@{version}: {error}")
            )
            continue
        if published is None:
            findings.append(Finding(path, 0, f"{name}@{version} not found in the registry"))
        elif published > cutoff:
            age = (datetime.now(UTC) - published).days
            findings.append(
                Finding(
                    path,
                    0,
                    f"{name}@{version} was published {age} day(s) ago; minimum is {MIN_AGE_DAYS}",
                )
            )
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = build_parser(__doc__ or "")
    parser.add_argument("--offline", action="store_true", help="Skip registry release-date lookups")
    args = parser.parse_args(argv)

    findings: list[Finding] = []
    for manifest in (FRONTEND_MANIFEST, ROOT_MANIFEST):
        findings.extend(
            check_manifest(
                manifest, npm_dependencies, EXACT_NPM, npm_release_date, args.base, args.offline
            )
        )
    findings.extend(
        check_manifest(
            BACKEND_MANIFEST,
            poetry_dependencies,
            EXACT_PY,
            pypi_release_date,
            args.base,
            args.offline,
        )
    )
    return report(
        "dependencies",
        findings,
        "Pin dependencies exactly and only adopt versions published at least "
        f"{MIN_AGE_DAYS} days ago. New dependencies need explicit approval in the request.",
    )


if __name__ == "__main__":
    sys.exit(main())
