# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Features
- Add `send_frame` service for sending raw OpenWebNet frames (useful for debug and advanced automations)
- Add device triggers for scenario activation (enable automation based on scenario events)
- Add Climate platform (WHO=4) with full HVAC support

### Tests
- Add `test_services.py` with 4 tests for send_frame service
- Add `test_device_trigger.py` with 3 tests for device triggers
- Add `test_climate.py` with 7 tests for BticinoClimate
- Add `test_protocol_thermo.py` with 4 tests for WHO=4 frame parsing

### Documentation
- Update roadmap v2.3 with complete file-by-file analysis

## [0.1.13] - 2026-09-03

### Features
- **Climate platform (WHO=4)** — Full HVAC support for BTicino thermostats
  - Temperature measurement (DIM=0)
  - Setpoint control (DIM=14) with 0.5°C precision
  - Mode control: heat, cool, auto, eco, off
  - Local offset support (DIM=13)
  - Probe status (DIM=12)
  - Valves status (DIM=19)
- Add `send_frame` service for sending raw OpenWebNet frames (useful for debug and advanced automations)
- Add device triggers for scenario activation (enable automation based on scenario events)

### Tests
- Add `test_climate.py` with 7 tests covering:
  - Set HVAC mode (heat, cool, off)
  - Set target temperature
  - Update from temperature/setpoint/mode events
- Add `test_protocol_thermo.py` with 4 tests for WHO=4 frame parsing
- Add `test_services.py` with 4 tests for send_frame service
- Add `test_device_trigger.py` with 3 tests for device triggers

### Internal
- Create `services.py` module for service implementations
- Create `services.yaml` for service definitions
- Create `device_trigger.py` for device automation triggers
- Update `__init__.py` to register/unregister services
- Update `protocol.py` with WHO=4 constants
- Update `normalizer.py` with WHO=4 event parsing
- Update `discovery.py` with WHO=4 device discovery
- Update `device.py` to support climate devices

## [0.1.12] - 2026-09-03

### Features
- Add `send_frame` service for sending raw OpenWebNet frames (useful for debug and advanced automations)
- Add device triggers for scenario activation (enable automation based on scenario events)

### Tests
- Add `test_services.py` with 4 tests covering:
  - Successful frame send
  - Frame send with status request flag
  - Error handling for missing frame
  - Error handling for no gateway configured
- Add `test_device_trigger.py` with 3 tests covering:
  - Empty triggers when no scenes
  - Scenario triggers for scene devices
  - Trigger capabilities

### Internal
- Create `services.py` module for service implementations
- Create `services.yaml` for service definitions
- Create `device_trigger.py` for device automation triggers
- Update `__init__.py` to register/unregister services

## [0.1.11] - 2026-09-03

### Fixes
- Fix ruff errors in protocol.py (unused import, whitespace)
- Restore missing CONF_* and PLATFORMS constants in const.py

## [0.1.10] - 2026-09-03

### Features
- Extend OpenWebNet parser to handle composite addresses (21#4)
- Add support for dimension frames (*#WHO*WHERE*DIM*val##)
- Add status request handling in parser

### Improvements
- Update `async_added_to_hass()` in light/cover/switch to request initial state from bus
- Remove duplicate AlarmControlPanelState import in alarm_control_panel.py
- Align const.py comment with manifest min_ha_version

## [0.1.9] - 2026-09-03

### Fixes
- Fix test discovery engine expectations (address vs where)
- Fix from_manual() location (DiscoveredDevice, not BticinoDiscovery)

## [0.1.8] - 2026-09-03

### Features
- Add comprehensive protocol layer with 5 dedicated modules
- Implement full parser for OpenWebNet frames
- Add normalizer for event standardization

### Tests
- Add 28 tests covering all major components
- Achieve 100% test pass rate

## [0.1.7] - 2026-09-03

### CI/CD
- Add GitHub Actions workflow with pytest + ruff
- Add hassfest and HACS validators
- Configure 10s timeout per test, 10min per job

### Infrastructure
- Add pyproject.toml with Python 3.12+ requirement
- Add requirements-dev.txt with OWNd==0.7.49
- Add CODEOWNERS and CONTRIBUTING.md

## [0.1.6] - 2026-09-03

### Fixes
- Fix OWNGateway API (config dict instead of positional args)
- Fix NormalizedEvent parsing (manual frame parse)
- Fix from_manual() signature and location

## [0.1.5] - 2026-09-03

### Fixes
- Fix circular import in gateway.py
- Fix OWNd import case sensitivity
- Fix test timeouts with bounded asyncio.wait_for()

## [0.1.4] - 2026-09-03

### Features
- Implement complete gateway lifecycle management
- Add reconnect with exponential backoff (1s → 60s)
- Add explicit timeouts (10s command, 10s connect)

## [0.1.3] - 2026-09-03

### Features
- Add device manager with merge logic
- Implement passive/active/manual discovery
- Add precedence for manual devices over passive events

## [0.1.2] - 2026-09-03

### Features
- Add config flow with options flow
- Implement scan, passive learning, manual add actions

### Documentation
- Add comprehensive README with architecture sections
- Add architecture.md, discovery.md, protocol.md

## [0.1.1] - 2026-09-02

### Features
- Initial release with core platforms:
  - Light (WHO=1)
  - Cover (WHO=2)
  - Switch (WHO=16)
  - Scene (WHO=0)
  - Alarm Control Panel (WHO=5)
  - Button (WHO=7)
  - Binary Sensor
  - Sensor (WHO=18)

### Infrastructure
- HACS-compatible structure
- manifest.json with OWNd dependency
- Brand assets and translations (IT/EN)

## [0.1.0] - 2026-09-02

### Initial Release
- First working version
- Basic OpenWebNet integration
- Core platforms implemented
