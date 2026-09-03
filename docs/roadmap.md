# Technical roadmap

Last reviewed: 2026-09-03 on post-0.2.0 `master` against Home Assistant 2026.9 integration-quality guidance.

The project is local-first and capture-led. Protocol-sensitive behavior must be validated from official BTicino/Legrand OpenWebNet documentation, established MyHOME implementations and, when available, real MH201 captures. Numeric WHO/WHAT values are never treated as sufficient evidence on their own.

## Permanent scope exclusions

The following surfaces are intentionally outside this project and must not be introduced as future roadmap items unless the project scope is explicitly changed:

- WHO=22;
- media player;
- audio, music and sound diffusion;
- WHO=1 dimmer / brightness / transition control.

WHO=1 support for this MH201 integration is intentionally limited to basic lighting ON/OFF control and state.

## Validation labels

- **spec/reference validated**: behavior is derived from public BTicino/Legrand OpenWebNet documentation and cross-checked against established MyHOME implementations, with deterministic unit/mocked tests;
- **hardware validated**: the same behavior has also been confirmed against captures and runtime behavior from a real MH201/MyHOME installation.

## Development completion rule

Every implementation sprint must keep this roadmap synchronized with the code delivered in the same development cycle. A software change is not considered complete until the relevant roadmap items reflect its actual validation state and the same final `master` HEAD is green for the Home Assistant test matrix, Ruff, mypy, Hassfest and HACS validation. Hardware-dependent items remain explicitly pending until verified against a real MH201/MyHOME installation.

## Current checkpoint — post-0.2.0 master

Release 0.2.0 established the repository/architecture baseline. Subsequent `master` work completed the software-side runtime/transport hardening phase and Home Assistant surface-quality phase.

WHO=4 thermoregulation is spec/reference aligned for the currently modeled surfaces, including explicit heating-only KW4691 zones. WHO=2 advanced-shutter position is spec/reference validated software-side: DIM=10 status/position decoding, DIM=11 go-to-level writes, explicit position capability, manual advanced-shutter configuration, Home Assistant `SET_POSITION`, unknown-position preservation and deterministic protocol/entity regression tests are implemented.

WHO=1 remains ON/OFF only by design. Dimmer/brightness support is permanently excluded from the current project scope.

CI is green against Home Assistant 2025.1 / Python 3.12 and Home Assistant 2026.9 / Python 3.14, with Ruff, mypy, pytest, Hassfest and HACS validation. The current HA 2026.9 quality target enforces a coverage gate of 55%; after the WHO=2 advanced-shutter test sprint the suite contains 126 tests and reports 68.90% integration-package coverage.

A local/running Home Assistant instance is not required for the remaining software-side work. Integration-level lifecycle testing, clean-install/upgrade validation and physical MH201 validation are deferred to Phase F.

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

### Command/event lifecycle

- [x] Serialize persistent command-session access
- [x] Re-open a missing command session on the next command
- [x] Recover a failed command channel in the background while events remain alive
- [x] Never blindly retransmit an ambiguous failed frame from the integration recovery layer
- [x] Track command-channel and event-channel health separately
- [x] Aggregate entity availability from both channel states
- [x] Use Home Assistant-owned task creation for persistent gateway workers
- [x] Add command concurrency, recovery, cancellation and close tests
- [x] Introduce explicit command-result handling
- [x] Let the integration own post-negotiation command/event recovery semantics
- [x] Use structured connection/authentication/command/protocol exceptions
- [x] Log availability transitions only on state changes

### Gateway identity and discovery

- [x] Use `OWNd.discovery.find_gateways()`
- [x] Native Home Assistant SSDP discovery for MH201
- [x] Manual host/port fallback
- [x] Prefer serial, then UDN, then host/port for new gateway identity
- [x] ConfigEntry version 3 migration preserving existing entity identity/history
- [x] Associate a stable serial/UDN with a changed IP address
- [x] Register MH201 as hub device
- [x] Link endpoint devices to the hub through Device Registry parent/via semantics

### Device runtime state and discovery safety

