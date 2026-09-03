# BTicino MyHome MH201 for Home Assistant

A local-first Home Assistant custom integration for **BTicino MyHome installations using an MH201 gateway and OpenWebNet**.

Current release: **0.2.0**.

The integration communicates directly with the MH201 over the local network. It does not use the BTicino, Netatmo or Legrand cloud for the control path.

> Scope: this project is intentionally focused on MH201/OpenWebNet. WHO=22, media player, audio, music and sound diffusion are deliberately out of scope.

## Project status

Version 0.2.0 is the first architecture/runtime consolidation milestone. The repository is validated by CI against:

- Home Assistant 2025.1 / Python 3.12 as the compatibility baseline;
- Home Assistant 2026.9 / Python 3.14 as the current primary target;
- Ruff, mypy, pytest, Hassfest and HACS validation.

CI green does **not** replace validation against a physical MH201. Protocol-sensitive areas are deliberately marked experimental until representative real OpenWebNet captures confirm their semantics.

## Current functional surface

| WHO | Area | Current status |
| --- | --- | --- |
| 0 | Scenarios | Basic activation entity and Home Assistant device triggers implemented; real MH201 event fixtures still required |
| 1 | Lighting | Basic on/off command and event state implemented |
| 2 | Automation / shutters | Open/close/stop and motion-state handling implemented |
| 3 | Load management | Basic on/off state/control implemented |
| 4 | Thermoregulation | Experimental climate surface; read/write semantics still require real MH201 validation |
| 5 | Alarm | Experimental minimal alarm-control-panel surface; mappings remain provisional |
| 7 | Video door entry | Experimental call-event / door-release surfaces; real traffic validation still required |
| 18 | Energy | Family recognized by protocol/discovery only; production energy entities are not yet implemented |
| 22 | Audio / sound diffusion | Explicitly unsupported and outside the roadmap |

The integration also provides passive bus learning, explicit active discovery, manual endpoint registration, diagnostics and a read-only OpenWebNet capture tool.

## Architecture

```text
Home Assistant
      |
   ConfigEntry
      |
      +-- MH201 hub device
      |      |
      |      +-- command session
      |      +-- event session
      |
      +-- Device Manager
             |
             +-- WHO/WHERE endpoint
             +-- WHO/WHERE endpoint
```

Wire-format knowledge is isolated in `custom_components/bticino_myhome/protocol/`:

- `frame.py` — immutable parsed frame model;
- `parser.py` — OpenWebNet wire frame -> structured frame;
- `commands.py` — semantic command/status request -> wire frame;
- `normalizer.py` — parsed frame -> normalized semantic event.

The Home Assistant platforms consume normalized events rather than parsing raw OpenWebNet strings themselves.

## Gateway lifecycle

The integration maintains separate command and event channels. Command writes are serialized so entity actions and discovery probes cannot overlap on one persistent command session.

The health model distinguishes:

- `command_connected` — command/control channel health;
- `event_connected` — event stream health;
- `connected` — aggregate availability requiring both channels.

If the command channel is lost while the event channel remains alive, the integration recovers the command session in the background with backoff. It deliberately does **not** automatically retransmit a failed frame after an ambiguous timeout/reset because the command may already have reached the BUS.

Persistent workers are owned by the Home Assistant task lifecycle.

## Gateway discovery and identity

Version 0.2.0 adds native Home Assistant SSDP discovery for MH201 and fixes the OWNd discovery path to use `OWNd.discovery.find_gateways()`.

When discovery metadata is available, gateway identity is chosen in this order:

1. serial number;
2. UDN;
3. host/port fallback.

New installations therefore use a stable serial/UDN identity when possible. Existing 0.1.x ConfigEntries migrate to ConfigEntry version 3 while preserving the previously persisted entity identity so Home Assistant entity history is not intentionally renamed by the upgrade.

If SSDP later sees the same serial/UDN on a different IP address, the existing ConfigEntry can be updated rather than creating a second gateway entry.

Manual host/port configuration remains supported when discovery is unavailable.

## Device Registry model

The MH201 is registered as the integration hub device. OpenWebNet endpoint devices are linked to that hub using the Device Registry parent/via relationship supported by the running Home Assistant version.

This separates physical gateway identity from logical WHO/WHERE endpoints and prepares the integration for safer migrations and future device lifecycle management.

## Discovery model

Device discovery is intentionally conservative and has three sources:

```text
                   MH201
                     |
              OpenWebNet / OWNd
                     |
          +----------+----------+
          |          |          |
       Passive     Active     Manual
          |          |          |
          +----------+----------+
                     |
             DiscoveredDevice
                     |
               Device Manager
```

