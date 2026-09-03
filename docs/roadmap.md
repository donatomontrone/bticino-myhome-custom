# Technical roadmap

Last reviewed: 2026-09-03 on post-0.2.0 `master` against Home Assistant 2026.9 integration-quality guidance.

The project is local-first and capture-led. Protocol-sensitive behavior must be validated from official BTicino/Legrand OpenWebNet documentation, established MyHOME implementations and, when available, real MH201 captures. Numeric WHO/WHAT values are never treated as sufficient evidence on their own.

## Permanent scope exclusions

The following surfaces are intentionally outside this project and must not be introduced as future roadmap items unless the project scope is explicitly changed:

- WHO=22;
- media player;
- audio, music and sound diffusion;
- WHO=1 dimmer / brightness / transition control;
- WHO=3 load-management semantics; energy management is modeled only through documented WHO=18 surfaces;
- video/audio streaming and camera entities for the VDE/HomeTouch target.

WHO=1 support for this MH201 integration is intentionally limited to basic lighting ON/OFF control and state. WHO=3 has been removed from runtime code, discovery, manual configuration and platform exposure and must not be reintroduced as an energy-management family.

## Validation labels

- **spec/reference validated**: behavior is derived from public BTicino/Legrand OpenWebNet documentation and cross-checked against established MyHOME implementations, with deterministic unit/mocked tests;
- **hardware validated**: the same behavior has also been confirmed against captures and runtime behavior from a real MH201/MyHOME installation.

For legacy BTicino commands that are documented outside the public WHO application note, the roadmap uses **reference-backed, hardware validation pending** rather than claiming the target 4200C/MH201 path has already been proven.

## Development completion rule

Every implementation sprint must keep this roadmap synchronized with the code delivered in the same development cycle. A software change is not considered complete until the relevant roadmap items reflect its actual validation state and the same final `master` HEAD is green for the Home Assistant test matrix, Ruff, mypy, Hassfest and HACS validation. Hardware-dependent items remain explicitly pending until verified against a real MH201/MyHOME installation.

## Current checkpoint — post-0.2.0 master

Release 0.2.0 established the repository/architecture baseline. Subsequent `master` work completed the software-side runtime/transport hardening phase and Home Assistant surface-quality phase.

WHO=1 is complete software-side for the deliberately restricted ON/OFF-only project scope. WHO=2 advanced-shutter position and WHO=4 thermoregulation are spec/reference validated for their currently modeled software surfaces. Real MH201/BUS validation remains pending for all three.

WHO=5 has been reworked around the actual BTicino 4200C target. The software now models documented central and partition status, eight partition sensors, evidence-driven alarm-panel state, reference-backed total arm/disarm, selected-active-partition arm and explicit single-partition active/partialized controls. All alarm control commands remain hardware-validation-pending on the target 4200C through MH201.

Door-entry handling is now separated from public WHO=7 multimedia semantics. The HomeTouch target uses a conservative reference-backed WHO=6 door-release surface plus disabled-by-default raw WHO=6/7 diagnostic capture. A ring binary sensor is intentionally pending until a stable HomeTouch/MH201 call-start and call-end frame is established from documentation/reference evidence or real capture. Public WHO=7 camera/multimedia controls are not exposed because audio/video streaming is outside scope.

WHO=18 has a deliberately narrow production surface that is spec/reference validated software-side: documented `5N` energy-meter endpoints expose read-only DIM=113 active power in watts using a Home Assistant `POWER`/`MEASUREMENT` sensor, with initial hydration and evidence-driven updates. Totalizers and other WHO=18 dimensions are deliberately deferred until their units, reset semantics and real MH201 behavior can be validated.

The latest software baseline contains 162 deterministic tests and reports 73.27% integration-package coverage on Home Assistant 2026.9 / Python 3.14. The coverage gate remains 55%. The final completion state for this roadmap revision still requires the same final `master` HEAD to be green for HA 2025.1 / Python 3.12, HA 2026.9 / Python 3.14, Ruff, mypy, pytest, Hassfest and HACS.

A local/running Home Assistant instance is not required for the remaining software-side work. Integration-level lifecycle testing can continue with deterministic/mocked Home Assistant test machinery; clean-install/upgrade validation and physical MH201 validation remain deferred to the final validation campaign.

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

- [x] Initial-state hydration plumbing for supported stateful families without optimistic state
- [x] Remove synthetic/guessed WHO=7 call entities
- [x] Keep raw WHO=6/7 door-entry/multimedia event capture diagnostic and disabled by default
- [x] Propagate explicit DeviceManager removals to runtime entities and inventory
- [x] Keep discovery snapshots merge-only
- [x] DeviceManager/dynamic add-remove coverage
- [x] Stop synthesizing WHO=0 addresses 1-30 during active discovery
- [x] Response-correlated active probes
- [x] Conservative SCS/OpenWebNet probe rate limiting
- [x] Surface gateway failure during active discovery
- [x] Validate manual WHO/device-type combinations
- [x] Remove WHO=3 from discovery, manual inventory and platform exposure

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
- [x] Coverage reporting with 55% CI gate; current validated software baseline 162 tests / 73.27%

