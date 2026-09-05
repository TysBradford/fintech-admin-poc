"""Run every repository guardrail check in one go.

python3 scripts/checks/run.py            # staged files
python3 scripts/checks/run.py --all      # whole repository
python3 scripts/checks/run.py --base origin/main
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

CHECKS = [
    "check_secrets.py",
    "check_protected_files.py",
    "check_sensitive_data.py",
    "check_authorization.py",
    "check_dependencies.py",
]


def main(argv: list[str]) -> int:
    here = Path(__file__).resolve().parent
    failed: list[str] = []
    for check in CHECKS:
        extra = ["--offline"] if check == "check_dependencies.py" and "--base" not in argv else []
        result = subprocess.run([sys.executable, str(here / check), *argv, *extra], check=False)
        if result.returncode != 0:
            failed.append(check)
    if failed:
        print(f"\n{len(failed)} check(s) failed: {', '.join(failed)}", file=sys.stderr)
        return 1
    print("\nall guardrail checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