- [x] Initial-state hydration plumbing for WHO=1/2/3 without optimistic state
- [x] Remove synthetic WHO=7 entities
- [x] Keep raw WHO=7 event surface diagnostic and disabled by default
- [x] Propagate explicit DeviceManager removals to runtime entities and inventory
- [x] Keep discovery snapshots merge-only
- [x] DeviceManager/dynamic add-remove coverage
- [x] Stop synthesizing WHO=0 addresses 1-30 during active discovery
- [x] Response-correlated active probes
- [x] Conservative SCS/OpenWebNet probe rate limiting
- [x] Surface gateway failure during active discovery
- [x] Validate manual WHO/device-type combinations

## Phase C — code completion and Home Assistant surface quality — COMPLETE SOFTWARE-SIDE

- [x] Typed `ConfigEntry[BticinoMyHomeData]`
- [x] Typed ConfigEntry propagated through integration/platform helpers
- [x] Reconfigure host/port/password with stable identity conflict protection
- [x] Explicit stored-password removal
- [x] Reauthentication and `ConfigEntryAuthFailed`
- [x] Explicit endpoint removal from Options Flow and Device Registry
- [x] Home Assistant selectors and `data_description`
- [x] English/Italian flow and action translations
- [x] HA-native entity naming / translation keys
- [x] Manual WHO=4 heating/cooling profiles, including heating-only KW4691 zones
- [x] Deterministic multi-gateway `send_frame`
- [x] Integration-wide action registration from `async_setup`
- [x] Translated entity command and climate validation errors
- [x] Diagnostics/redaction regression tests
- [x] Mocked Config/Options/inventory/changed-IP tests
- [x] Coverage reporting with 55% CI gate; current validated baseline 126 tests / 68.90%

## Phase D — protocol evidence and deterministic replay

This phase starts when real captures are available. No protocol-specific behavior is to be invented merely to make the implementation look complete.

- [ ] Build sanitized real-capture fixtures grouped by WHO/device/action
- [ ] Raw frame -> parsed frame -> normalized event -> entity state replay tests
- [ ] Record gateway model/firmware and safe installation context with captures
- [x] Reject parameterized standard `#WHERE` endpoint evidence outside explicit WHO=4 central-zone handling
- [ ] Investigate diagnostic/broadcast/group frames per WHO using real captures
- [ ] Revisit flat `NormalizedEvent.state` before complex WHO=5/18 payloads
- [ ] Move additional WHO-specific semantics into dedicated protocol modules only when evidence supports them

## Phase E — protocol/platform coverage

### WHO=0 — scenarios

- [x] Scenario activation entity
- [x] Scenario device-trigger adapter
- [x] No synthetic scenario inventory during active scan
- [ ] Real MH201 scenario fixtures and end-to-end trigger validation

### WHO=1 — lighting — ON/OFF ONLY BY PROJECT SCOPE

- [x] Basic ON/OFF command and event state
- [x] Initial-state hydration request/response plumbing
- [ ] Complete observed ON/OFF WHAT catalogue from real captures
- [ ] Initial-state query validation on a real MH201/BUS

Dimmer, brightness and transition semantics are permanently excluded from this integration scope.

### WHO=2 — automation / shutters — ADVANCED POSITION SPEC/REFERENCE VALIDATED, HARDWARE VALIDATION PENDING

- [x] Open / close / stop command and motion state
- [x] Initial-state hydration request/response plumbing
- [x] Dedicated `protocol/automation.py`
- [x] DIM=10 advanced shutter status/position, including `0..100` and `255` unknown
- [x] DIM=11 go-to-level command with explicit priority
- [x] Explicit `position_control` capability
- [x] Home Assistant `SET_POSITION` only when configured/observed
- [x] Never estimate percentage for basic shutters
- [x] Capability inferred only from valid DIM=10 evidence
- [x] Manual Options Flow advanced-shutter flag
- [x] DIM=10 initial-state request only for advanced covers
- [x] Evidence-driven position/movement updates; no optimistic writes
- [x] Reject parameterized/group `#WHERE` as endpoint discovery evidence
- [x] Deterministic `protocol/automation.py` tests
- [x] Cover entity tests for feature gating, hydration, events and translated errors
- [ ] Complete observed automation WHAT catalogue from real captures
- [ ] Initial-state and advanced-position validation on a real MH201/BUS

### WHO=3 — load management

