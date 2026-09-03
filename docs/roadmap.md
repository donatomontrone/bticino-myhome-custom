# Technical roadmap

Last reviewed: 2026-09-03 on post-0.2.0 `master` against Home Assistant 2026.9 integration-quality guidance.

The project remains local-first and capture-led. Protocol-sensitive behavior must be validated from real MH201/OpenWebNet traffic rather than inferred from numeric WHO/WHAT values. WHO=22, media player, audio, music and sound diffusion remain explicitly outside scope.

Two validation labels are used throughout this roadmap:

- **spec/reference validated**: the software behavior is derived from public BTicino/Legrand OpenWebNet documentation and cross-checked against established MyHOME implementations, with deterministic unit/mocked tests;
- **hardware validated**: the same behavior has also been confirmed against captures and runtime behavior from a real MH201/MyHOME installation.

## Development completion rule

Every implementation sprint must keep this roadmap synchronized with the code delivered in the same development cycle. A software change is not considered complete until the relevant roadmap items reflect its actual validation state and the same final `master` HEAD is green for the Home Assistant test matrix, Ruff, mypy, Hassfest and HACS validation. Hardware-dependent items remain explicitly pending until verified against a real MH201/MyHOME installation.

## Current checkpoint — post-0.2.0 master

Release 0.2.0 established the repository/architecture baseline. Subsequent `master` work has completed the software-side runtime/transport hardening phase and the software-side Home Assistant surface-quality phase: explicit command results, integration-owned post-negotiation channel semantics, initial-state hydration plumbing, conservative device lifecycle, safer active discovery, reconfigure/reauthentication, explicit inventory removal, typed runtime ConfigEntries, HA-native entity naming, deterministic multi-gateway raw-frame targeting, selector/data-description cleanup, translated entity action errors, hardened diagnostics redaction and expanded mocked regression coverage.

WHO=4 thermoregulation is now spec/reference aligned for the currently modeled surfaces, including explicit heating-only KW4691 zones. WHO=2 advanced-shutter software work is in progress: documented DIM=10 status/position decoding, DIM=11 go-to-level writes, explicit position capability, manual advanced-shutter configuration and Home Assistant `SET_POSITION` gating are implemented, while dedicated protocol/entity regression tests and physical MH201 validation remain pending.

CI is green against Home Assistant 2025.1 / Python 3.12 and Home Assistant 2026.9 / Python 3.14, with Ruff, mypy, pytest, Hassfest and HACS validation. The current HA 2026.9 quality target enforces a coverage gate of 55%; after the initial WHO=2 advanced-shutter implementation the current suite contains 81 tests and reports 65.12% integration-package coverage.

There is intentionally no requirement for a local/running Home Assistant instance during the remaining code-completion work. Integration-level Home Assistant lifecycle tests, clean-install/upgrade validation and physical MH201 validation are deferred to the final validation phase. Until then, development relies on code review, unit/mocked tests, public OpenWebNet specifications, established MyHOME implementations and CI compatibility checks.

The integration is not yet considered fully production-validated because a final Home Assistant lifecycle campaign, a physical MH201 clean-install/upgrade/runtime campaign and capture-backed verification of protocol-sensitive WHO families are still pending.

The working principle remains: **finish the software surface first, then validate against Home Assistant and real hardware at the end**. Protocol behavior is still capture-led: no numeric WHO/WHAT semantics are added merely to make the implementation look complete.

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

## Phase B — runtime solidity and transport hardening — COMPLETE SOFTWARE-SIDE

The remaining validation of BUS-specific semantics is intentionally tracked in Phases D/E/F rather than being inferred in this phase.

### Command/event lifecycle

- [x] Serialize persistent command-session access
- [x] Re-open a missing command session on the next command
- [x] Recover a failed command channel in the background while events remain alive
- [x] Never blindly retransmit an ambiguous failed frame from the integration recovery layer
- [x] Track command-channel and event-channel health separately
- [x] Aggregate entity availability from both channel states
- [x] Use Home Assistant-owned task creation for persistent gateway workers
- [x] Add command concurrency, missing-session recovery, background recovery, cancellation and close tests
- [x] Introduce an explicit command-result abstraction so ACK/NACK/status responses/transport failure are observable by the integration
- [x] Resolve reconnect/retry ownership after OWNd negotiation by letting the integration own command/event stream recovery semantics
- [x] Replace generic transport handling with structured connection/authentication/command/protocol exceptions
- [x] Log gateway availability transitions on state changes instead of on every retry cycle

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

- [x] Add initial-state hydration plumbing for WHO=1/2/3 without optimistic local state; real BUS query validation remains in Phase E
- [x] Remove unconditional/synthetic WHO=7 entities when no intercom endpoint has been observed or manually configured
- [x] Move the raw WHO=7 event surface to a diagnostic entity disabled by default
- [x] Propagate explicit DeviceManager removals to runtime entities and persisted inventory
- [x] Keep discovery snapshots merge-only so a missed response cannot be interpreted as device removal
- [x] Add DeviceManager/dynamic add-remove lifecycle coverage

### Discovery safety

