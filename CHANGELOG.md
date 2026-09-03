# Changelog

All notable changes to this project are documented here. The project follows Semantic Versioning.

## [Unreleased]

No unreleased changes yet.

## [0.3.0] - 2026-09-03

### Italiano

#### Aggiunto
- Tapparelle WHO=2 avanzate con stato/posizione DIM=10, GoToLevel DIM=11 e capability esplicita per `SET_POSITION`.
- Superficie WHO=4 termoregolazione con profili heating/cooling, setpoint DIM=14 e gestione conservativa DIM=19.
- Superficie WHO=5 orientata alla centrale BTicino 4200C: stato centrale, 8 partizioni, arm/disarm, inserimento con partizioni selezionate e controllo della singola partizione.
- Diagnostica WHO=5 read-only per batteria, presenza rete e allarmi tecnici AUX 1–9.
- Apriporta WHO=6 reference-backed e diagnostica raw WHO=6/7 per il target HomeTouch.
- Sensore WHO=18 DIM=113 Active Power in watt per endpoint energy meter `5N` documentati.
- Test deterministici dedicati per luci, tapparelle avanzate, allarme, servizi, apriporta ed energia.
- Nuovo `USAGE.md` bilingue con installazione HACS e manuale d'uso completo.

#### Modificato
- WHO=1 è definitivamente limitato a ON/OFF; dimmer/brightness/transition sono fuori scope.
- WHO=3 è rimosso dal modello del progetto; l'Energy Management usa esclusivamente WHO=18.
- WHO=7 è trattato come famiglia multimedia/camera secondo la documentazione Legrand pubblica e non come stato generico del citofono.
- Gli stati protocol-sensitive restano evidence-driven: nessun comando viene usato come conferma ottimistica dello stato fisico.
- README e documentazione protocollo/roadmap sono stati riallineati allo stato reale del progetto.

#### Corretto
- Eliminato il warning Hassfest relativo a `CONFIG_SCHEMA` dichiarando esplicitamente l'integrazione ConfigEntry-only.
- Rimosse semantiche citofoniche e load-management non supportate/documentate dal percorso di produzione.

#### Validazione
- Baseline software pre-release: 165 test passati e 73,51% di coverage su Home Assistant 2026.9 / Python 3.14.
- CI: Home Assistant 2025.1/Python 3.12, Home Assistant 2026.9/Python 3.14, Ruff, mypy, pytest, Hassfest e HACS.
- La validazione fisica su MH201, 4200C, HomeTouch e dispositivi BUS reali resta esplicitamente pendente.

### English

#### Added
- Advanced WHO=2 shutter support with DIM=10 status/position, DIM=11 GoToLevel and explicit Home Assistant `SET_POSITION` capability.
- WHO=4 thermoregulation surface with heating/cooling profiles, DIM=14 setpoint writes and conservative DIM=19 handling.
- BTicino 4200C-oriented WHO=5 surface: central state, 8 partitions, arm/disarm, selected-partition arm and per-partition control.
- Read-only WHO=5 diagnostics for battery, network presence and technical alarms AUX 1–9.
- Reference-backed WHO=6 door release plus raw WHO=6/7 diagnostics for the HomeTouch target.
- WHO=18 DIM=113 Active Power sensor in watts for documented `5N` energy-meter endpoints.
- Dedicated deterministic tests for lighting, advanced shutters, alarm, services, door entry and energy.
- New bilingual `USAGE.md` with HACS installation and complete usage instructions.

#### Changed
- WHO=1 is permanently restricted to ON/OFF; dimmer/brightness/transition are out of scope.
- WHO=3 is removed from the project model; Energy Management uses WHO=18 only.
- WHO=7 follows the public Legrand multimedia/camera specification and is not treated as a generic doorbell-state family.
- Protocol-sensitive state remains evidence-driven; command transmission is never used as optimistic proof of a physical state change.
- README, protocol notes and roadmap were synchronized with the actual implementation.

#### Fixed
- Removed the Hassfest `CONFIG_SCHEMA` warning by explicitly declaring the integration ConfigEntry-only.
- Removed unsupported/guessed load-management and door-entry semantics from the production model.

