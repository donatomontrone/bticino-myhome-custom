# Technical roadmap

Last reviewed: 2026-09-03 against the current `master` architecture and Home Assistant 2026.9 integration-quality guidance.

The project remains intentionally local-first and capture-led. Protocol-sensitive behavior must be validated from real MH201/OpenWebNet traffic rather than inferred from numeric WHO/WHAT values. WHO=22, media player, audio, music and sound-diffusion support remain explicitly outside the project scope.

## Current checkpoint

The repository foundation is established and CI is green against both the compatibility baseline (Home Assistant 2025.1 / Python 3.12) and the current target (Home Assistant 2026.9 / Python 3.14), with Ruff, mypy, pytest, Hassfest and HACS validation.

The architecture is suitable for continued development, but the integration is **not yet considered production-solid**. The main remaining risk is no longer repository structure: it is runtime behavior under disconnects/concurrency, stable Home Assistant identity/lifecycle, incomplete Home Assistant integration tests, and protocol behavior that still requires real MH201 captures.

The next milestone is therefore **runtime solidity before protocol breadth**. The internal quality target is to reach a Home Assistant Integration Quality Scale Silver-like level of robustness before expanding WHO=5/7/18 functionality. This is an engineering benchmark for this custom integration, not an official Home Assistant quality-tier claim.

## Phase A — repository and architecture foundation

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

## Phase B — runtime solidity and transport hardening — NEXT

### Command/event lifecycle

- [ ] Serialize access to the persistent command session so concurrent entity/discovery commands cannot overlap
- [ ] Define and test command-session self-healing after disconnect/reset/timeout
- [ ] Introduce an explicit command-result abstraction above OWNd so ACK/NACK/transport failure are not represented only by logging
- [ ] Audit the overlap between OWNd internal reconnect/retry behavior and the integration gateway lifecycle; keep one clear owner for each recovery path
- [ ] Distinguish event-stream health from command/control health when computing integration/entity availability
- [ ] Use Home Assistant-owned task creation/lifecycle for the persistent event worker
- [ ] Replace generic `BticinoGatewayError` cases with structured connection/authentication/command/protocol exceptions
- [ ] Log availability transitions once when unavailable and once when recovered instead of logging every retry cycle
- [ ] Add command concurrency, command recovery, reconnect, cancellation and close-during-retry tests

### Gateway identity and discovery

- [ ] Fix gateway discovery to use the actual OWNd discovery API (`OWNd.discovery.find_gateways`) instead of the unavailable `OWNGateway.discover` path
- [ ] Add native Home Assistant SSDP discovery for MH201 while preserving manual host/port setup
- [ ] Prefer stable gateway serial/UDN identity instead of host:port for ConfigEntry/device/entity identity
- [ ] Design a migration from current host:port identifiers that preserves existing entity history and registry entries
- [ ] Register the MH201 as the hub device and link OpenWebNet endpoint devices through `via_device`

### Device runtime state

- [ ] Hydrate initial state after entity setup for capture-validated WHO families instead of waiting indefinitely for the next bus event
- [ ] Remove unconditional/synthetic WHO=7 entities when no intercom endpoint has been observed or manually configured
- [ ] Move the raw WHO=7 event sensor out of the normal entity surface, or mark it diagnostic and disabled by default
- [ ] Propagate DeviceManager removals so stale Home Assistant entities/devices can be removed coherently
- [ ] Add stale-device and dynamic add/remove lifecycle tests

### Discovery safety

- [ ] Correlate active probes with the responses that confirm them
- [ ] Add explicit probe rate limiting/batching suitable for the SCS/OpenWebNet bus
- [ ] Stop or surface active discovery when gateway transport becomes unavailable instead of silently swallowing every probe failure
- [ ] Validate manual WHO/device-type combinations so impossible semantic combinations cannot be persisted

A separate low-level transport rewrite is **not** currently a goal. A dedicated adapter may be introduced only where OWNd does not expose the lifecycle/result semantics required by the integration.

## Phase C — Home Assistant integration quality

- [ ] Introduce a typed `ConfigEntry[BticinoMyHomeData]` alias and use it throughout the integration
- [ ] Full Config Flow tests: success, connection failure/recovery, invalid credentials, duplicate entry and migration behavior
- [ ] Full Options Flow tests: active scan, passive learning, manual registration, selection and persistence
- [ ] Add a reconfigure flow for host/port/password changes without removing the integration
- [ ] Add a reauthentication flow and raise `ConfigEntryAuthFailed` for genuine credential failures
- [ ] Setup / unload / reload / restart tests using a real Home Assistant test instance
- [ ] Entity lifecycle tests for every exposed platform
- [ ] Entity and Device Registry tests, including stable identifiers and `via_device`
- [ ] Availability loss/recovery tests
- [ ] Diagnostics and redaction tests
- [ ] Dynamic device add/remove tests
- [ ] Add `_attr_has_entity_name` and move default entity names to translation keys where appropriate
- [ ] Use selectors and `data_description` consistently in Config/Options flows
- [ ] Review `send_frame` as an advanced/debug action: require explicit gateway targeting for multi-entry setups or move it out of the normal user surface
- [ ] Translate user-facing action/connection exceptions
- [ ] Add test coverage reporting and target >95% integration-module coverage before release candidate
- [ ] Maintain an internal Home Assistant Integration Quality Scale checklist, targeting Silver-like robustness first

