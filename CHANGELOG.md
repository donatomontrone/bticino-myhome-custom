# Changelog

All notable changes to this project are documented here. The project follows Semantic Versioning.

## [Unreleased]

No unreleased changes yet.

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
- WHO=1 lighting, WHO=2 shutters/covers, WHO=3 load control and WHO=0 scenario activation are the current basic functional surfaces.
- WHO=4 climate, WHO=5 alarm and WHO=7 video door-entry support remain experimental/capture-led until validated against representative real MH201 traffic.
- WHO=18 is recognized by discovery/protocol classification, but production energy entities are not yet implemented.
- WHO=22, media player, audio, music and sound diffusion remain explicitly out of scope.
- CI validates software/API behavior; real MH201 clean-install, upgrade and long-running runtime validation are still required.

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
