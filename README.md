# Fintech Operations Admin

A security-conscious proof of concept for an internal operations console used by compliance, product, engineering, and customer support teams.

## Prototype capabilities

- Microsoft/Entra-style sign-in using synthetic internal personas
- Role-based module access enforced in the UI and FastAPI routes
- Super-admin role assignment
- KYC review queue
- Feature flag controls
- Refund operations dashboard
- Integration ports that can be replaced with internal data-source adapters

All people, accounts, transactions, and identity data in this repository are fictional.

## Repository structure

```text
frontend/   React, TypeScript, and Vite
backend/    FastAPI application managed with Poetry
docs/       Architecture and security notes
```

## Prerequisites

- Node.js 20+
- npm 10+
- Python 3.10+
- Poetry 1.8+

## Setup

```bash
npm install
poetry --directory backend install
```

Copy `.env.example` to `.env` if you need to override defaults.

Install the commit hooks once per clone:

```bash
npm run hooks:install
```

## Run locally

```bash
npm run dev
```

This starts the FastAPI server and Vite frontend together. Open `http://localhost:5173` and choose a demo identity. Morgan Lee is the super-admin persona.

## Checks

Commit hooks (`.pre-commit-config.yaml`) and CI (`.github/workflows/pr-checks.yml`) run
the same gates, so a change that commits cleanly should also pass review checks:

| Gate | What it enforces |
| --- | --- |
| `guard-secrets` | no credentials, tokens, private keys, or real `.env` files |
| `guard-sensitive-data` | synthetic emails/cards/IBANs only; no `print`/`console.log`; no PII in logs |
| `guard-protected-files` | auth, config, CI, hooks, and dependency manifests only change deliberately |
| `guard-authorization` | every API route keeps `require_permission`; mutations carry a request model; no wildcard CORS |
| `guard-dependencies` | exact version pins; new versions at least 7 days old (CI) |
| PR description (CI) | Summary, Data-security surface, and Not done sections are filled in |
| ruff, mypy, eslint, tsc | code quality on commit; pytest and build on push |

Run everything by hand:

```bash
npm run check
npm run lint
npm run typecheck
npm run build
poetry --directory backend run ruff check .
poetry --directory backend run mypy --config-file backend/pyproject.toml backend/app
poetry --directory backend run pytest
```

## Production path

The current sign-in screen is deliberately a demo adapter; it does not contact Microsoft or issue real credentials. See `docs/architecture.md` for the Entra ID integration, authorization, audit, sensitive-data, and internal-connector boundaries expected in a production implementation.