- [x] Stop synthesizing scenario endpoints 1-30 during active discovery
- [x] Correlate active probes with responses that confirm the same WHO/WHERE endpoint
- [x] Add explicit probe rate limiting suitable for conservative SCS/OpenWebNet discovery
- [x] Surface gateway transport failure and stop active discovery instead of swallowing every probe failure
- [x] Validate known manual WHO/device-type combinations before persisting them

A separate low-level transport rewrite is not a goal. The focused adapter now owns only the semantics OWNd does not expose reliably after session negotiation.

## Phase C — code completion and Home Assistant surface quality — COMPLETE SOFTWARE-SIDE

This phase is complete without requiring a running Home Assistant instance. Home Assistant lifecycle/registry/flow validation using a real test instance remains deferred to Phase F.

- [x] Introduce a typed `ConfigEntry[BticinoMyHomeData]` alias in a cycle-safe runtime data module
- [x] Propagate the typed ConfigEntry alias through integration, platforms, dynamic lifecycle helpers, diagnostics and gateway-action code
- [x] Add reconfigure flow for host/port/password changes with stable serial/UDN conflict protection
- [x] Add an explicit reconfigure control for removing a previously stored OpenWebNet password
- [x] Add reauthentication flow and raise `ConfigEntryAuthFailed` for genuine credential failures
- [x] Add explicit endpoint removal from Options Flow and the Home Assistant `async_remove_config_entry_device` hook
- [x] Translate Config/Options action selectors and connection/authentication errors in English and Italian
- [x] Add `_attr_has_entity_name` and translation-key based names for secondary entities while keeping primary endpoint entities unnamed relative to their device
- [x] Use Home Assistant selectors and `data_description` consistently across Config/Options fields
- [x] Expose explicit manual WHO=4 heating/cooling profiles, including the KW4691 floor-heating-only use case
- [x] Keep `send_frame` as an advanced/debug action but require an explicit BTicino ConfigEntry target, making multi-gateway behavior deterministic
- [x] Register integration-wide actions from `async_setup` instead of one config-entry lifecycle
- [x] Translate `send_frame` validation/transport failures and action metadata in English and Italian
- [x] Translate entity command transport failures and climate validation errors using Home Assistant error translation surfaces
- [x] Add diagnostics/redaction regression tests and remove potentially sensitive ConfigEntry titles from diagnostics
- [x] Expand unit/mocked tests for Config Flow helpers, Options inventory persistence, thermal-profile persistence, explicit removal and changed-IP stable identity
- [x] Add coverage reporting with a 55% CI gate; current HA 2026.9 run is 65.12% across 81 tests after the initial WHO=2 advanced-shutter implementation

## Phase D — protocol evidence and deterministic replay

This phase starts only when real captures are available. No protocol-specific behavior is to be invented merely to complete the codebase.

- [ ] Build a sanitized real-capture fixture corpus grouped by WHO/device/action
- [ ] Add deterministic raw frame -> parsed frame -> normalized event -> entity state replay tests
- [ ] Record gateway model/firmware and safe installation context alongside captures
- [x] Conservatively reject parameterized standard `#WHERE` frames as endpoint evidence outside the explicit documented WHO=4 central-zone form
- [ ] Investigate diagnostic/broadcast/group frames per WHO and explicitly model or exclude them from endpoint discovery using real captures
- [ ] Revisit the flat `NormalizedEvent.state` model before complex WHO=5/18 payloads; introduce structured semantic payloads only when captures require them
- [ ] Move WHO-specific numeric semantics into dedicated protocol modules as each family becomes spec/reference validated and later capture-validated

## Phase E — protocol/platform coverage

### WHO=0 — scenarios
- [x] Scenario activation entity
- [x] Scenario device-trigger adapter
- [x] No synthetic 1-30 scenario inventory during active scan
- [ ] Real MH201 scenario event fixtures and end-to-end trigger validation

### WHO=1 — lighting
- [x] Basic on/off command and event state
- [x] Initial-state hydration request/response plumbing
- [ ] Add spec/reference-backed dimmer/brightness semantics only for devices that expose the required capability
- [ ] Complete observed WHAT catalogue from real captures
- [ ] Initial-state and dimmer query validation on a real MH201/BUS

### WHO=2 — automation / shutters — IN PROGRESS, SPEC/REFERENCE IMPLEMENTATION
- [x] Open / close / stop command and motion state
- [x] Initial-state hydration request/response plumbing
- [x] Introduce a dedicated `protocol/automation.py` boundary for documented advanced-shutter semantics
- [x] Model documented DIM=10 shutter status/position states, including `0..100` position and `255` unknown position
- [x] Add DIM=11 go-to-level command builder using the documented priority parameter and the established `#001` command form
- [x] Add explicit `position_control` capability and expose Home Assistant `SET_POSITION` only when the capability is configured or observed
- [x] Preserve unknown position as unknown and never estimate a percentage for basic shutters
- [x] Infer advanced-shutter capability only from a valid DIM=10 status frame; do not infer it from ordinary open/close/stop events
- [x] Add manual Options Flow support for explicitly marking a WHO=2 cover as an advanced shutter
- [x] Request DIM=10 initial state only for covers known to support advanced position reporting
- [x] Keep Home Assistant position/motion updates evidence-driven from received OpenWebNet events rather than optimistic local writes
- [x] Conservatively exclude parameterized/group `#WHERE` WHO=2 frames from endpoint discovery
- [ ] Add dedicated deterministic `protocol/automation.py` tests for valid/invalid DIM=10 frames, unknown position and DIM=11 command construction
- [ ] Add dedicated cover entity tests for feature gating, initial DIM=10 hydration, position updates and translated validation errors
- [ ] Complete observed automation WHAT catalogue from real captures
- [ ] Initial-state and advanced-position validation on a real MH201/BUS

