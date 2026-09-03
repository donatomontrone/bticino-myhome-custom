# Technical roadmap

Last reviewed: 2026-09-03 for release 0.2.0 against Home Assistant 2026.9 integration-quality guidance.

The project remains local-first and capture-led. Protocol-sensitive behavior must be validated from real MH201/OpenWebNet traffic rather than inferred from numeric WHO/WHAT values. WHO=22, media player, audio, music and sound diffusion remain explicitly outside scope.

## Current checkpoint — 0.2.0

Release 0.2.0 completes the repository/architecture foundation and a substantial part of runtime/gateway hardening. CI is green against Home Assistant 2025.1 / Python 3.12 and Home Assistant 2026.9 / Python 3.14, with Ruff, mypy, pytest, Hassfest and HACS validation.

The integration is not yet considered fully production-validated because a physical MH201 clean-install/upgrade/runtime campaign and capture-backed verification of protocol-sensitive WHO families are still pending.

The working principle remains: **runtime solidity before protocol breadth**. The internal quality target is Silver-like Home Assistant integration robustness before broadening WHO=5/7/18 functionality. This is an engineering benchmark, not an official Home Assistant quality-tier claim.

## Phase A — repository and architecture foundation — COMPLETE

- [x] Dedicated `protocol/` package
- [x] Immutable parsed frame model
- [x] Normalized event model
- [x] Centralized command builders
- [x] ConfigEntry `runtime_data` container
- [x] Separate OpenWebNet command and event sessions
- [x] Persistent event worker with reconnect/backoff
- [x] Unified `DiscoveredDevice` model
- [x] Persistent ConfigEntry device inventory
- [x] Passive / active / manual discovery paths
- [x] Runtime dynamic entity-add path
- [x] WHO=0 scenario entities and device triggers
- [x] Diagnostics with sensitive-data redaction
- [x] Read-only OpenWebNet capture tool
- [x] HACS metadata and Hassfest validation
- [x] CI matrix for HA 2025.1 / Python 3.12 and HA 2026.9 / Python 3.14
- [x] Ruff and mypy quality gates on the current HA target

## Phase B — runtime solidity and transport hardening — IN PROGRESS

### Command/event lifecycle

- [x] Serialize persistent command-session access
- [x] Re-open a missing command session on the next command
- [x] Recover a failed command channel in the background while events remain alive
- [x] Never blindly retransmit an ambiguous failed frame from the integration recovery layer
- [x] Track command-channel and event-channel health separately
- [x] Aggregate entity availability from both channel states
- [x] Use Home Assistant-owned task creation for persistent gateway workers
- [x] Add command concurrency, missing-session recovery, background recovery, cancellation and close tests
- [ ] Introduce an explicit command-result abstraction above OWNd so ACK/NACK/transport failure are observable beyond logging
- [ ] Complete the ownership audit between OWNd internal reconnect/retry and integration recovery logic
- [ ] Replace generic `BticinoGatewayError` cases with structured connection/authentication/command/protocol exceptions
- [ ] Log availability transitions once when unavailable and once when recovered instead of on every retry cycle

### Gateway identity and discovery

- [x] Use the actual `OWNd.discovery.find_gateways()` discovery API
- [x] Add native Home Assistant SSDP discovery for MH201
- [x] Preserve manual host/port configuration as fallback
- [x] Prefer serial, then UDN, then host/port for new gateway ConfigEntry identity
- [x] Add ConfigEntry version 3 migration preserving existing 0.1.x entity identity/history
- [x] Allow discovered stable identity to associate an existing gateway after an address change
- [x] Register the MH201 as the Home Assistant hub device
- [x] Link endpoint devices to the MH201 hub with the Device Registry parent/via mechanism compatible with HA 2025.1 and 2026.9

### Device runtime state

- [ ] Hydrate initial state after entity setup for capture-validated WHO families
- [ ] Remove unconditional/synthetic WHO=7 entities when no intercom endpoint has been observed or manually configured
- [ ] Move the raw WHO=7 event sensor to diagnostics or mark it diagnostic and disabled by default
- [ ] Propagate DeviceManager removals so stale Home Assistant entities/devices can be removed coherently
- [ ] Add stale-device and dynamic add/remove lifecycle tests

### Discovery safety

- [x] Stop synthesizing scenario endpoints 1-30 during active discovery
- [ ] Correlate active probes with responses that confirm them
- [ ] Add explicit probe rate limiting/batching suitable for the SCS/OpenWebNet bus
- [ ] Stop or surface active discovery when gateway transport becomes unavailable instead of swallowing every probe failure
- [ ] Validate manual WHO/device-type combinations so impossible semantic combinations cannot be persisted

A separate low-level transport rewrite is not a goal. A focused adapter may be introduced only where OWNd does not expose lifecycle/result semantics required by the integration.

## Phase C — Home Assistant integration quality — NEXT MAJOR BLOCK

