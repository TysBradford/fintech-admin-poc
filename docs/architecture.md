# Architecture and security notes

## Authentication

The prototype uses an explicit `AUTH_MODE=demo` adapter and synthetic personas. A production adapter should use Microsoft Entra ID's OAuth 2.0 authorization-code flow with PKCE:

1. Register separate frontend and API applications.
2. Restrict the tenant and redirect URIs.
3. Validate issuer, audience, signature, nonce, expiry, and tenant on the API.
4. Resolve immutable Entra object IDs to internal user records.
5. Prefer short-lived tokens and require conditional access or step-up authentication for high-risk actions.

The frontend must never be treated as an authorization boundary. Every protected API operation checks permissions independently.

The application composes authentication and authorization through vendor-neutral ports:

- an identity provider authenticates credentials into an external subject and tenant;
- an authorization repository maps that identity to an internal user and resolves role policy;
- an authorization service computes effective permissions and enforces route requirements;
- privileged role assignments execute through a unit of work with an audit sink.

`AUTH_MODE` selects the configured identity provider and fails closed when no adapter exists. The demo adapter requires an explicit synthetic identity; production modes must never fall back to it.

## Authorization

Roles are small job-function bundles, while permissions are operation-specific. Production storage should include:

- immutable user and role identifiers;
- effective and expiry timestamps;
- the assigning actor and reason;
- approval requirements for privileged roles;
- append-only audit events.

Entra groups can seed role membership, but application-level policy remains the source of truth where finer controls are required.

## Sensitive data

- Default to masked fields and reveal only with a specific permission and audit event.
- Avoid placing personal or financial data in URLs, client logs, analytics, or error trackers.
- Encrypt data in transit and at rest using organization-managed keys.
- Apply data minimization, retention, export, and deletion policies per source.
- Use synthetic fixtures outside approved production environments.

## Internal integrations

`app.ports` defines interfaces for KYC, feature flags, and payments. Demo adapters currently return synthetic records. Production adapters should add:

- workload identity rather than static credentials;
- strict timeouts, retries, circuit breakers, and idempotency keys;
- source-specific request and response validation;
- correlation IDs and structured, redacted logs;
- explicit failure states rather than silent fallback data.

## Operational controls

State-changing actions should require CSRF protection where cookie auth is used, server-side validation, actor/reason capture, and an immutable audit trail. Refunds and privileged role changes should support dual control above configurable risk thresholds.