### Passive learning

Passive learning only listens to actual OpenWebNet traffic. It sends no discovery commands. Use physical BTicino controls during the selected listening window to identify observable WHO/WHERE endpoints.

### Active discovery

Active discovery sends supported status probes and accepts endpoints only when matching bus traffic confirms them. WHO=4 remains excluded from broad active probing while its semantics are capture-led.

Version 0.2.0 no longer creates scenario addresses 1-30 merely because they could exist. WHO=0 scenarios are included only when observed during the scan or explicitly configured.

### Manual registration

Endpoints that cannot be safely discovered can be registered manually with WHO, WHERE, device type and an optional name. Manual records have precedence over later generic discovery updates.

## State model

For the stable/basic surfaces, a transmitted command is not treated as proof that the physical device changed state. State is expected to come back through OpenWebNet events/status responses.

WHO=4 climate is still experimental and is being audited to remove any optimistic behavior that is not justified by real protocol evidence.

## Configuration

Home Assistant can discover an MH201 through SSDP and offer a confirmation flow. If discovery is unavailable, enter the gateway host/IP, OpenWebNet port and optional password manually.

Default OpenWebNet port: `20000`.

Initial integration setup does not perform an implicit bus-wide device scan. Device discovery is an explicit action in the integration Options flow so Home Assistant startup remains deterministic.

## Installation

### HACS

1. Add `https://github.com/donatomontrone/bticino-myhome-mh201` as a HACS custom integration repository if it is not already available.
2. Install **BTicino MyHome MH201**.
3. Restart Home Assistant.
4. Open **Settings -> Devices & services -> Add integration** and search for **BTicino MyHome**.

Home Assistant installs the declared dependency automatically:

```json
"requirements": ["OWNd==0.7.49"]
```

### Manual

Copy `custom_components/bticino_myhome/` into `/config/custom_components/bticino_myhome/` and restart Home Assistant.

## Diagnostics

Home Assistant diagnostics include ConfigEntry metadata, gateway port, aggregate/channel connection health and discovered-device metadata. Passwords, host/IP and known serial/MAC fields are redacted.

For temporary frame-level logging:

```yaml
logger:
  default: warning
  logs:
    custom_components.bticino_myhome.gateway: debug
```

Do not publish credentials or unreviewed identifying data with logs/captures.

## OpenWebNet capture tool

The repository includes the read-only EVENT-session monitor:

```bash
python tools/openwebnet_monitor.py 192.168.1.50 --output capture.txt
```

A bounded capture can be created with:

```bash
python tools/openwebnet_monitor.py 192.168.1.50 --seconds 300 --output capture.txt
```

The capture workflow is the preferred source of evidence for extending WHO=4, WHO=5, WHO=7 and WHO=18 support. Do not intentionally trigger unsafe alarm conditions merely to generate traffic.

## Known limitations

- Real MH201 clean-install, upgrade, restart/reload and long-running disconnect/recovery testing is still required.
- Active discovery cannot infer the complete configuration stored in Home+Project and intentionally avoids manufacturing unconfirmed endpoints.
- WHO=4/5/7 semantics are not declared stable until backed by real captures.
- WHO=18 energy entities are not yet implemented.
- Stale-device removal and dynamic entity removal still need a complete Home Assistant lifecycle implementation.
- Config/Options Flow coverage is not yet at the project's targeted Silver-like Home Assistant integration-quality level.

## Development

The package declares Python `>=3.12`. CI currently runs runtime tests on Python 3.12 with Home Assistant 2025.1 and Python 3.14.2 with Home Assistant 2026.9. Static quality checks run against the current Home Assistant target.

```bash
python -m pip install -r requirements-dev.txt
python -m pytest
python -m ruff check custom_components/bticino_myhome tests
python -m mypy custom_components/bticino_myhome
```

## Roadmap

Development priority after 0.2.0 is **runtime solidity before protocol breadth**:

1. finish transport result/error semantics and availability logging;
2. initial-state hydration and removal of synthetic/diagnostic WHO=7 entities;
3. stale-device and dynamic add/remove lifecycle;
4. full Home Assistant Config Flow, Options Flow, setup/unload/reload and registry tests;
5. sanitized real-capture fixture corpus and deterministic replay;
6. only then expand capture-backed WHO=4/5/7/18 functionality.

See `docs/roadmap.md` for the detailed checklist.

**WHO=22 / media player / audio / music / sound diffusion remain permanently excluded.**