## Phase D — protocol evidence and deterministic replay

This phase starts when real captures are available. No protocol-specific behavior is to be invented merely to make the implementation look complete.

- [ ] Build sanitized real-capture fixtures grouped by WHO/device/action
- [ ] Raw frame -> parsed frame -> normalized event -> entity state replay tests
- [ ] Record gateway model/firmware and safe installation context with captures
- [x] Reject parameterized standard `#WHERE` endpoint evidence except for explicitly parsed WHO=4 central-zone and WHO=5 partition semantics; WHO=5 `#N` remains partition state rather than endpoint-discovery evidence
- [ ] Investigate diagnostic/broadcast/group frames per WHO using real captures
- [ ] Revisit flat `NormalizedEvent.state` before additional complex WHO=5/18 payloads require structured semantics
- [x] Move WHO=2, WHO=4, WHO=5, WHO=6 door-entry and WHO=18 semantics into dedicated protocol modules where current evidence supports them

## Phase E — protocol/platform coverage

### WHO=0 — scenarios

- [x] Scenario activation entity
- [x] Scenario device-trigger adapter
- [x] No synthetic scenario inventory during active scan
- [ ] Real MH201 scenario fixtures and end-to-end trigger validation

### WHO=1 — lighting — COMPLETE SOFTWARE-SIDE, HARDWARE VALIDATION PENDING

- [x] Basic ON/OFF command and event state
- [x] Initial-state hydration request/response plumbing
- [x] Deterministic light-entity tests for ON/OFF commands, no optimistic state, event updates, endpoint filtering and documented status request
- [ ] Complete observed ON/OFF WHAT catalogue from real captures
- [ ] Validate on the target MH201 whether `*#1*WHERE##` returns a state frame or ACK only; either behavior must leave asynchronous event state authoritative

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

### WHO=5 — burglar alarm / BTicino 4200C target — STATUS SPEC-ALIGNED, CONTROL REFERENCE-BACKED, HARDWARE VALIDATION PENDING

- [x] Dedicated `protocol/alarm.py`
- [x] Parse WHO=5 central frames such as `*5*WHAT**##` as central WHERE=0 evidence
- [x] Parse WHO=5 partition frames with `#1..#8` without treating them as discovered endpoint devices
- [x] Documented central status request `*#5*0##`
- [x] Documented partition status requests `*#5*#N##`, N=1..8
- [x] Evidence-driven central ENGAGED/DISENGAGED Home Assistant alarm state
- [x] Evidence-driven alarm-trigger state for supported intrusion/tamper/panic-style WHAT values
- [x] Expose eight read-only partition-state sensors from WHO=5 `WHAT=11` active and `WHAT=18` partialized/non-active evidence
- [x] Reference-backed total arm command `*5*8##`
- [x] Reference-backed total disarm command `*5*9##`
- [x] Reference-backed selected-active-partition arm action using `*5*8#...##`
- [x] Reference-backed single-partition activate action using `*5*11*#N##`
- [x] Reference-backed single-partition partialize action using `*5*18*#N##`
- [x] Keep all alarm state evidence-driven; transmitted commands never update Home Assistant state optimistically
- [x] Deterministic protocol, alarm-panel, partition-sensor and service tests
- [x] Cross-check status/zone model against the mature openHAB OpenWebNet alarm handler and OWNd event semantics
- [ ] Validate central status query and all arm/disarm/partition commands against the target 4200C through MH201
- [ ] Capture normal arm/disarm and partition transitions from the real installation
- [ ] Capture safe fault/battery/network event lifecycle without intentionally creating unsafe alarm conditions
- [ ] Decide whether additional 4200C zone/input entities are useful only after real traffic establishes stable mapping

### WHO=6 — door entry / HomeTouch target — REFERENCE-BACKED DOOR RELEASE, HARDWARE VALIDATION PENDING

- [x] Separate door-entry semantics from public WHO=7 multimedia/camera semantics
- [x] Dedicated `protocol/door_entry.py`
- [x] Reference-backed WHO=6 door-release command surface
- [x] Manual WHO=6 `intercom` / `door_lock` inventory support
- [x] Disabled-by-default raw WHO=6/7 diagnostic event sensor for capture work
- [x] Remove guessed WHO=7 call start/end mappings rather than presenting unsupported ring state
- [x] Deterministic door-release and scope-mapping tests
- [ ] Validate door-release command against the target MH201/HomeTouch installation
- [ ] Capture HomeTouch call start and call end traffic without requiring audio/video
- [ ] Add a ring binary sensor only after a repeatable call lifecycle is established from official/reference evidence or real capture

