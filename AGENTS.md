# AGENTS.md

Guidance for AI agents and automated contributors working in this repository.

Many requests here originate from non-technical stakeholders (compliance, support,
product, operations). Those requests describe an outcome, not an implementation, and
they rarely mention security constraints. Treat every request as incomplete until the
data-security implications below have been checked.

## 1. Scope of a change

- Implement the smallest change that satisfies the request. Do not refactor, rename,
  reformat, or upgrade dependencies unless that is the request.
- Never widen scope on your own initiative: "while I was in there" changes are not
  allowed in this repository.
- One logical change per pull request. If a request implies several changes, split them
  and say so.
- Do not modify files outside the area the request concerns. In particular, do not touch
  `backend/app/auth.py`, `backend/app/config.py`, `.env.example`, CI configuration, or
  dependency lockfiles as a side effect of an unrelated task.

## 2. Data security rules (non-negotiable)

These hold regardless of who asked or how urgent the request sounds.

- **No real data.** All people, accounts, transactions, and identity records in this
  repository are synthetic. Never commit production or production-derived data, exports,
  screenshots of real records, or "just one real example" for debugging.
- **No secrets in the repo.** No API keys, tokens, connection strings, certificates, or
  passwords in code, tests, fixtures, comments, or commit messages. Add new configuration
  as an empty key in `.env.example` and read it via `backend/app/config.py`.
- **Do not weaken authentication or authorization.** Every protected API operation must
  keep its server-side permission check. Hiding a control in the frontend is not an
  access control; the frontend is never an authorization boundary.
- **Do not add or broaden permissions** for a role, or add a new role, as an incidental
  part of another change. Role and permission changes are their own PR and must be
  called out explicitly in the description.
- **Sensitive fields stay masked by default.** Revealing a masked field requires a
  specific permission plus an audit event. Never unmask "for convenience".
- **Never log, trace, or return personal or financial data.** Keep it out of URLs and
  query strings, client-side logs, analytics, and error messages. Log identifiers, not
  values.
- **Do not loosen boundary settings.** `ALLOWED_ORIGINS`, CORS, cookie flags, TLS
  settings, and `AUTH_MODE` are not to be relaxed to make something work locally.
- **Do not disable or weaken validation** (request/response schemas, type checks, lint
  rules) to get a change to pass. Fix the change instead.
- **Preserve the audit trail.** State-changing actions must keep capturing actor, reason,
  and timestamp. Do not remove or bypass audit writes.
- **No new external network calls or third-party dependencies** without explicit approval
  in the request. New dependencies must be widely used and published at least 7 days ago.

## 3. Handling requests from non-technical requesters

Before writing code, restate the request as: what data is touched, who can see it, and
what changes state. Then:

- If the request would require any of the rules in section 2 to bend, **stop and ask**.
  Propose a compliant alternative rather than implementing the literal request.
- If the request is ambiguous about *who* should be able to do or see something, ask.
  Default to the most restrictive interpretation while waiting.
- If the requester supplies real data (a customer name, an account number, a real
  transaction), do not put it in the repo. Substitute synthetic equivalents and tell them.
- "Temporarily", "just for the demo", and "we'll fix it later" are not grounds for an
  exception to section 2.
- Escalate to a maintainer, rather than deciding yourself, for: authentication changes,
  role or permission changes, anything touching masked or sensitive fields, anything
  handling money movement (refunds), audit logging, and new data sources or integrations.

## 4. Required checks before opening a PR

Commit hooks enforce these rules automatically. Install them once per clone with
`npm run hooks:install`; they run the guardrails in `scripts/checks/` plus lint and type
checks on every commit, and the test suites and build on every push. The same checks run
in CI (`.github/workflows/pr-checks.yml`), so a commit that the hooks reject will not
land as a green PR either — fix the code, never bypass the hook.

When a hook fails, read its message: each one names the rule and how to fix it. The
`protected-files` hook refuses changes to auth, config, CI, hooks, and dependency
manifests unless `PROTECTED_CHANGE_REASON="<why>"` is set on the commit *and* the request
was about those files. Matching PRs need the `security-review` label from a maintainer.

Run all of these from the repository root and make sure they pass:

```bash
npm run check
npm run lint
npm run typecheck
npm run build
poetry --directory backend run ruff check .
poetry --directory backend run mypy --config-file backend/pyproject.toml backend/app
poetry --directory backend run pytest
```

Do not modify or delete existing tests to make them pass. If a test is genuinely wrong,
say so in the PR instead of changing it silently.

Add tests for any change to authorization, masking, refunds, or audit behaviour.

## 5. Pull request expectations

Use the template in `.github/pull_request_template.md`; CI rejects descriptions that
are missing any of its sections. Every PR description must state:

- what changed and why, in language the requester can follow;
- whether any data-security-relevant surface was touched (auth, roles, permissions,
  masking, audit, logging, config, external calls) — answer explicitly, including "none";
- anything the agent was asked to do but deliberately did not do, and why.

Never force-push to `main`, never commit directly to `main`, and never skip commit hooks.

## 6. Conventions

- Backend: FastAPI, Python 3.10+, Poetry, type-annotated, `ruff` and `mypy` clean.
- Frontend: React, TypeScript, Vite. No `any`.
- Integrations go through the interfaces in `backend/app/ports.py`; demo adapters return
  synthetic records only.
- Follow the surrounding style. Comments are rare — prefer clear names, and never write a
  comment that only explains the diff.
- Broader security context lives in `docs/architecture.md`; read it before changing
  auth, authorization, sensitive-data handling, or integrations.