### WHO=3 — load management
- [x] Basic on/off command and event state
- [x] Initial-state hydration request/response plumbing
- [ ] Initial-state query validation on a real MH201/BUS
- [ ] Complete observed load-management catalogue
- [ ] Validate whether additional measurements/states belong here or in WHO=18

### WHO=4 — thermoregulation — SPEC/REFERENCE VALIDATED, HARDWARE VALIDATION PENDING
- [x] Home Assistant climate entity exists
- [x] Dedicated `protocol/thermoregulation.py` for WHO=4 states, constants and command builders
- [x] Parser support for documented current dimension-response shapes and central-zone `#WHERE` standard events
- [x] Documented heating/conditioning/generic WHAT families and protection/manual/programming semantics
- [x] Explicit heating-only, cooling-only and heating+cooling zone capabilities
- [x] KW4691 floor-heating-only Home Assistant surface: OFF / HEAT / AUTO with anti-freeze protection and no exposed COOL
- [x] Manual Options Flow support for persisting an explicit thermal profile
- [x] Preserve standalone versus central-unit WHERE routing instead of forcing every zone through `#WHERE`
- [x] DIM=14 setpoint writes encode temperature plus operation-mode value with documented 0.5 °C steps
- [x] Conservative DIM=19 active-output decoding
- [x] Remove optimistic local mode/preset/setpoint updates; state requires received protocol evidence
- [x] WHO=4 protocol/climate/discovery regression tests
- [ ] Validate every read/write frame against real MH201/KW4691 thermoregulation captures
- [ ] Confirm whether each real installation zone is standalone or central-unit routed
- [ ] Validate setpoint-write acknowledgement/effect against real hardware
- [ ] Validate valve/HVAC-action semantics from real traffic

### WHO=5 — alarm — EXPERIMENTAL
- [x] Minimal alarm-control-panel surface exists
- [ ] Treat current WHAT/state mappings as provisional until real-installation confirmation
- [ ] Build alarm fixture catalogue from safe normal operations
- [ ] Distinguish arm, zone/event, fault/restore and alarm transitions only when observed
- [ ] Do not expand control semantics beyond capture-backed behavior

### WHO=7 — video door entry — EXPERIMENTAL
- [x] Initial call-event and door-release surfaces exist
- [x] Remove synthetic default entities and require observed/manual endpoint evidence
- [x] Keep the raw event surface diagnostic and disabled by default
- [ ] Build video door-entry fixture catalogue
- [ ] Validate call start/end semantics and WHERE routing
- [ ] Validate door-release command against real MH201 traffic

### WHO=18 — energy
- [x] Device family is classified by protocol/discovery
- [ ] Define spec/reference-backed typed measurements and Home Assistant device/state classes
- [ ] Implement production energy entities only where public dimension/unit semantics are unambiguous
- [ ] Build real energy-frame fixture catalogue
- [ ] Validate units, counters and update cadence on a real MH201/BUS

## Phase F — final Home Assistant and hardware validation

This is the first phase that requires an actual Home Assistant environment and, for hardware checks, the real MH201 installation. The automated code/CI work should be substantially complete before entering it.

### Home Assistant integration-level validation

- [ ] Full Config Flow tests using Home Assistant flow machinery: success, connection failure/recovery, invalid credentials, SSDP, duplicate entry, migration and changed-IP identity behavior
- [ ] Full Options Flow tests using Home Assistant flow machinery: active scan, passive learning, manual registration, selection, removal and persistence
- [ ] Setup / unload / reload / restart tests using a real Home Assistant test instance
- [ ] Entity lifecycle tests for every exposed platform
- [ ] Entity and Device Registry tests for stable identifiers, hub linkage and explicit removal
- [ ] Availability loss/recovery tests through Home Assistant state machinery
- [ ] Dynamic device add/remove tests through Home Assistant entity platforms
- [ ] Confirm diagnostics/redaction behavior in Home Assistant

### Installation and MH201 validation

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

0.2.0 is an architecture/runtime milestone, not a declaration that every protocol surface is hardware-validated. It is appropriate as a tagged development release because repository structure, compatibility CI, gateway recovery, native discovery and migration semantics form a coherent baseline. Post-0.2.0 `master` now has the software-side architecture/runtime and Home Assistant surface-quality phases complete; the current development focus is WHO=2 advanced automation/shutter coverage using public OpenWebNet specifications and established implementations, with final Home Assistant and MH201 validation intentionally deferred until the end of the project.
