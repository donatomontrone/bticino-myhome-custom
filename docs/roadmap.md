# Technical roadmap — BTicino MyHome MH201

Last reviewed: 2026-09-03.

Repository: https://github.com/donatomontrone/bticino-myhome-mh201

Primary protocol source: official BTicino/Legrand OpenWebNet Local Interoperability documentation at https://developer.legrand.com/local-interoperability/ . Mature MyHOME/OWNd/openHAB projects are secondary cross-checks; real MH201 captures remain the final hardware evidence.

## Permanent scope exclusions

The following must not be reintroduced as future work unless the project scope is explicitly changed:

- WHO=22;
- media player, audio, music and sound diffusion;
- WHO=1 dimmer / brightness / transition control;
- WHO=3 load-management semantics; Energy Management is WHO=18 only;
- HomeTouch/VDE audio-video streaming and camera entities.

WHO=1 is intentionally ON/OFF only. WHO=7 is treated according to the public multimedia/camera specification and is not used as a guessed generic doorbell family.

## Validation labels

- **Complete software-side**: the intended project surface is implemented and covered by deterministic tests; physical-device validation may still be pending.
- **Spec/reference validated**: semantics are derived from official OpenWebNet documentation, cross-checked with established implementations where useful and covered by deterministic tests.
- **Reference-backed**: the implementation follows older official BTicino material and/or mature implementation precedent, but target-hardware acceptance has not yet been proven.
- **Hardware validated**: confirmed on the real target installation with representative traffic and runtime behavior.

## Development completion rule

Every implementation cycle must update this roadmap in the same work cycle. Software work is not considered complete until the same final `master` HEAD is green for:

- Home Assistant compatibility test matrix;
- Ruff;
- mypy;
- pytest;
- Hassfest;
- HACS validation.

Hardware-dependent items remain explicitly pending until a real MH201/MyHome system is available.

## Release 0.3.0 checkpoint

The pre-release software baseline after WHO=5 diagnostics contains **165 deterministic tests** and **73.51% integration-package coverage** on Home Assistant 2026.9 / Python 3.14. The coverage gate remains 55%.

The Hassfest `CONFIG_SCHEMA` warning has been fixed by explicitly declaring the integration ConfigEntry-only. The corresponding Hassfest run is clean.

Release 0.3.0 consolidates the software surfaces developed after 0.2.0. The only broad validation layer intentionally left for later is execution on a real Home Assistant instance and physical MH201/MyHome installation.

## Repository / runtime foundation — COMPLETE SOFTWARE-SIDE

- [x] Dedicated `protocol/` package and normalized event boundary
- [x] ConfigEntry runtime data and stable gateway identity
- [x] MH201 hub Device Registry model
- [x] Separate persistent command/event sessions
- [x] Serialized command writes and recovery without blind retransmission
- [x] Passive, conservative active and manual discovery
- [x] Explicit device removal and merge-only discovery safety
- [x] SSDP MH201 discovery plus host/port fallback
- [x] Diagnostics with sensitive-data redaction
- [x] Read-only OpenWebNet capture tool
- [x] HACS metadata and Hassfest validation
- [x] Home Assistant 2025.1/Python 3.12 and 2026.9/Python 3.14 CI matrix
- [x] Ruff, mypy and pytest quality gates
- [x] ConfigEntry-only `CONFIG_SCHEMA`; Hassfest warning removed

## WHO=0 — scenarios

Status: **COMPLETE SOFTWARE-SIDE, HARDWARE VALIDATION PENDING**.

- [x] Scenario activation entity
- [x] Scenario device triggers
- [x] No fabricated scenario inventory during discovery
- [ ] Real MH201 scenario-event fixtures and end-to-end physical validation

## WHO=1 — lighting

Status: **COMPLETE SOFTWARE-SIDE FOR ON/OFF-ONLY SCOPE, HARDWARE VALIDATION PENDING**.

- [x] ON command
- [x] OFF command
- [x] Evidence-driven ON/OFF state
- [x] Initial status-request plumbing
- [x] Dedicated light tests; no optimistic state
- [x] Permanently exclude dimmer/brightness/transition
- [ ] Validate the real MH201 behavior of `*#1*WHERE##` status requests

## WHO=2 — automation / shutters

Status: **ADVANCED POSITION SPEC/REFERENCE VALIDATED, HARDWARE VALIDATION PENDING**.

- [x] Open / close / stop
- [x] Dedicated `protocol/automation.py`
- [x] DIM=10 advanced status/position
- [x] Position `0..100` and `255` unknown semantics
- [x] DIM=11 GoToLevel builder
- [x] Explicit advanced-position capability
- [x] `SET_POSITION` only when supported/configured/observed
- [x] No synthetic travel-time percentage
- [x] Initial DIM=10 hydration for advanced shutters
- [x] Deterministic protocol/entity tests
- [ ] Validate position and priority behavior on a real MH201/BUS

## WHO=4 — thermoregulation

Status: **SPEC/REFERENCE VALIDATED, HARDWARE VALIDATION PENDING**.

- [x] Dedicated `protocol/thermoregulation.py`
- [x] Home Assistant climate entity
- [x] Standalone and central-zone routing
- [x] Heating-only, cooling-only and heating+cooling profiles
- [x] KW4691-compatible heating-only surface where configured
- [x] Temperature and documented mode/protection families
- [x] DIM=14 setpoint writes
- [x] Conservative DIM=19 output/valve state
- [x] No optimistic climate state
- [x] Protocol/climate/discovery regression tests
- [ ] Validate read/write frames and zone routing on the target installation

