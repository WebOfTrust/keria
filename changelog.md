# Changelog

## 0.4.1 - Unreleased

Changes since [0.4.0](https://github.com/WebOfTrust/keria/compare/0.4.0...9f38d063807620cca89d00e9119362a6fe850020), including the dependency upgrade from KERIpy `1.2.12` through `1.2.13` to `1.2.14`. HIO remains pinned to `0.6.14`; Python `>=3.12.2` is still required.

### Authentication and API behavior

- Added ESSR client authentication alongside signed HTTP headers. Clients can tunnel signed, encrypted requests through `POST /` and receive encrypted responses. Exposed authentication headers through CORS and improved signed-header error reporting. ([#351](https://github.com/WebOfTrust/keria/pull/351))
- Made the ESSR tunnel byte-transparent, including binary bodies, trailing whitespace, and correct byte-based content lengths; malformed envelopes return `401`. ([#456](https://github.com/WebOfTrust/keria/pull/456))
- Fixed controller-rotation authentication to use the updated authenticator contract and reject invalid request signatures. ([#451](https://github.com/WebOfTrust/keria/pull/451))
- Added `GET /locschemes/{eid}` to retrieve a known endpoint identifier's location schemes. ([#437](https://github.com/WebOfTrust/keria/pull/437))
- Bound end-role and location-scheme reply signatures to the last establishment event, allowing replies after interaction events to validate against the correct keys. ([#461](https://github.com/WebOfTrust/keria/pull/461))

### Delegation, credentials, and operations

- Added KERIpy-compatible `/delegate/request` EXN sending and receiving, including singlesig delegation requests and notifications. Approval remains an explicit delegator action; documented the sender/proxy KEL prerequisites and notification flow. ([#432](https://github.com/WebOfTrust/keria/pull/432))
- Fixed IPEX grant artifact gathering for untargeted credentials and undisclosed issuees, while retaining issuer and available delegation-chain artifacts. ([#453](https://github.com/WebOfTrust/keria/pull/453))
- Fixed `keria sig-fix` scheduler execution and database iteration, closed intermediate databases to avoid LMDB reader-slot failures, and skipped/reported malformed controller records or habitats without key state. ([#431](https://github.com/WebOfTrust/keria/pull/431), [#458](https://github.com/WebOfTrust/keria/pull/458))
- Corrected generated OpenAPI schemas for ACDC ordering and extension fields, credential and registry states, anchoring attachments, key events, and nested group-member endpoints. Corrected operation dependency types, required registry dependencies, boolean `done` constants, and delegated inception/rotation embeds. ([#428](https://github.com/WebOfTrust/keria/pull/428), [#441](https://github.com/WebOfTrust/keria/pull/441), [#446](https://github.com/WebOfTrust/keria/pull/446), [#448](https://github.com/WebOfTrust/keria/pull/448))

### Configuration and scheduling

- Fixed startup to honor the supplied agent configuration parameters. ([#397](https://github.com/WebOfTrust/keria/pull/397))
- Added validated scheduler configuration for long-running Agency/Agent tasks under `tocks.signify`, with KERIpy service settings directly under `tocks`. Resolution uses KERIpy's resolver with precedence `specific env > coarse env > specific config > coarse config > default`. Invalid or unknown settings fail at load time. ([#465](https://github.com/WebOfTrust/keria/pull/465))
- Retained legacy flat KERIA tock names with deprecation warnings; identical legacy/canonical duplicates are accepted and conflicting duplicates rejected. Migrate these names to `tocks.signify`; removal will be announced in a future release.
- Defaulted registered work cadences to `0.03125` seconds (one 32 Hz scheduler tick), with explicit `0.0` supported. The idle-Agent release scan remains `60.0` seconds; its inactivity timeout remains separate. Removed the fixed half-second delegation escrow delay and threaded configured or parent cadences through parser waits, witness receipt/resubmission, query/grant workers, servers, and shutdown.
- Added Agent-owned signal expiry with a configurable scan cadence and safe iteration while notifications are queued. The ten-minute signal lifetime is unchanged.
- Defined configuration snapshots: new Agents inherit configured Agency values; reopened Agents load their own persisted files. Defaults and environment overrides are not persisted, changes do not live-reload, and Agency template edits do not overwrite existing Agent configuration. Fixed reopening when database and configuration bases differ. Added complete sample configurations and scheduling documentation.

### KERIpy dependency changes used by KERIA

KERIA `0.4.0` pinned `keri==1.2.12`. This release first upgraded to `1.2.13` and then to the published `keri==1.2.14`, retaining the matching `hio==0.6.14` dependency. ([#434](https://github.com/WebOfTrust/keria/pull/434), [#464](https://github.com/WebOfTrust/keria/pull/464))

- **1.2.13 — registry storage:** prevented a `Reger` LMDB environment from being opened twice. ([KERIpy #1366](https://github.com/WebOfTrust/keripy/pull/1366))
- **1.2.14 — scheduler contracts:** centralized tock configuration and environment overrides, preserved generator-local cadences, corrected parser scheduler boundaries, and clarified Signaler scheduling ownership. These provide the resolver and runtime behavior used by KERIA's scheduling configuration. ([#1585](https://github.com/WebOfTrust/keripy/pull/1585), [#1592](https://github.com/WebOfTrust/keripy/pull/1592), [#1593](https://github.com/WebOfTrust/keripy/pull/1593), [#1594](https://github.com/WebOfTrust/keripy/pull/1594))
- **Parsing and encrypted exchange:** aligned SPAC/ESSR processing, retained ESSR attachments across exchange escrow retries, consumed KERI/ACDC genus-version counters, handled incomplete Serders as shortages, and corrected the CESR Ed448 signature size. ([#1565](https://github.com/WebOfTrust/keripy/pull/1565), [#1603](https://github.com/WebOfTrust/keripy/pull/1603), [#1447](https://github.com/WebOfTrust/keripy/pull/1447), [#1634](https://github.com/WebOfTrust/keripy/pull/1634), [#1601](https://github.com/WebOfTrust/keripy/pull/1601))
- **Credentials and notifications:** added revocation details and correct sequence handling to cloned credentials, honored explicitly supplied ACDC issuees, and suppressed IPEX notifications for the local initiator. ([#1599](https://github.com/WebOfTrust/keripy/pull/1599), [#1600](https://github.com/WebOfTrust/keripy/pull/1600), [#1604](https://github.com/WebOfTrust/keripy/pull/1604))
- **Multisig and discovery:** fixed exchange leader election for `SignifyGroupHab`, made query-not-found escrow retries idempotent, and retained endpoint identifiers from OOBI replies when available. ([#1597](https://github.com/WebOfTrust/keripy/pull/1597), [#1579](https://github.com/WebOfTrust/keripy/pull/1579), [#1606](https://github.com/WebOfTrust/keripy/pull/1606))
- **Witness delivery:** fixed publisher lifecycle tracking, admitted TCP stream payloads for delivery, avoided redundant messenger creation for completed receipts, and made HTTP/TCP messenger idle state reflect queued and active work rather than stale connection state. ([#1651](https://github.com/WebOfTrust/keripy/pull/1651), [#1653](https://github.com/WebOfTrust/keripy/pull/1653), [#1655](https://github.com/WebOfTrust/keripy/pull/1655), [#1633](https://github.com/WebOfTrust/keripy/pull/1633), [#1657](https://github.com/WebOfTrust/keripy/pull/1657))

KERIpy `1.2.14` also adds operator-side registry rename, schema import, multisig import/export and catch-up workflows, witness query endpoints, and witness configuration/logging fixes. Its own Registrar now uses `Receiptor`, and its `sendArtifacts` handles untargeted credentials. These are dependency tools/services, not new KERIA REST endpoints; KERIA retains its own Registrar and artifact-gathering implementation. See the [complete KERIpy delta](https://github.com/WebOfTrust/keripy/compare/1.2.12...1.2.14) and [release history](https://github.com/WebOfTrust/keripy/blob/1.2.14/ref/ChangeLog.md) for CLI details. The experimental `gleif_hio` upgrade and deterministic TCP teardown changes were reverted before `1.2.14` and are not included.

### Build and documentation

- Refreshed GitHub Actions dependencies and repaired the Read the Docs configuration and documentation badge. ([#459](https://github.com/WebOfTrust/keria/pull/459), [#463](https://github.com/WebOfTrust/keria/pull/463), [#442](https://github.com/WebOfTrust/keria/pull/442))
- Aligned Makefile Docker tags with `0.4.1`, corrected the documented container commands and package-version maintenance comment, and made Docker publishing build the requested release tag with generated OCI labels and a package-version check.

## 0.4.0 - 2026-03-23

Changes in this draft cover the delta from `0.2.0-rc2` (`6ad36d5e171c599b078624c9ed4cd1c54e3c1b4a`) through `aba457cab3813078bfedb65a7d819f48d86974b8`.

### Summary

- Hardened credential, IPEX, and exchange flows by fixing deletion/index cleanup, first-grant artifact delivery, admit/grant parsing, escrowed credential reads, and outbound EXN indexing.
- Improved runtime behavior with cleaner shutdown semantics, better logging, optional request tracing, and log-level propagation into the underlying KERI stack.
- Refactored startup and configuration handling to improve testability, temp-mode correctness, and agency/agent config injection.
- Expanded and tightened the OpenAPI contract with generated schemas, typed operation models, and more accurate endpoint response definitions.
- Improved response-shape compatibility for identifiers, key-state records, multisig EXN payloads, and mixed client request formats.
- Modernized packaging and delivery by moving to `uv`, refreshing CI and Docker workflows, and upgrading KERI/KERIA runtime dependencies.

### Agent, credential, and exchange behavior

- Deleted credentials now also remove KERIA-specific search indexes, so filtered queries no longer return stale deleted records.
- IPEX grant delivery now includes the agent and controller KELs required to validate the first presented credential, fixing the long-standing first/double-present failure mode.
- Refactored IPEX grant processing around a dedicated `GrantDoer` that gathers dependent KEL, TEL, and chained-credential artifacts into one debuggable flow.
- IPEX admit/grant/apply/offer/agree handling now uses the agent parser consistently, preventing crashes such as the `NoneType ... ked` admit failure.
- Peer exchange parsing now indexes outbound EXN messages so sent exchanges are visible through local exchange indexes.
- `GET /credentials/{said}` now returns `404 Not Found` for escrowed or unsaved credentials instead of surfacing as `500`, including on the CESR path.
- Credential issuance now accepts either `ri` or legacy `ii` registry references and returns a clear `400` when neither is present.
- Identifier rename validation now rejects duplicate target names instead of allowing one AID rename to overwrite another.

### Runtime, logging, and operability

- Reworked shutdown handling so agency shutdown follows the HIO doer lifecycle, using shutdown flags and `KeyboardInterrupt` instead of forcing `Doist.exit()`.
- Improved logs with a truncated formatter, clearer habitat context, and full identifier logging for multi-agent runs.
- Disabled HTTP request logging by default and added a `--logrequests` CLI switch for opt-in tracing.
- Propagated the configured KERIA log level into the underlying KERI logger so verbosity stays aligned across both layers.
- Added a maintainer-facing `scripts/keria.json` config and a `MAINTAINERS.md` file.

### Configuration, startup, and testability

- Refactored server startup so agency creation and HTTP server wiring are split into smaller reusable functions.
- Made agency configuration more testable by allowing an external `Configer` to be injected and by merging per-agent config with configured controller, introduction, and data OOBI lists.
- Fixed temporary-mode handling so config files and LMDB state respect `temp` instead of partially writing persistent test data.

### API descriptions and generated schemas

- Added reusable OpenAPI-generation utilities and shifted more schema definitions to generated type-hint-driven models.
- Expanded OpenAPI coverage for credentialing endpoints, including credential, registry, credential-state, anchoring-event, and cloned-credential response shapes.
- Expanded OpenAPI coverage for identifier and agent endpoints, including typed responses for agent state, identifier listings, identifier details, key state, key event logs, OOBIs, and agent config.
- Expanded OpenAPI coverage for delegation, grouping, IPEX, notification, and peer exchange endpoints, including typed multisig EXN payloads and long-running operation responses.
- Reworked long-running operation schemas so OpenAPI distinguishes operation families such as OOBI, query, witness, delegation, end-role, and registry instead of exposing one loose generic object.
- Added and refined operation IDs, response payload schemas, and component references across the REST surface to support client generation and stricter schema validation.

### Type and response-shape compatibility

- Fixed `KeyStateRecord` typing and OpenAPI shape for `kt` and `nt`, allowing threshold fields to be represented as either strings or arrays.
- Split identifier response modeling into base and full `HabState` variants so list and detail endpoints can describe different field guarantees accurately.
- Relaxed `HabState` optionality for `state`, `transferable`, and `windexes` where those fields are not always present.
- Made `ExnMultisig` helper fields such as `groupName`, `memberName`, and `sender` optional in generated schemas instead of incorrectly requiring them.

### Dependency, packaging, and CI updates

- Upgraded KERI from `1.2.6` to `1.2.7`, including the HIO-compatible doer signature updates required by the newer runtime.
- Upgraded again to KERI `1.2.12` and bumped KERIA to `0.4.0`.
- Removed the explicit setuptools dependency and then migrated packaging from `setup.py` and `requirements.txt` to `pyproject.toml`, `uv`, and a checked-in `uv.lock`.
- Added `ruff` linting and formatting checks to the repo and CI workflow.
- Updated the Makefile with `uv`-based install, test, coverage, lint, and format targets.
- Updated the Docker build to run from the `uv`-managed environment and added a Docker validation step to CI.
- Adjusted CI/runtime dependencies to pin `uv`, downgrade `lmdb` for Docker compatibility, and move GitHub Actions macOS testing to `macos-15`.

## 0.3.0 - 2025-05-28

- Improved runtime logging with clearer formatting plus habitat name and prefix context in log messages.
- Simplified graceful shutdown behavior and related runtime lifecycle handling.
- Upgraded KERI to `1.2.6` and finalized the `0.3.0` version bump.

## 0.2.0-rc4 - 2025-05-28

- Fixed first-time IPEX grant/present flows by sending the agent and controller KELs needed by recipients to validate the credential chain.
- Fixed credential deletion cleanup so KERIA-specific search indexes are removed with the credential record.
- Removed the explicit setuptools dependency.

## 0.2.0-rc2 and Older Releases

### 0.2.0-rc2 - 2025-01-24

- Added an API for creating new location schemes.
- Fixed basic boot passwords to allow colon characters.
- Fixed delegated multisig rotation by always routing Signify group messages through the agent proxy.
- Upgraded KERI to `1.2.4`.

### 0.2.0-rc1 - 2025-01-13

- Added graceful shutdown handling for agents and the KERIA process, including `SIGTERM` support and the new serving/shutdown path.
- Returned `400` for invalid end-role signatures while preserving the multisig-required `UnverifiedReplyError` behavior.
- Refreshed release docs, Docker, CI, and `keria.json` documentation for the `0.2.0` release candidates.

### 0.2.0 / 0.2.0-dev6 - 2024-12-12

- Added experimental basic-auth protection for the boot endpoint.
- Added environment-variable-based server configuration.
- Exposed inception timestamps in identifier/hab info.
- Added credential deletion support and explicit `404` behavior after deletion.
- Added multi-arch Docker publishing support.

### 0.2.0-dev5 through 0.2.0-dev0 - 2024

- Expanded multisig and delegation support with delegation approval, delegated rotation fixes, multisig join/rotation fixes, submit/witness-receipt improvements, and better SignifyTS compatibility.
- Expanded IPEX and credential flows with apply/offer/agree endpoints, multisig IPEX support, direct credential verification from `(acdc, iss)`, registry read endpoints, and better recipient routing.
- Improved API usability with prefix-based identifier/addressing support, agent-config retrieval, `409` on already-booted agents, idle-agent release, and clearer long-running operation IDs and status handling.
- Added more REST and OpenAPI documentation, plus broader test coverage around delegation, multisig, witness receipts, revocation, and credential workflows.
- Kept pace with KERI/KERIpy, Falcon, Docker, and CI changes as the stack moved through the `1.2.x` transition.

### 0.1.3 and Earlier - 2024

- Established the early credential-registry lifecycle, including registry rename/join support, duplicate-name protection, and fixes for partially committed registry visibility.
- Added the first IPEX apply/offer/agree support and tightened early long-running-operation handling.
- Continued aligning with upstream KERI/KERIpy and Python runtime changes while filling in foundational tests and release automation.
