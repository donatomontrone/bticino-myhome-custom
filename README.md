# BTicino MyHome MH201 for Home Assistant

A local-first Home Assistant custom integration for **BTicino MyHome systems using an MH201 gateway and OpenWebNet**.

The integration communicates directly with the MH201 over the local network. It does **not** use the BTicino, Netatmo or Legrand cloud for device control.

> **Scope:** this project is intentionally focused on MH201/OpenWebNet. Audio, sound diffusion and music features are deliberately out of scope.

## Why this project?

The goal is to make a BTicino MyHome installation feel like a native Home Assistant system while keeping the control path local:

```text
Home Assistant
      │
      │ TCP / OpenWebNet
      ▼
   BTicino MH201
      │
      │ SCS / BUS
      ▼
 BTicino devices
```

There is no dependency on this path on:

```text
Home Assistant → Internet → BTicino/Netatmo/Legrand Cloud → MyHome
```

If Internet access or the manufacturer's cloud is unavailable, local Home Assistant control can continue to work as long as Home Assistant, the LAN and the MH201 remain available.

## Current capabilities

The current development line (0.1.9) focuses on:

- **WHO=1** — lighting
- **WHO=2** — automation / shutters / covers
- **WHO=3** — load management
- **WHO=5** — alarm / 4200C, with protocol support being expanded from real-world captures
- **WHO=7** — video door entry events and door-lock command
- **WHO=0** — OpenWebNet scenarios
- local gateway discovery through OWNd/SSDP
- persistent discovered-device inventory
- asynchronous OpenWebNet event monitoring
- automatic event-session reconnect with exponential backoff
- Home Assistant diagnostics
- an OpenWebNet frame monitor for protocol analysis

Passive learning is now available from the integration options: it listens to real OpenWebNet traffic without sending discovery commands, so pressing a physical BTicino control can identify the corresponding WHO/WHERE device. Climate and energy remain planned development areas. Music/sound diffusion is intentionally **not** planned.

## Installation

### HACS

Once the repository is published and added to HACS as a custom repository:

1. Open **HACS → Integrations**.
2. Add this repository as a custom integration if it is not already available.
3. Install **BTicino MyHome MH201**.
4. Restart Home Assistant.
5. Open **Settings → Devices & services → Add integration**.
6. Search for **BTicino MyHome**.

Home Assistant installs the Python dependency declared in `manifest.json` automatically:

```json
"requirements": [
  "OWNd==0.7.49"
]
```

You do not need to install OWNd manually on the Home Assistant host.

### Manual installation

Copy:

```text
custom_components/bticino_myhome/
```

to:

```text
/config/custom_components/bticino_myhome/
```

and restart Home Assistant.

## Configuration

The config flow first attempts to discover the MH201 on the local network. If discovery is not available, the gateway can be entered manually by IP address and port. The initial setup does not perform a bus-wide device scan; discovery is an explicit action from the integration Options flow so setup remains fast and deterministic.

Default OpenWebNet port:

```text
20000
```

The OpenWebNet password is stored in the Home Assistant ConfigEntry and is never included in diagnostics.

## Device model

The integration separates the local gateway from the discovered device inventory:

```text
ConfigEntry
   │
   ├── MH201 Gateway
   │      ├── command session
   │      └── event session
   │
   └── Device Manager
          ├── WHO/WHERE device
          ├── WHO/WHERE device
          └── WHO/WHERE device
```

This separation is intentional. The gateway owns connection/lifecycle and OWNd transport, while the dedicated protocol layer parses OpenWebNet frames, builds commands and produces normalized events. Discovery and Home Assistant platforms consume those normalized events without knowing OpenWebNet wire syntax.

## State handling

Commands are not treated as proof that a physical device changed state.

For example:

```text
Home Assistant → ON command
                  ↓
               MH201 / BUS
                  ↓
          OpenWebNet event
                  ↓
          Home Assistant state
```

This avoids optimistic states when the gateway is unavailable or a command fails.

The event connection is maintained asynchronously. If the event session is lost, the integration marks entities unavailable and retries with exponential backoff rather than blocking Home Assistant's event loop.

## Diagnostics

The integration provides Home Assistant diagnostics for troubleshooting.

Diagnostics include safe information such as:

- ConfigEntry metadata
- gateway connection status
- gateway port
- discovered devices and their types

Sensitive information is redacted before diagnostics are returned, including:

- OpenWebNet password
- gateway host/IP
- serial numbers
- MAC addresses

Use **Settings → Devices & services → BTicino MyHome → Download diagnostics** when reporting an issue.

## OpenWebNet frame monitor

The repository includes a read-only monitor:

```text
tools/openwebnet_monitor.py
```

It opens an OpenWebNet EVENT session and does not send control commands.

Example:

```bash
python tools/openwebnet_monitor.py 192.168.1.50
```

Save a capture:

```bash
python tools/openwebnet_monitor.py 192.168.1.50 --output capture.txt
```

Limit the capture to five minutes:

```bash
python tools/openwebnet_monitor.py 192.168.1.50 --seconds 300 --output capture.txt
```

The password is requested interactively.

### Debugging TX/RX from Home Assistant

Temporarily enable debug logging:

```yaml
logger:
  default: warning
  logs:
    custom_components.bticino_myhome.gateway: debug
```

The gateway logs frames as:

```text
OpenWebNet RX: ...
OpenWebNet TX: ...
```

Do not share passwords or credentials when sharing logs.

## Alarm development