## WHO=5 — burglar alarm / BTicino 4200C

Status: **STATUS/DIAGNOSTICS SPEC-ALIGNED; CONTROL REFERENCE-BACKED; HARDWARE VALIDATION PENDING**.

- [x] Dedicated `protocol/alarm.py`
- [x] Central WHO=5 parsing and snapshot request `*#5*0##`
- [x] Partition status requests `*#5*#N##`, N=1..8
- [x] Evidence-driven central ENGAGED/DISENGAGED/TRIGGERED state
- [x] Eight active/partialized partition sensors
- [x] Full arm reference-backed command
- [x] Full disarm reference-backed command
- [x] Selected-active-partition arm action
- [x] Single-partition activate/partialize action
- [x] No optimistic alarm state
- [x] Battery diagnostic: WHAT 4/10 problem, WHAT 5 OK
- [x] Network diagnostic: WHAT 6 absent, WHAT 7 present
- [x] Technical alarm AUX 1–9: WHAT 12 alarm / WHAT 13 reset, disabled by default
- [x] Keep WHAT=14 observable but do not model a persistent state without a reliable reset lifecycle
- [x] Deterministic protocol, panel, partition, service and diagnostic tests
- [x] Cross-check with official WHO=5 documentation and mature OWNd/openHAB behavior
- [ ] Validate arm/disarm/partition commands against the target 4200C through MH201
- [ ] Capture normal arm/disarm and partition transitions
- [ ] Capture battery/network/technical-fault lifecycle safely on the real installation
- [ ] Evaluate additional 4200C sensor/input entities only after stable real mapping is known

## WHO=6 — door entry / HomeTouch 7"

Status: **REFERENCE-BACKED DOOR RELEASE, HARDWARE VALIDATION PENDING**.

- [x] Keep door-entry semantics separate from public WHO=7 multimedia semantics
- [x] Dedicated `protocol/door_entry.py`
- [x] Reference-backed WHO=6 door-release button
- [x] Manual WHO=6 inventory support
- [x] Disabled-by-default raw WHO=6/7 diagnostic sensor
- [x] Remove guessed ring WHAT mappings
- [ ] Validate door release on MH201 + HomeTouch
- [ ] Capture repeatable call-start and call-end traffic
- [ ] Add a ring binary sensor only after the call lifecycle is proven

## WHO=7 — multimedia / VDE cameras

Status: **DOCUMENTED FAMILY, NOT EXPOSED AS AN A/V PLATFORM**.

- [x] Confirm from official WHO=7 documentation that the family controls camera/multimedia resources
- [x] Do not treat WHO=7 as a generic doorbell state family
- [x] Allow raw diagnostic observation for HomeTouch investigation
- [x] Keep camera/audio/video entities outside scope
- [ ] Determine from real capture whether any WHO=7 frame contributes to HomeTouch ring lifecycle evidence

## WHO=18 — Energy Management

Status: **ACTIVE POWER SPEC/REFERENCE VALIDATED, HARDWARE VALIDATION PENDING**.

- [x] WHO=18-only Energy Management model; WHO=3 removed from project scope
- [x] Dedicated `protocol/energy.py`
- [x] Restrict current production sensor to documented `5N` endpoints
- [x] DIM=113 Active Power decoding in watts
- [x] Initial DIM=113 status request
- [x] Home Assistant `POWER` / `MEASUREMENT` sensor
- [x] Measurement-specific unique ID
- [x] Event/response-driven state; no polling and no optimistic value
- [x] Deterministic protocol/sensor tests
- [ ] Validate DIM=113 on a real energy meter through MH201
- [ ] Add totalizers only after units, reset semantics and Home Assistant state-class mapping are proven

## WHO=3 — permanently removed

- [x] Remove WHO=3 platform semantics
- [x] Remove discovery mapping
- [x] Remove command builders/runtime exposure
- [x] Do not use WHO=3 for energy
- [ ] Never reintroduce without an explicit project-scope change

## Final Home Assistant / hardware validation campaign

These are the intended next steps after release 0.3.0 when a real environment is available:

- [ ] Clean HACS installation on a fresh Home Assistant instance
- [ ] Upgrade from the previous release
- [ ] ConfigEntry setup → unload → reload validation
- [ ] Home Assistant restart with persisted inventory
- [ ] Authentication/reauthentication validation against the actual MH201
- [ ] Long-running event session and reconnect testing
- [ ] Sanitized capture fixtures for each installed WHO family
- [ ] Physical light/shutter/climate/alarm/door-entry/energy validation
- [ ] HomeTouch ring lifecycle discovery
- [ ] Update each WHO status from hardware-validation-pending only after evidence exists

## Release documentation

- [x] README rewritten as an Italian-first bilingual project overview
- [x] `USAGE.md` created as an Italian-first bilingual HACS installation and usage manual
- [x] Protocol notes synchronized with WHO=3 removal and WHO=5/6/7/18 boundaries
- [x] Hassfest schema warning corrected
- [x] WHO=5 battery/network/technical-alarm diagnostics implemented before release

The automated release workflow must publish 0.3.0 only after the final release HEAD has passed Test, Hassfest and HACS checks. This rule is intentionally enforced by `.github/workflows/release.yml`.