### WHO=7 — multimedia / VDE cameras — DOCUMENTED FAMILY, NOT EXPOSED AS A/V PLATFORM

- [x] Confirm from public Legrand WHO=7 documentation that the family models multimedia/camera controls rather than a generic HomeTouch ring state
- [x] Do not misclassify WHO=7 camera/multimedia events as door-entry endpoint evidence
- [x] Allow raw WHO=7 diagnostics to support HomeTouch traffic analysis
- [x] Keep camera/audio/video entities outside the requested project scope
- [ ] Use real HomeTouch/MH201 captures to determine whether any WHO=7 event materially contributes to ring lifecycle evidence

### WHO=18 — energy — ACTIVE POWER SPEC/REFERENCE VALIDATED, HARDWARE VALIDATION PENDING

- [x] Device family classified by protocol/discovery
- [x] Dedicated `protocol/energy.py` boundary for the current unambiguous measurement surface
- [x] Restrict production active-power entities to documented `5N` energy-meter addresses (`N=1..255`)
- [x] Decode documented DIM=113 active power in watts
- [x] Request initial active power with `*#18*WHERE*113##`
- [x] Expose a read-only Home Assistant `SensorDeviceClass.POWER` sensor in watts with `SensorStateClass.MEASUREMENT`
- [x] Use measurement-specific unique IDs so future WHO=18 sensors cannot collide on the same endpoint
- [x] Keep state evidence-driven from DIM=113 responses/events with no optimistic value and no periodic polling
- [x] Add deterministic WHO=18 protocol and sensor regression tests
- [ ] Define totalizer DIM=51/52/53/54 units, reset semantics and Home Assistant state classes only after sufficient specification/capture evidence
- [ ] Add additional WHO=18 dimensions only where their unit and lifecycle semantics are unambiguous
- [ ] Build real energy-frame fixture catalogue
- [ ] Validate active-power units, sign, update cadence and initial query behavior on a real MH201/BUS

## Phase F — final Home Assistant and hardware validation

### Home Assistant integration-level validation

- [ ] Full Config Flow tests with Home Assistant flow machinery
- [ ] Full Options Flow tests with Home Assistant flow machinery
- [ ] Setup / unload / reload / restart tests with Home Assistant test machinery
- [ ] Entity lifecycle tests for every exposed platform
- [ ] Entity and Device Registry stability/removal tests
- [ ] Availability loss/recovery through Home Assistant state machinery
- [ ] Dynamic device add/remove through Home Assistant entity platforms
- [ ] Confirm diagnostics/redaction through Home Assistant diagnostics machinery

### Installation and MH201 validation

- [x] README synchronized with current implementation scope
- [x] Native SSDP, stable identity and migration documented
- [x] Implemented vs hardware-validation-pending protocol families documented
- [x] Dual Home Assistant CI window documented
- [x] Changelog/version metadata for 0.2.0
- [ ] Runtime validation on a real MH201
- [ ] Validate WHO=5 4200C central/partition status and control path
- [ ] Validate WHO=6 HomeTouch door release and capture ring lifecycle
- [ ] HACS installation validation from the tagged release
- [ ] Clean-install validation
- [ ] Upgrade validation from 0.1.x
- [ ] Restart/reload and changed-IP validation on a real HA instance
- [ ] Final troubleshooting pass using real failure cases
- [ ] Production-ready release candidate after the above validation

## Release boundary and next software focus

0.2.0 remains an architecture/runtime milestone, not a declaration that every protocol surface is hardware-validated. Post-0.2.0 `master` has the software-side architecture/runtime and Home Assistant surface-quality phases complete. WHO=1 ON/OFF is complete software-side; WHO=2 advanced position, WHO=4 thermoregulation and WHO=18 active power are spec/reference validated for their currently modeled software surfaces. WHO=5 now has a 4200C-oriented status/partition model plus reference-backed control, and WHO=6 has the deliberately narrow HomeTouch door-release/capture surface.

Further protocol breadth remains evidence-driven: WHO=1 dimming, WHO=3 load management, WHO=22/audio and VDE audio/video are permanently excluded; HomeTouch ring state waits for a reliable call-start/call-end frame; WHO=18 totalizers/additional dimensions wait for safe unit/reset semantics. After the WHO=5/6 software slice is green on its final documentation-synchronized HEAD, the next general software focus is **Home Assistant integration-level lifecycle coverage in Phase F**, while physical MH201/4200C/HomeTouch validation remains the final hardware campaign.