- [ ] Introduce a typed `ConfigEntry[BticinoMyHomeData]` alias and use it throughout
- [ ] Full Config Flow tests: success, connection failure/recovery, invalid credentials, SSDP, duplicate entry, migration and changed-IP identity behavior
- [ ] Full Options Flow tests: active scan, passive learning, manual registration, selection and persistence
- [ ] Add reconfigure flow for host/port/password changes
- [ ] Add reauthentication flow and raise `ConfigEntryAuthFailed` for genuine credential failures
- [ ] Setup / unload / reload / restart tests using a real Home Assistant test instance
- [ ] Entity lifecycle tests for every exposed platform
- [ ] Entity and Device Registry tests for stable identifiers and hub linkage
- [ ] Availability loss/recovery tests
- [ ] Diagnostics/redaction tests
- [ ] Dynamic device add/remove tests
- [ ] Add `_attr_has_entity_name` and translation-key based default entity names where appropriate
- [ ] Use selectors and `data_description` consistently in Config/Options flows
- [ ] Review `send_frame` as an advanced/debug action and require explicit gateway targeting for multi-entry setups if retained
- [ ] Translate user-facing action/connection exceptions
- [ ] Add coverage reporting and target >95% integration-module coverage before a production-ready release candidate

## Phase D — protocol evidence and deterministic replay

- [ ] Build a sanitized real-capture fixture corpus grouped by WHO/device/action
- [ ] Add deterministic raw frame -> parsed frame -> normalized event -> entity state replay tests
- [ ] Record gateway model/firmware and safe installation context alongside captures
- [ ] Investigate diagnostic/broadcast/group frames and explicitly exclude frames that must not create endpoint devices
- [ ] Revisit the flat `NormalizedEvent.state` model before complex WHO=5/18 payloads; introduce structured semantic payloads only when captures require them
- [ ] Move WHO-specific numeric semantics into dedicated protocol modules as each family becomes capture-validated

## Phase E — protocol/platform coverage

### WHO=0 — scenarios
- [x] Scenario activation entity
- [x] Scenario device-trigger adapter
- [x] No synthetic 1-30 scenario inventory during active scan
- [ ] Real MH201 scenario event fixtures and end-to-end trigger validation

### WHO=1 — lighting
- [x] Basic on/off command and event state
- [ ] Initial-state query validation
- [ ] Complete observed WHAT catalogue
- [ ] Dimmer/brightness only if confirmed by real captures/devices

### WHO=2 — automation / shutters
- [x] Open / close / stop command and motion state
- [ ] Initial-state query validation
- [ ] Complete observed automation WHAT catalogue
- [ ] Position support only where real devices expose a reliable model

### WHO=3 — load management
- [x] Basic on/off command and event state
- [ ] Initial-state query validation
- [ ] Complete observed load-management catalogue
- [ ] Validate whether additional measurements/states belong here or in WHO=18

### WHO=4 — thermoregulation — EXPERIMENTAL
- [x] Home Assistant climate entity exists
- [x] Parser support for current dimension-response shapes
- [x] Basic HVAC mode/setpoint/temperature unit tests
- [ ] Validate every read/write frame against real MH201 thermoregulation captures
- [ ] Remove optimistic local state changes unless protocol evidence requires them
- [ ] Validate setpoint-write value/mode semantics
- [ ] Move thermoregulation-specific builders/decoders into a dedicated protocol module after capture validation
- [ ] Validate valve/HVAC-action semantics from real traffic

### WHO=5 — alarm — EXPERIMENTAL
- [x] Minimal alarm-control-panel surface exists
- [ ] Treat current WHAT/state mappings as provisional until real-installation confirmation
- [ ] Build alarm fixture catalogue from safe normal operations
- [ ] Distinguish arm, zone/event, fault/restore and alarm transitions only when observed
- [ ] Do not expand control semantics beyond capture-backed behavior

### WHO=7 — video door entry — EXPERIMENTAL
- [x] Initial call-event and door-release surfaces exist
- [ ] Remove synthetic default entities and require observed/manual endpoint evidence
- [ ] Build video door-entry fixture catalogue
- [ ] Validate call start/end semantics and WHERE routing
- [ ] Validate door-release command against real MH201 traffic

### WHO=18 — energy
- [x] Device family is classified by protocol/discovery
- [ ] Build real energy-frame fixture catalogue
- [ ] Define typed measurements and Home Assistant device/state classes
- [ ] Implement production energy entities only after units/dimensions/counters are confirmed

## Phase F — release/readiness

- [x] Synchronize README with the 0.2.0 implementation
- [x] Document native SSDP, stable identity and migration behavior
- [x] Document experimental vs implemented protocol families
- [x] Document the dual Home Assistant CI window
- [x] Publish changelog/version metadata for 0.2.0
- [ ] Runtime validation on a real MH201
- [ ] HACS installation validation from the tagged release
- [ ] Clean-install validation
- [ ] Upgrade validation from a 0.1.x installation
- [ ] Restart/reload and changed-IP validation on a real Home Assistant instance
- [ ] Final troubleshooting pass using real failure cases
- [ ] Production-ready release candidate after the above validation

## 0.2.0 release boundary

0.2.0 is an architecture/runtime milestone, not a declaration that every protocol surface is hardware-validated. It is appropriate as a tagged development release because repository structure, compatibility CI, gateway recovery, native discovery and migration semantics now form a coherent baseline. Real MH201 validation remains the gate for declaring protocol-sensitive features production-solid.
