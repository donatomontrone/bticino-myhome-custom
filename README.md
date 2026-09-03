# BTicino MyHome MH201 for Home Assistant

A local-first Home Assistant custom integration for **BTicino MyHome installations using an MH201 gateway and OpenWebNet**.

Current release: **0.2.0**.

The integration communicates directly with the MH201 over the local network. It does not use the BTicino, Netatmo or Legrand cloud for the control path.

> Scope: this project is intentionally focused on MH201/OpenWebNet. WHO=22, media player, audio, music, sound diffusion, WHO=1 dimmer/brightness/transition control and WHO=3 load-management semantics are deliberately out of scope. WHO=1 lighting is intentionally limited to ON/OFF. Energy management is modeled only through documented WHO=18 semantics. Audio/video streaming from video-door-entry devices is not a project target.

## Project status

Version 0.2.0 is the first architecture/runtime consolidation milestone. The repository is validated by CI against:

- Home Assistant 2025.1 / Python 3.12 as the compatibility baseline;
- Home Assistant 2026.9 / Python 3.14 as the current primary target;
- Ruff, mypy, pytest, Hassfest and HACS validation.

CI green does **not** replace validation against a physical MH201. Protocol-sensitive areas are deliberately marked hardware-validation-pending until representative real OpenWebNet captures confirm their runtime behavior.

## Current functional surface

| WHO | Area | Current status |
| --- | --- | --- |
| 0 | Scenarios | Basic activation entity and Home Assistant device triggers implemented; real MH201 event fixtures still required |
| 1 | Lighting | ON/OFF-only surface complete software-side; dimmer/brightness permanently excluded from project scope; real MH201 status-query validation pending |
| 2 | Automation / shutters | Open/close/stop plus spec/reference-backed advanced position handling implemented; real MH201 validation still required |
| 4 | Thermoregulation | Spec/reference-aligned climate surface; real MH201/KW4691 validation still required |
| 5 | Burglar alarm | 4200C-oriented software surface: documented central/partition status, eight partition sensors, reference-backed total arm/disarm, selected-partition arm and single-partition active/partialized controls; MH201/4200C hardware validation pending |
| 6 | Door entry | Reference-backed door-release command plus disabled-by-default raw WHO=6/7 diagnostic capture for HomeTouch traffic; real MH201/HomeTouch validation pending |
| 7 | Multimedia / VDE cameras | Public Legrand WHO=7 camera/multimedia semantics are recognized as a separate protocol family but no camera/audio/video entity is exposed; ring semantics are not invented from WHO=7 |
| 18 | Energy | Read-only active-power sensor (DIM=113) implemented for documented 5N energy-meter endpoints; totalizers and other measurements remain pending |
| 22 | Audio / sound diffusion | Explicitly unsupported and outside the roadmap |

WHO=3 is intentionally not a supported project family. No WHO=3 platform, command builder, discovery mapping or manual device type is exposed; energy-management development belongs to WHO=18.

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
- `commands.py` — generic semantic command/status request -> wire frame;
- `normalizer.py` — parsed frame -> normalized semantic event;
- `automation.py` — WHO=2 advanced shutter status/position helpers;
- `thermoregulation.py` — WHO=4 thermoregulation semantics and command builders;
- `alarm.py` — WHO=5 central/partition status plus 4200C-targeted reference-backed control builders;
- `door_entry.py` — conservative WHO=6 door-release boundary, kept distinct from public WHO=7 multimedia/camera semantics;
- `energy.py` — conservative WHO=18 active-power decoding and documented energy-meter addressing.

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

Active discovery sends supported status probes and accepts endpoints only when matching bus traffic confirms them. WHO=4 and WHO=18 remain excluded from broad active probing; their endpoint semantics are intentionally evidence-driven rather than discovered by speculative bus-wide scans. WHO=5 uses only the documented central status request rather than a speculative address scan.

Version 0.2.0 no longer creates scenario addresses 1-30 merely because they could exist. WHO=0 scenarios are included only when observed during the scan or explicitly configured.

### Manual registration

Endpoints that cannot be safely discovered can be registered manually with WHO, WHERE, device type and an optional name. Manual records have precedence over later generic discovery updates.

For a 4200C alarm, the integration models a WHO=5 central endpoint and exposes the documented central state plus partitions 1-8. For a HomeTouch/video-door-entry endpoint, WHO=6 can be registered manually to expose the reference-backed door-release button and raw diagnostic capture. WHO=7 is not treated as a synonym for door entry: the public Legrand WHO=7 specification describes the multimedia/camera subsystem.

