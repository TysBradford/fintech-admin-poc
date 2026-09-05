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

## Run locally

Start the API:

```bash
poetry --directory backend run uvicorn app.main:app --reload
```

Start the frontend in another terminal:

```bash
npm run dev
```

Open `http://localhost:5173` and choose a demo identity. Morgan Lee is the super-admin persona.

## Checks

```bash
npm run lint
npm run typecheck
npm run build
poetry --directory backend run ruff check .
poetry --directory backend run mypy app
poetry --directory backend run pytest
```

## Production path

The current sign-in screen is deliberately a demo adapter; it does not contact Microsoft or issue real credentials. See `docs/architecture.md` for the Entra ID integration, authorization, audit, sensitive-data, and internal-connector boundaries expected in a production implementation.
