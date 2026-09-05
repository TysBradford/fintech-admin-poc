import ast
import sys
import textwrap
from pathlib import Path

import pytest

CHECKS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CHECKS_DIR))

import check_authorization  # noqa: E402
import check_dependencies  # noqa: E402
import check_pr_description  # noqa: E402
import check_secrets  # noqa: E402
import check_sensitive_data  # noqa: E402
from common import REPO_ROOT  # noqa: E402


def write(tmp_path: Path, name: str, content: str) -> Path:
    path = tmp_path / name
    path.write_text(textwrap.dedent(content), encoding="utf-8")
    return path


# Assembled at runtime so the fixtures themselves do not trip the secret scanners.
FAKE_SECRETS = [
    'AWS_KEY = "' + "AKIA" + "ABCDEFGHIJKLMNOP" + '"',
    "pass" + 'word = "hunter2hunter2hunter2"',
    "-----BEGIN RSA " + "PRIVATE KEY-----",
    "postgres://admin:" + "s3cretpass@db.internal/app",
]


@pytest.mark.parametrize("content", FAKE_SECRETS)
def test_secrets_detected(tmp_path: Path, content: str) -> None:
    assert check_secrets.scan_file(write(tmp_path, "settings.py", content))


@pytest.mark.parametrize(
    "content",
    [
        'password = "<your-password-here>"',
        'api_key = "${API_KEY_FROM_VAULT}"',
        'token = "abcdefghijklmnopqrstuvwxyz"  # pragma: allowlist secret',
        'auth_mode: str = "demo"',
    ],
)
def test_secrets_placeholders_allowed(tmp_path: Path, content: str) -> None:
    assert not check_secrets.scan_file(write(tmp_path, "settings.py", content))


def test_env_file_rejected(tmp_path: Path) -> None:
    assert check_secrets.scan_file(write(tmp_path, ".env", "X=1"))
    assert check_secrets.scan_file(write(tmp_path, ".env.production", "X=1"))


def test_env_example_requires_empty_secrets(tmp_path: Path) -> None:
    assert check_secrets.scan_file(write(tmp_path, ".env.example", "ENTRA_CLIENT_SECRET=abc123\n"))
    assert not check_secrets.scan_file(write(tmp_path, ".env.example", "ENTRA_CLIENT_SECRET=\n"))


def test_repo_env_example_is_clean() -> None:
    assert not check_secrets.scan_file(REPO_ROOT / ".env.example")


def test_real_looking_email_rejected(tmp_path: Path) -> None:
    assert check_sensitive_data.scan_file(
        write(tmp_path, "fixtures.py", 'email="jane.doe@gmail.com"')
    )
    assert not check_sensitive_data.scan_file(
        write(tmp_path, "fixtures.py", 'email="jane.doe@example.internal"')
    )


def test_luhn_valid_card_rejected(tmp_path: Path) -> None:
    assert check_sensitive_data.scan_file(
        write(tmp_path, "fixtures.py", 'card="5555 5555 5555 4444"')
    )
    assert check_sensitive_data.scan_file(write(tmp_path, "fixtures.py", 'card="4111111111111111"'))
    assert not check_sensitive_data.scan_file(
        write(tmp_path, "fixtures.py", 'card="4111111111111112"')
    )


def test_iban_rejected(tmp_path: Path) -> None:
    assert check_sensitive_data.scan_file(
        write(tmp_path, "fixtures.py", 'iban="GB29 NWBK 6016 1331 9268 19"')
    )


def test_debug_logging_only_flagged_in_app_code() -> None:
    lines = ["print(user.email)", 'logger.info("refund for %s", account_number)']
    findings = check_sensitive_data.scan_logging(Path("x.py"), lines)
    assert [f.line for f in findings] == [1, 2]
    assert not check_sensitive_data.scan_logging(
        Path("x.py"), ['logger.info("refund %s", refund_id)']
    )


def test_repo_fixtures_are_synthetic() -> None:
    files = [p for p in (REPO_ROOT / "backend").rglob("*.py")] + list(
        (REPO_ROOT / "frontend" / "src").rglob("*.ts*")
    )
    findings = [f for path in files for f in check_sensitive_data.scan_file(path)]
    assert findings == []


def _routes(source: str) -> list[str]:
    tree = ast.parse(textwrap.dedent(source))
    return [f.message for f in check_authorization.check_routes(Path("main.py"), tree)]


def test_route_without_auth_rejected() -> None:
    assert _routes(
        """
        @app.get("/api/kyc/cases")
        def list_cases() -> list[dict[str, object]]:
            return []
        """
    ) == ["GET /api/kyc/cases has no authentication dependency"]


def test_mutating_route_needs_permission_and_body() -> None:
    messages = _routes(
        """
        @app.post("/api/refunds/{refund_id}/approve")
        def approve(refund_id: str, user: User = Depends(get_current_user)) -> dict[str, object]:
            return {}
        """
    )
    assert (
        "POST /api/refunds/{refund_id}/approve mutates state without require_permission" in messages
    )
    assert any("no request model" in m for m in messages)


def test_compliant_mutating_route_passes() -> None:
    assert not _routes(
        """
        @app.post("/api/refunds/{refund_id}/approve")
        def approve(
            refund_id: str,
            payload: RefundRequest,
            user: User = Depends(require_permission(Permission.REFUNDS_WRITE)),
        ) -> dict[str, object]:
            return {}
        """
    )


def test_wildcard_cors_rejected() -> None:
    tree = ast.parse('app.add_middleware(CORSMiddleware, allow_origins=["*"])')
    assert check_authorization.check_cors(Path("main.py"), tree)


def test_current_backend_passes_authorization_check() -> None:
    assert check_authorization.main([]) == 0


def test_poetry_manifest_parsing() -> None:
    deps = check_dependencies.poetry_dependencies(
        (REPO_ROOT / "backend" / "pyproject.toml").read_text()
    )
    assert deps["fastapi"] == "0.115.6"
    assert deps["uvicorn"] == "0.32.1"
    assert "python" not in deps


def test_unpinned_dependency_rejected(tmp_path: Path) -> None:
    manifest = write(tmp_path, "package.json", '{"dependencies": {"react": "^18.0.0"}}')
    findings = check_dependencies.check_manifest(
        manifest,
        check_dependencies.npm_dependencies,
        check_dependencies.EXACT_NPM,
        lambda n, v: None,
        None,
        True,
    )
    assert findings and "pinned" in findings[0].message


GOOD_BODY = """
## Summary
Adds a filter to the refund queue so completed refunds are hidden.

## Data-security surface
None. No auth, roles, masking, audit, logging, or config changes.

## Not done
Nothing was left out.
"""


def test_pr_description_complete() -> None:
    assert not check_pr_description.check("Hide completed refunds from queue", GOOD_BODY)


def test_pr_description_missing_section() -> None:
    body = GOOD_BODY.replace("## Data-security surface", "## Other")
    messages = [f.message for f in check_pr_description.check("Hide completed refunds", body)]
    assert any("Data-security surface" in m for m in messages)


def test_pr_description_rejects_wip_and_unchecked_items() -> None:
    messages = [
        f.message for f in check_pr_description.check("WIP: thing", GOOD_BODY + "\n- [ ] todo")
    ]
    assert any("work in progress" in m for m in messages)
    assert any("unchecked" in m for m in messages)