For WHO=18, the current production sensor surface is deliberately limited to documented `5N` energy-meter addresses (`N=1..255`) and DIM=113 active power.

## Alarm control model — WHO=5 / BTicino 4200C target

The alarm surface deliberately separates documented status semantics from control commands that still require hardware validation on the target installation.

Documented/status-oriented behavior includes:

- central status hydration with `*#5*0##`;
- central engaged/disengaged evidence;
- alarm events such as intrusion/tamper/panic where represented by WHO=5 WHAT values;
- partition 1-8 hydration with `*#5*#N##`;
- partition active (`WHAT=11`) vs partialized/non-active (`WHAT=18`) state.

Reference-backed control behavior includes:

- total arm `*5*8##`;
- total disarm `*5*9##`;
- arm with selected active partitions using `*5*8#...##`;
- activate one partition with `*5*11*#N##`;
- partialize one partition with `*5*18*#N##`.

The latter commands come from legacy official BTicino alarm-control documentation and established OpenWebNet precedent, but are **not declared hardware-validated for a 4200C through MH201** until real traffic confirms acceptance and resulting state. Home Assistant never treats a transmitted alarm command as proof of a successful state change.

## HomeTouch / door-entry model

The requested HomeTouch surface is deliberately limited to **ring indication and door release**, without audio/video streaming.

Door release is implemented through a conservative, reference-backed WHO=6 command surface and remains hardware-validation-pending. A disabled-by-default diagnostic sensor captures raw WHO=6 and WHO=7 events so the actual HomeTouch/MH201 call-start and call-end frames can be identified safely.

A Home Assistant ring binary sensor is **not yet synthesized** because the public Legrand WHO=7 document describes camera/multimedia functions and does not define a reliable doorbell call lifecycle for this target. Ring indication will be added only after an official/reference-backed frame or a real HomeTouch/MH201 capture identifies stable call start/end semantics.

## State model

For all control surfaces, a transmitted command is not treated as proof that the physical device changed state. State is expected to come back through OpenWebNet events/status responses.

WHO=2 advanced position, WHO=4 climate and WHO=5 alarm likewise keep their modeled state evidence-driven rather than relying on optimistic local writes. WHO=5 partition actions do not alter partition sensors locally; the received WHO=5 state remains authoritative.

WHO=18 active power is read-only: the integration requests DIM=113 for initial hydration and only updates watt values from received OpenWebNet evidence; it does not poll periodically or synthesize measurements.

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

The capture workflow is the preferred source of evidence for final WHO=4, WHO=5, WHO=6/HomeTouch and WHO=18 validation. For HomeTouch specifically, the next protocol-capture goal is to identify a repeatable call-start and call-end frame without relying on video/audio. Do not intentionally trigger unsafe alarm conditions merely to generate traffic.

## Known limitations

- Real MH201 clean-install, upgrade, restart/reload and long-running disconnect/recovery testing is still required.
- Active discovery cannot infer the complete configuration stored in Home+Project and intentionally avoids manufacturing unconfirmed endpoints.
- WHO=5 central/partition status and control builders are software-tested, but 4200C acceptance and feedback through MH201 remain hardware-validation-pending.
- WHO=6 door release is reference-backed but still requires validation against the target MH201/HomeTouch installation.
- HomeTouch ring indication is intentionally pending because no sufficiently reliable call-start/call-end frame has yet been established from the public Legrand WHO=7 documentation or available mature integrations.
- Public WHO=7 multimedia/camera controls are not exposed because audio/video camera integration is outside the requested project surface.
- WHO=18 currently exposes only documented active power (DIM=113) for 5N energy-meter endpoints; totalizers and additional dimensions remain deferred until their units, reset semantics and real MH201 behavior are validated.
- Final Home Assistant lifecycle validation is still pending.

## Development

The package declares Python `>=3.12`. CI currently runs runtime tests on Python 3.12 with Home Assistant 2025.1 and Python 3.14.2 with Home Assistant 2026.9. Static quality checks run against the current Home Assistant target.

```bash
python -m pip install -r requirements-dev.txt
python -m pytest
python -m ruff check custom_components/bticino_myhome tests
python -m mypy custom_components/bticino_myhome
```

## Roadmap

The detailed development checklist is maintained in `docs/roadmap.md`. Every implementation cycle must update that roadmap and end with the same final `master` HEAD green for the Home Assistant test matrix, Ruff, mypy, Hassfest and HACS validation.

**WHO=22 / media player / audio / music / sound diffusion, WHO=1 dimmer / brightness / transition control, WHO=3 load-management semantics and VDE audio/video streaming remain permanently excluded.**