#### Validation
- Pre-release software baseline: 165 passing tests and 73.51% coverage on Home Assistant 2026.9 / Python 3.14.
- CI covers Home Assistant 2025.1/Python 3.12, Home Assistant 2026.9/Python 3.14, Ruff, mypy, pytest, Hassfest and HACS.
- Physical validation against a real MH201, 4200C, HomeTouch and BUS devices remains explicitly pending.

## [0.2.0] - 2026-09-03

### Added
- Native Home Assistant SSDP discovery for BTicino MH201 gateways.
- Normalized gateway discovery metadata from the actual `OWNd.discovery.find_gateways()` API.
- Stable gateway identity using serial number first, UDN second, and host/port only as a fallback.
- ConfigEntry migration to version 3 with a persisted gateway identity that preserves existing 0.1.x entity identifiers and history.
- MH201 registration as the Home Assistant hub device, with endpoint devices linked to the hub using the Device Registry mechanism supported by each tested Home Assistant version.
- Separate command-channel and event-channel health in diagnostics.
- Gateway identity/discovery and migration tests.
- CI compatibility matrix for Home Assistant 2025.1 / Python 3.12 and Home Assistant 2026.9 / Python 3.14.

### Changed
- Hardened the persistent command session with serialized writes, missing-session recovery and background command-channel recovery.
- A failed command is not blindly retransmitted by the integration after an ambiguous timeout/reset; the channel is recovered for subsequent commands instead.
- Persistent gateway workers are created through Home Assistant task lifecycle management.
- `connected` now represents aggregate command + event availability while the two channel states remain independently observable.
- Active discovery no longer manufactures scenario addresses 1-30. WHO=0 scenarios are accepted only when observed during the listening window or explicitly configured.
- Manual gateway setup can enrich identity/model metadata through OWNd discovery when available while remaining usable by host/port alone.
- Scenario device-trigger attachment was aligned with the Home Assistant Core event-trigger pattern and validated on both supported CI targets.
- Repository quality gates now include Ruff, mypy, pytest, Hassfest and HACS validation on the current Home Assistant target.

### Fixed
- Corrected the previous gateway discovery path that referenced an unavailable `OWNGateway.discover` API.
- Preserved legacy entity identity across the ConfigEntry v2 -> v3 migration so existing Home Assistant history is not intentionally renamed by this release.
- Improved command-session recovery so losing control transport while the event stream is still alive does not require a Home Assistant restart.

### Status / limitations
- Version 0.2.0 was the architecture/runtime consolidation milestone.
- Subsequent protocol/platform work is included in 0.3.0.
- WHO=22, media player, audio, music and sound diffusion remain explicitly out of scope.

## [0.1.13] - 2026-09-03

### Features
- Added the initial WHO=4 climate surface and dimension parsing.
- Added the `send_frame` advanced/debug service.
- Added scenario device triggers.

### Tests
- Added climate, thermoregulation protocol, raw-frame service and scenario trigger tests.

## [0.1.12] - 2026-09-03

### Features
- Added the `send_frame` service and scenario device triggers.

## [0.1.11] - 2026-09-03

### Fixes
- Fixed Ruff errors and restored integration constants.

## [0.1.10] - 2026-09-03

### Features
- Extended OpenWebNet parsing for composite addresses and dimension/status frames.

## [0.1.9] - 2026-09-03

### Fixes
- Fixed discovery-engine expectations and manual-device construction.

## [0.1.8] - 2026-09-03

### Features
- Added the dedicated OpenWebNet protocol package, parser and semantic normalizer.

## [0.1.7] - 2026-09-03

### CI/CD
- Added pytest/Ruff, Hassfest and HACS workflows.

## [0.1.6] - 2026-09-03

### Fixes
- Fixed OWNGateway configuration, normalized event parsing and manual discovery signatures.

## [0.1.5] - 2026-09-03

### Fixes
- Fixed circular imports, OWNd case sensitivity and test timeouts.

## [0.1.4] - 2026-09-03

### Features
- Added gateway lifecycle management, reconnect/backoff and explicit timeouts.

## [0.1.3] - 2026-09-03

### Features
- Added the device manager and passive/active/manual discovery model.

## [0.1.2] - 2026-09-03

### Features
- Added Config Flow, Options Flow and initial architecture/discovery documentation.

## [0.1.1] - 2026-09-02

### Features
- Initial Home Assistant platform surfaces and HACS-compatible repository structure.

## [0.1.0] - 2026-09-02

### Initial release
- First local OpenWebNet integration baseline.
