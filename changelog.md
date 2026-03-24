# Changelog

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
