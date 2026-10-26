# Compatibility and upgrade policy

Compatibility is established for a version and deployment combination, not from a dependency range alone. See [VALIDATION.md](VALIDATION.md) for dated execution evidence and outstanding acceptance gates. All current workflows use `supportScope: controlled-validation` and require administrator admission of their published version.

## Version matrix

| Community package | n8n / Node.js | JS / Python MCP SDK | MCP wire protocol | AstronRPA | Deployment and evidence |
| --- | --- | --- | --- | --- | --- |
| `0.1.0-dev.3` | `2.40.7` / `24.18.0` | `1.30.0` / `1.26.0` | `2025-11-25` | Desktop shell `1.1.8` with candidate Engine; business/profile/client protocol `1` | 2026-10-23: regular and isolated queue (PostgreSQL `15.19`, Redis `7.0.15`, database Binary Data); single OpenAPI and two same-host replicas with shared storage |
| `0.1.0-dev.4` | `2.40.7` / `24.18.0` | `1.30.0` / `1.26.0` | `2025-11-25` | Full locally built/installed Windows `1.1.8` candidate, Python `3.13.14`; business/profile/client protocol `1` | 2026-10-23: regular and isolated queue (PostgreSQL `17.11`, Redis `7.0.15`, default Binary Data), MCP/REST data/file/WPS workflows, worker recovery and cancellation/deadline; earlier dev.3 rollback/dev.4 re-upgrade evidence retained separately |
| Current server adapter | Protocol probes, independent of node package | Python `1.26.0` plus explicit modern adapter | `2025-03-26`, `2025-06-18`, `2025-11-25`, `2026-07-28` | Same candidate server | 2026-10-23 proxy probes; legacy initialize/list/call and modern no-session discover/list/call. The community node selects only `2025-11-25` |
| Other versions or deployments | Declared Node `>=24`, peer `n8n-workflow >=2.36.4 <3` | Not otherwise verified | No inferred compatibility | Unverified | Older clients, n8n Cloud, multiple desktops and multi-host file stores are outside the verified scope |

The `2026-07-28` adapter does not support initialize, session resume or subscriptions. Running an older SDK with `stateless=True` alone does not establish modern protocol compliance. Queue workers must run the same node tarball as main; filesystem Binary Data across workers is not validated. Redis routing requires all OpenAPI replicas to share the same mode, database, policy and file store.

The full-client Office checks used WPS Office `12.8.2.21555` through the existing Excel/Word COM components; native Microsoft Office remains unverified. Controlled MCP and REST desktop workflows passed window, mouse/keyboard, UIA and screenshot checks at physical resolution `1920×1200`. The initial REST attempt stopped at the fixture's foreground check and remains a recorded failure; a separate 2026-10-23 rerun passed with physical DPI coordinates and explicit click-target/input-focus checks, without product changes. This does not establish every GUI operation or host combination. Remote reads passed with MySQL `8.4`, PostgreSQL `14`, SQL Server `2019 Developer` and Oracle `21c XE`, using installed optional drivers and a native Oracle client. This does not establish every server/driver combination or Linux Engine compatibility. SQL Server 2022 did not start reliably on the tested kernel 3.10 host and is not included in that evidence. Access remains an existing type without an installed test driver. No configured real model provider was available; that check was skipped at the user's direction.

## Contract and identity rules

- Node package versions, MCP wire versions, integration `contractVersion`, `profileSchemaVersion`, managed Client protocol and category contract versions are independent. Display `serviceVersion` is informational. The node checks required control operations and versions before execution; unsupported contracts fail closed.
- Published workflows use immutable `projectId` plus explicit version and profile revision. A display-name change does not change the target. Republishing or changing admission requires a new reviewed declaration; it does not rewrite a frozen receipt or make an uncertain start safe to repeat.
- Adding Engine components or variable types requires an operation-level classification, admission review, bounded serialization/transfer decisions and related regressions. A catalog entry is not permission to execute an operation.

## Deprecation and candidate gates

Before removing/renaming a tool, adding required inputs, or changing authentication or state semantics, document the replacement and migration in release notes and retain the old supported contract for at least one announced migration release. A breaking change requires a new contract version and explicit support matrix entry. Security fixes may shorten that period only with a documented maintainer decision; no silent transport fallback is a migration mechanism.

Every n8n, SDK, Client or contract upgrade must run the relevant CI suites, proxy protocol tests, credential/admission checks and actual start/query/result/error flows. A deployment upgrade or rollback also requires discovery, a synthetic execution, identity-preserving recovery and cancellation smoke checks. Keep the previous package, database/key backup and compatible Client resources; never erase receipts or downgrade schema to force retry.

The PR author/operator supplies host versions, package/source hashes, actual execution IDs, result assertions and unresolved environment checks. The maintainer reviews P0/P1 closure or explicitly accepts a documented exception before declaring the candidate ready. Passing CI is not evidence for Windows GUI/Office, full EXE packaging, remote databases or a real model provider.