## Phase D — protocol evidence and deterministic replay

- [ ] Build a sanitized real-capture fixture corpus grouped by WHO/device/action
- [ ] Add deterministic fixture replay tests from raw OpenWebNet frame -> parsed frame -> normalized event -> entity state
- [ ] Record gateway model/firmware and installation context alongside captures when safe and useful
- [ ] Investigate diagnostic/broadcast/group frames and explicitly exclude frames that must not create endpoint devices
- [ ] Revisit the flat `NormalizedEvent.state` model before adding complex WHO=5/18 payloads; introduce typed/structured semantic payloads only when real captures require them
- [ ] Move WHO-specific numeric semantics out of Home Assistant platform files and into protocol modules as each family becomes capture-validated

## Phase E — protocol and platform coverage

### WHO=0 — scenarios

- [x] Scenario activation entity
- [x] Scenario device-trigger adapter
- [ ] Real MH201 scenario event fixture set and end-to-end trigger validation

### WHO=1 — lighting

- [x] Basic on/off command and event state
- [ ] Initial-state query validation
- [ ] Complete observed WHAT catalogue
- [ ] Dimmer/brightness support only if confirmed by real captures and installed devices

### WHO=2 — automation / shutters

- [x] Open / close / stop command and motion state
- [ ] Initial-state query validation
- [ ] Complete observed shutter/automation WHAT catalogue
- [ ] Position support only where real devices expose a reliable position model

### WHO=3 — load management

- [x] Basic on/off command and event state
- [ ] Initial-state query validation
- [ ] Complete observed load-management catalogue
- [ ] Validate whether additional measurements/states belong here or in WHO=18

### WHO=4 — thermoregulation

- [x] Experimental Home Assistant climate entity exists
- [x] Parser support for observed dimension-response shapes
- [x] Basic HVAC mode / setpoint / temperature unit tests
- [ ] Validate every read and write frame against real MH201 thermoregulation captures before declaring climate support stable
- [ ] Validate setpoint-write value/mode semantics rather than inferring optional dimension values
- [ ] Move thermoregulation-specific builders/decoders/mappings into a dedicated protocol module after capture validation
- [ ] Validate valve/HVAC-action semantics from real traffic

### WHO=5 — alarm

- [x] Minimal alarm-control-panel surface exists
- [ ] Treat current WHAT/state mappings as provisional until confirmed from real installations
- [ ] Build alarm fixture catalogue from safe normal operations on real installations
- [ ] Distinguish arm state, zone/event state, fault/restore and alarm transitions only when observed
- [ ] Do not expand control semantics beyond capture-backed behavior

### WHO=7 — video door entry

- [x] Initial call-event and door-release surfaces exist
- [ ] Remove synthetic default entities and require observed/manual endpoint evidence
- [ ] Build video door-entry event fixture catalogue
- [ ] Validate call start/end semantics and WHERE routing
- [ ] Validate door-release command against real MH201 traffic before declaring it stable

### WHO=18 — energy

- [x] Device family is classified by the protocol/discovery model
- [ ] Build real energy-frame fixture catalogue
- [ ] Define typed energy measurement semantics and Home Assistant device/state classes
- [ ] Implement energy entities only after units, dimensions and counters are confirmed

## Phase F — documentation and release readiness

- [ ] Synchronize README capability/version statements with the actual 0.1.13 development line
- [ ] Correct README gateway-discovery claims to match the implemented Config Flow
- [ ] Document experimental vs capture-validated protocol families explicitly
- [ ] Document supported/unsupported gateway/device families and known limitations
- [ ] Document scenario triggers and the advanced raw-frame action if it remains exposed
- [ ] Decide and document the supported Home Assistant version window; keep the CI compatibility baseline only while it provides real maintenance value
- [ ] Runtime validation on a real MH201
- [ ] HACS installation validation
- [ ] Clean-install validation
- [ ] Upgrade/migration validation from the previous released configuration model
- [ ] Restart/reload validation on a real Home Assistant instance
- [ ] Final troubleshooting pass using real failure cases
- [ ] Release candidate

## Release gate

A release candidate should not be considered ready merely because CI is green. The minimum gate is:

1. command and event channels recover predictably;
2. ConfigEntry/entity/device identities survive restart and gateway address changes;
3. core entity state is hydrated and availability is trustworthy;
4. Home Assistant lifecycle/configuration paths have integration-level tests;
5. protocol-sensitive features advertised as stable are backed by real MH201 captures;
6. HACS/Hassfest/CI remain green on the supported Home Assistant range;
7. clean install, upgrade and real MH201 runtime validation have been completed.