Alarm support is deliberately being developed from real OpenWebNet traffic rather than guessed frame semantics.

For alarm analysis, capture normal operations such as:

1. disarmed state;
2. arm operation;
3. completed arm state;
4. disarm operation;
5. normal zone events, if applicable;
6. restore/reset events.

Do not deliberately trigger an alarm merely for testing. Use the procedures appropriate to the installed security system.

## Troubleshooting

### The gateway is discovered but setup fails

Check:

- Home Assistant can reach the MH201 IP address.
- TCP port `20000` is reachable.
- the OpenWebNet password is correct.
- the MH201 is powered and connected to the BUS.

### Devices become unavailable

This normally means the local event session has lost connectivity. Check the Home Assistant log for:

```text
OpenWebNet RX:
```

and connection/reconnect messages from the integration and OWNd.

### Internet is down

The integration itself does not require Internet access for local MH201 control. Functions belonging to other cloud-based integrations may of course stop working independently.

### Discovery does not find every device

OpenWebNet discovery is not equivalent to reading the complete configuration stored in Home+Project. Some devices/events are only observable when they generate traffic on the BUS. Use **Settings → Devices & services → BTicino MyHome → Configure → Impara dispositivi dai pulsanti fisici** to start passive learning. During the selected time window, press the physical BTicino controls you want to identify. No discovery command is transmitted in this mode.

## Technical documentation

Detailed architecture and protocol decisions are maintained in:

- `docs/architecture.md`
- `docs/protocol.md`
- `docs/discovery.md`
- `docs/roadmap.md`

These documents describe the intended boundaries before runtime validation on a real MH201.

## Development architecture

```text
                    Home Assistant
                           │
                     ConfigEntry
                           │
                 ┌─────────┴─────────┐
                 │                   │
             Gateway            Device Manager
                 │                   │
        ┌────────┴────────┐          │
        │                 │          │
 Command session     Event session   │
        │                 │          │
        └────────┬────────┘          │
                 ▼                   ▼
               OWNd          DiscoveredDevice
                 │                   │
                 └─────────┬─────────┘
                           ▼
                    HA entity platforms
```

The low-level OpenWebNet transport is delegated to **OWNd 0.7.49**. The integration owns the Home Assistant lifecycle, entity model, discovery inventory, availability and diagnostics.

## Roadmap

The project is intentionally developed in layers:

1. repository and Home Assistant quality cleanup;
2. robust gateway lifecycle and reconnect handling;
3. normalized device manager;
4. better UI-based device management;
5. passive bus learning and dynamic entity registration (`press a physical BTicino button → identify and add the device`);
6. diagnostics and troubleshooting improvements;
7. scenario events and triggers;
8. climate support where applicable;
9. energy support (`WHO=18`) where applicable;
10. deeper alarm (`WHO=5`) decoding from real installations;
11. video door-entry (`WHO=7`) improvements.

**Music/sound diffusion is explicitly excluded from the roadmap.**

## Project status

This is an active development project. The most protocol-sensitive areas, especially alarm and discovery, are being implemented conservatively from observed OpenWebNet traffic.

If reporting an issue, include:

- Home Assistant version;
- integration version;
- MH201 firmware if known;
- the relevant log excerpt;
- diagnostics with sensitive fields redacted automatically by Home Assistant.

## Protocol layer
The integration keeps OpenWebNet wire-format knowledge in `custom_components/bticino_myhome/protocol/`. The layer contains:

- `frame.py` — immutable parsed frame model;
- `parser.py` — raw event-frame parsing;
- `commands.py` — command and status-request builders;
- `normalizer.py` — semantic event normalization.

The gateway exposes both a raw debug stream and a normalized event stream. Home Assistant entities and the Discovery Engine consume the normalized stream, so they do not need to construct or parse raw OpenWebNet frames themselves.

An empty device inventory no longer triggers an implicit full scan during integration startup. Discovery remains an explicit operation through the integration options, which avoids coupling Home Assistant startup to a potentially long bus scan.

## Discovery Engine

The integration deliberately does not assume that every MyHome device has a physical button. Discovery therefore has three complementary sources:

```text
                    MH201
                      │
               OpenWebNet / OWNd
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
       Passive       Active      Manual
        events        probes       UI
          │           │           │
          └───────────┼───────────┘
                      ▼
              Discovery Engine
                      │
                      ▼
              DiscoveredDevice
                      │
                      ▼
               Device Manager
```

### Passive discovery

The integration listens to real OpenWebNet traffic. It does not send commands during passive learning. This is useful for physical controls such as lights and shutters, and can also identify sensors/thermostats/alarm events when those devices emit observable events.

### Active discovery

The integration can send status probes for supported WHO/WHERE ranges. A probe is **not** considered proof that an address exists: a device is accepted only when a matching OpenWebNet event is observed. This conservative approach avoids creating dozens of false devices for unused addresses.

### Manual discovery

Some MyHome endpoints may not expose a discoverable event or may require installation-specific knowledge. They can therefore be registered from the integration options by specifying WHO, WHERE, type and an optional name. Manual discovery is a fallback, not a requirement for normal devices.

All three paths produce the same normalized `DiscoveredDevice` object and are then handled by the Device Manager. This means future device platforms such as climate, energy and alarm do not need to know how the endpoint was discovered.

## Discovery source and capabilities

Every discovered endpoint records its source (`passive`, `active` or `manual`) and a normalized capability list. These fields are internal integration metadata and are also used to improve diagnostics and future device setup flows.