- [x] Basic ON/OFF command and event state
- [x] Initial-state hydration request/response plumbing
- [ ] Initial-state query validation on a real MH201/BUS
- [ ] Complete observed load-management catalogue
- [ ] Validate whether additional measurements/states belong here or in WHO=18

### WHO=4 — thermoregulation — SPEC/REFERENCE VALIDATED, HARDWARE VALIDATION PENDING

- [x] Home Assistant climate entity
- [x] Dedicated `protocol/thermoregulation.py`
- [x] Current dimension-response parsing and central-zone `#WHERE` support
- [x] Heating/conditioning/generic WHAT families and protection/manual/programming semantics
- [x] Heating-only, cooling-only and heating+cooling capabilities
- [x] Heating-only KW4691 surface: OFF / HEAT / AUTO + anti-freeze
- [x] Manual Options Flow thermal profile persistence
- [x] Preserve standalone vs central-unit WHERE routing
- [x] DIM=14 setpoint writes with 0.5 °C steps and operation mode
- [x] Conservative DIM=19 active-output decoding
- [x] No optimistic local mode/preset/setpoint updates
- [x] WHO=4 protocol/climate/discovery regression tests
- [ ] Validate read/write frames against real MH201/KW4691 captures
- [ ] Confirm standalone vs central routing per real zone
- [ ] Validate setpoint-write acknowledgement/effect on real hardware
- [ ] Validate valve/HVAC-action semantics from real traffic

### WHO=5 — alarm — EXPERIMENTAL

- [x] Minimal alarm-control-panel surface
- [ ] Keep current WHAT/state mappings provisional until real-installation confirmation
- [ ] Build safe alarm fixture catalogue
- [ ] Distinguish arm, zone/event, fault/restore and alarm transitions only when observed
- [ ] Do not expand control semantics beyond capture-backed behavior

### WHO=7 — video door entry — EXPERIMENTAL

- [x] Initial call-event and door-release surfaces
- [x] Require observed/manual endpoint evidence
- [x] Raw event surface diagnostic and disabled by default
- [ ] Build video door-entry fixture catalogue
- [ ] Validate call start/end semantics and WHERE routing
- [ ] Validate door-release command against real MH201 traffic

### WHO=18 — energy

- [x] Device family classified by protocol/discovery
- [ ] Define spec/reference-backed typed measurements and HA device/state classes
- [ ] Implement production energy entities only where dimension/unit semantics are unambiguous
- [ ] Build real energy-frame fixture catalogue
- [ ] Validate units, counters and update cadence on a real MH201/BUS

## Phase F — final Home Assistant and hardware validation

### Home Assistant integration-level validation

- [ ] Full Config Flow tests with HA flow machinery
- [ ] Full Options Flow tests with HA flow machinery
- [ ] Setup / unload / reload / restart tests in a real HA test instance
- [ ] Entity lifecycle tests for every exposed platform
- [ ] Entity and Device Registry stability/removal tests
- [ ] Availability loss/recovery through HA state machinery
- [ ] Dynamic device add/remove through HA entity platforms
- [ ] Confirm diagnostics/redaction in Home Assistant

### Installation and MH201 validation

- [x] README synchronized with the 0.2.0 implementation baseline
- [x] Native SSDP, stable identity and migration documented
- [x] Experimental vs implemented protocol families documented
- [x] Dual Home Assistant CI window documented
- [x] Changelog/version metadata for 0.2.0
- [ ] Runtime validation on a real MH201
- [ ] HACS installation validation from the tagged release
- [ ] Clean-install validation
- [ ] Upgrade validation from 0.1.x
- [ ] Restart/reload and changed-IP validation on a real HA instance
- [ ] Final troubleshooting pass using real failure cases
- [ ] Production-ready release candidate after the above validation

## Release boundary

0.2.0 remains an architecture/runtime milestone, not a declaration that every protocol surface is hardware-validated. Post-0.2.0 `master` has the software-side architecture/runtime and Home Assistant surface-quality phases complete. WHO=2 advanced position and WHO=4 thermoregulation are spec/reference validated for their currently modeled software surfaces, while hardware/capture validation remains pending. WHO=1 remains deliberately ON/OFF-only; dimmer/brightness support is not part of this project.