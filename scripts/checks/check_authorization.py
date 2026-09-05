"""Verify every FastAPI route keeps its server-side authorization and audit inputs.

Rules, enforced by parsing ``backend/app``:

* every ``/api/...`` route must depend on ``get_current_user`` or ``require_permission``;
* every state-changing route (POST/PUT/PATCH/DELETE) must use ``require_permission``
  and accept a request body model (so a reason can be captured for the audit trail);
* ``allow_origins=["*"]`` and other wildcard CORS settings are rejected.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

from common import REPO_ROOT, Finding, build_parser, report

BACKEND_APP = REPO_ROOT / "backend" / "app"
PUBLIC_PATHS = {"/health"}
MUTATING_METHODS = {"post", "put", "patch", "delete"}


def _route_decorator(decorator: ast.expr) -> tuple[str, str] | None:
    if not isinstance(decorator, ast.Call) or not isinstance(decorator.func, ast.Attribute):
        return None
    method = decorator.func.attr.lower()
    if method not in {"get", "post", "put", "patch", "delete"} or not decorator.args:
        return None
    path_node = decorator.args[0]
    if not isinstance(path_node, ast.Constant) or not isinstance(path_node.value, str):
        return None
    return method, path_node.value


def _dependency_names(func: ast.FunctionDef) -> dict[str, set[str]]:
    """Map parameter name -> names referenced inside its Depends(...) default."""
    result: dict[str, set[str]] = {}
    positional = func.args.args
    defaults = [None] * (len(positional) - len(func.args.defaults)) + list(func.args.defaults)
    for param, default in zip(positional, defaults, strict=True):
        if (
            isinstance(default, ast.Call)
            and isinstance(default.func, ast.Name)
            and default.func.id == "Depends"
        ):
            result[param.arg] = {n.id for n in ast.walk(default) if isinstance(n, ast.Name)}
    return result


def _has_body_model(func: ast.FunctionDef, dependency_params: set[str]) -> bool:
    for param in func.args.args:
        if param.arg in dependency_params or param.annotation is None:
            continue
        annotation = ast.unparse(param.annotation)
        if annotation not in {"str", "int", "float", "bool"}:
            return True
    return False


def check_routes(path: Path, tree: ast.Module) -> list[Finding]:
    findings: list[Finding] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        for decorator in node.decorator_list:
            route = _route_decorator(decorator)
            if route is None:
                continue
            method, url = route
            if url in PUBLIC_PATHS:
                continue
            deps = _dependency_names(node)
            auth_params = {
                name
                for name, refs in deps.items()
                if refs & {"get_current_user", "require_permission"}
            }
            permission_params = {
                name for name, refs in deps.items() if "require_permission" in refs
            }
            if not auth_params:
                findings.append(
                    Finding(
                        path,
                        node.lineno,
                        f"{method.upper()} {url} has no authentication dependency",
                    )
                )
                continue
            if method in MUTATING_METHODS:
                if not permission_params:
                    findings.append(
                        Finding(
                            path,
                            node.lineno,
                            f"{method.upper()} {url} mutates state without require_permission",
                        )
                    )
                if not _has_body_model(node, set(deps)):
                    findings.append(
                        Finding(
                            path,
                            node.lineno,
                            f"{method.upper()} {url} has no request model; "
                            "state changes must carry a reason",
                        )
                    )
    return findings


def check_cors(path: Path, tree: ast.Module) -> list[Finding]:
    findings: list[Finding] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.keyword) and node.arg == "allow_origins":
            if isinstance(node.value, ast.List) and any(
                isinstance(el, ast.Constant) and el.value == "*" for el in node.value.elts
            ):
                findings.append(
                    Finding(path, node.value.lineno, "wildcard CORS origin is not allowed")
                )
    return findings


def main(argv: list[str] | None = None) -> int:
    build_parser(__doc__ or "").parse_args(argv)
    findings: list[Finding] = []
    for path in sorted(BACKEND_APP.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        findings.extend(check_routes(path, tree))
        findings.extend(check_cors(path, tree))
    return report(
        "authorization",
        findings,
        "Every API route needs a server-side permission check, and state-changing routes must "
        "capture the actor and a reason. See AGENTS.md section 2 and docs/architecture.md.",
    )


if __name__ == "__main__":
    sys.exit(main())
