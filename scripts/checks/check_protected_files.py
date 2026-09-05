"""Block incidental edits to security-sensitive files.

Changes to authentication, configuration, CI, and dependency manifests require an
explicit acknowledgement so they are never bundled into an unrelated request:

* locally: ``PROTECTED_CHANGE_REASON="<why>" git commit ...``
* in CI: the pull request carries the ``security-review`` label
"""

from __future__ import annotations

import os
import sys

from common import Finding, build_parser, matches_any, relative, report, resolve_files

PROTECTED_PATHS: dict[str, str] = {
    "backend/app/auth.py": "authentication and role-permission mapping",
    "backend/app/config.py": "runtime boundary settings (CORS, auth mode)",
    "backend/app/models.py": "roles, permissions, and request schemas",
    ".env.example": "configuration surface",
    ".github/workflows/*": "CI configuration",
    ".pre-commit-config.yaml": "commit hooks",
    "scripts/checks/*": "repository guardrails",
    "package-lock.json": "frontend dependency lockfile",
    "frontend/package.json": "frontend dependency manifest",
    "backend/pyproject.toml": "backend dependency manifest",
    "backend/poetry.lock": "backend dependency lockfile",
    "AGENTS.md": "agent operating rules",
}

LOCAL_OVERRIDE_ENV = "PROTECTED_CHANGE_REASON"
CI_LABEL = "security-review"


def acknowledged() -> bool:
    if os.environ.get(LOCAL_OVERRIDE_ENV, "").strip():
        return True
    labels = {label.strip() for label in os.environ.get("PR_LABELS", "").split(",")}
    return CI_LABEL in labels


def main(argv: list[str] | None = None) -> int:
    args = build_parser(__doc__ or "").parse_args(argv)
    findings: list[Finding] = []
    if args.all:
        print("[protected-files] skipped (only meaningful for changed files)")
        return 0
    if not acknowledged():
        for path in resolve_files(args):
            rel = relative(path)
            for pattern, description in PROTECTED_PATHS.items():
                if matches_any(rel, [pattern]):
                    findings.append(Finding(path, 0, f"protected file changed ({description})"))
                    break
    return report(
        "protected-files",
        findings,
        "Protected files may only change when that is the request itself. If it is, commit "
        f'with {LOCAL_OVERRIDE_ENV}="<justification>" set and ask a maintainer to add the '
        f"'{CI_LABEL}' label to the pull request. Otherwise revert these files.",
    )


if __name__ == "__main__":
    sys.exit(main())
