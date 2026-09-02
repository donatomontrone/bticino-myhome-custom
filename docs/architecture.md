# Architecture

## Goals

The integration is designed around four boundaries:

1. OpenWebNet protocol representation.
2. Local MH201 transport and connection lifecycle.
3. Discovery and persistent device inventory.
4. Home Assistant entity platforms.

The Home Assistant layer must not construct OpenWebNet wire frames directly.
The transport layer must not contain entity-specific behavior.

```text
Home Assistant
      |
      v
ConfigEntry / Options Flow
      |
      +--------------------+
      |                    |
      v                    v
BticinoGateway       DeviceManager
      |
      +--------------------+
      |                    |
      v                    v
OWNd sessions        DiscoveredDevice
      |
      v
OpenWebNet protocol
      |
      v
MH201 / SCS BUS
```

## Protocol boundary

`protocol/` owns:

- parsed frame representation;
- event parsing;
- command construction;
- semantic event normalization.

The public protocol API is exported from `protocol/__init__.py`.

## Gateway boundary

`gateway.py` owns:

- OWNd command session;
- OWNd persistent event session;
- reconnect lifecycle;
- command serialization;
- normalized event dispatch;
- connection availability.

Raw event listeners remain available only for diagnostics/compatibility. Normal
entities use normalized events.

## Discovery boundary

Discovery has three explicit sources:

- passive: observe real bus traffic;
- active: send status probes and require event confirmation;
- manual: explicit WHO/WHERE registration.

All three produce `DiscoveredDevice` records.

## Inventory boundary

`BticinoDeviceManager` is the runtime inventory. The ConfigEntry persists its
serialized representation under `entry.data["devices"]`.

Future work should move persistence to a dedicated storage abstraction rather
than allowing entity platforms to update ConfigEntry data directly.

## Entity boundary

Entity platforms consume `DiscoveredDevice` and normalized protocol events.
They do not parse OpenWebNet syntax.

## Explicit non-goals

WHO=22, media player, audio, music and sound-diffusion features are outside the
project scope.
