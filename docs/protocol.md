# OpenWebNet protocol boundary

This document records the protocol decisions used by the Home Assistant integration. The primary source is the official BTicino/Legrand OpenWebNet documentation published through https://developer.legrand.com/local-interoperability/ . Mature MyHOME/OWNd/openHAB implementations are used only as secondary cross-checks.

## General frame model

OpenWebNet standard events use:

```text
*WHO*WHAT*WHERE##
```

Status requests use:

```text
*#WHO*WHERE##
```

Dimension requests use:

```text
*#WHO*WHERE*DIMENSION##
```

Dimension writes use:

```text
*#WHO*WHERE*#DIMENSION*VAL1*VAL2*...##
```

The integration keeps raw wire parsing separate from semantic normalization. Requests and dimension writes are not emitted as device events.

## Conservative WHERE parsing

Generic standard endpoint events reject parameterized `#WHERE` values. Two explicit exceptions are modeled because their address forms are documented and have dedicated semantics:

- WHO=4 thermoregulation central-unit zones such as `#1`;
- WHO=5 burglar-alarm central partitions/auxiliary sources such as `#1..#N`.

WHO=5 parameterized WHERE frames are state/event evidence and are not automatically treated as independent discoverable endpoint devices.

## WHO=0 — scenarios

Scenario activation follows documented WHO=0 frames. The integration does not synthesize a full range of possible scenario addresses during discovery; only observed or explicitly configured scenarios become inventory endpoints.

## WHO=1 — lighting

Project scope is intentionally limited to documented basic lighting ON/OFF:

```text
*1*1*WHERE##   ON
*1*0*WHERE##   OFF
*#1*WHERE##    status request
```

The official WHO=1 specification contains dimmer, RGB and tunable-white semantics, but those surfaces are permanently excluded from this MH201 project. No brightness, dimmer or transition estimation is implemented.

## WHO=2 — automation / shutters

Base shutters use WHAT 0/1/2 for stop/up/down.

Advanced shutter support is capability-gated and uses the official WHO=2 dimensions:

- DIM=10 — advanced shutter status/position;
- DIM=11 — GoToLevel.

DIM=10 position mapping follows the official specification:

- `0` = fully closed;
- `1..99` = current percentage;
- `100` = fully open;
- `255` = unknown.

Home Assistant `SET_POSITION` is exposed only when advanced capability is configured or proven by a valid DIM=10 event. Basic shutters never receive a synthetic percentage based on travel time. Writes are non-optimistic.

## WHO=4 — thermoregulation

WHO=4 has a dedicated protocol module. The current software model covers the documented heating, conditioning and generic operation families, protection/off/manual/programming states, standalone and central-zone routing, and selected dimensions:

- DIM=0 temperature;
- DIM=12 complete probe status;
- DIM=14 setpoint read/write;
- DIM=19 valves/output state.

Manual inventory supports heating-only, cooling-only and heating+cooling profiles. A heating-only KW4691-style zone therefore does not expose cooling functions merely because the general WHO=4 specification contains them.

State remains evidence-driven; commands do not locally fabricate HVAC mode, preset or setpoint confirmation.

## WHO=5 — burglar alarm / BTicino 4200C target

The official WHO=5 catalogue used by the integration includes:

- WHAT=4 system battery fault;
- WHAT=5 battery OK;
- WHAT=6 no network;
- WHAT=7 network present;
- WHAT=8 engaged;
- WHAT=9 disengaged;
- WHAT=10 battery unloaded/KO;
- WHAT=11 active zone/partition;
- WHAT=12 technical alarm;
- WHAT=13 reset technical alarm;
- WHAT=14 no reception / peripheral ACK condition;
- WHAT=15 intrusion alarm;
- WHAT=16 24h/tampering alarm;
- WHAT=17 anti-panic alarm;
- WHAT=18 non-active/partialized zone;
- WHAT=31 silent alarm.

Central snapshot hydration uses:

```text
*#5*0##
```

Partition status requests use:

```text
*#5*#N##
```

for the modeled partitions 1–8.

The 4200C Home Assistant surface is evidence-driven and models:

- central engaged/disengaged/triggered state;
- eight active/partialized partition sensors;
- battery-problem diagnostic: WHAT 4/10 = problem, WHAT 5 = OK;
- network connectivity: WHAT 6 = unavailable, WHAT 7 = present;
- technical-alarm AUX sensors: WHAT 12 = active, WHAT 13 = reset on the same `#N`.

WHAT=14 is deliberately not converted into a persistent binary state because the public/reference material does not provide a sufficiently unambiguous reset lifecycle for the target installation.

Control builders for full arm/disarm and partition operations follow legacy BTicino OpenWebNet alarm-control syntax and established implementation precedent:

```text
*5*8##          full engage
*5*9##          full disengage
*5*8#...##      engage with selected active partitions
*5*11*#N##      activate one partition
*5*18*#N##      partialize one partition
```

These control frames are reference-backed and deterministic-test-covered but remain hardware-validation-pending on the target 4200C through MH201.

## WHO=6 — door entry / HomeTouch target

Door-entry control is kept separate from public WHO=7 multimedia semantics.

The project currently exposes a conservative reference-backed WHO=6 door-release builder. Public Legrand documentation does not provide a sufficiently reliable HomeTouch ring start/end lifecycle for this target, so the integration does not invent one.

Raw WHO=6/7 diagnostic capture remains available, disabled by default, to identify the actual HomeTouch/MH201 call lifecycle when hardware becomes available.

## WHO=7 — multimedia / VDE cameras

The official WHO=7 document describes the multimedia/camera subsystem, including video reception/freeing resources, zoom, image coordinates, luminosity, contrast, color and image quality.

This project does not expose those controls as Home Assistant camera/media entities because audio/video streaming is outside scope. WHO=7 frames may still be observed through the raw diagnostic path when investigating HomeTouch call traffic.

## WHO=18 — Energy Management

Energy Management is modeled only through documented WHO=18 semantics. WHO=3 is not part of this integration.

The current production surface is intentionally narrow:

- documented `5N` energy-meter endpoints;
- DIM=113 Active Power;
- unit: watt;
- Home Assistant `SensorDeviceClass.POWER`;
- `SensorStateClass.MEASUREMENT`;
- initial DIM=113 request plus event/response-driven updates;
- no periodic polling and no optimistic values.

The official WHO=18 document also defines totalizers and additional dimensions, but those remain deferred until unit/reset semantics and real MH201 behavior are validated strongly enough for correct Home Assistant state-class modeling.

## Permanent exclusions

Do not add these surfaces without an explicit project-scope change:

- WHO=22;
- WHO=1 dimmer/brightness/transition;
- WHO=3 load-management semantics;
- media player, audio, music and sound diffusion;
- VDE/HomeTouch audio/video streaming or camera entities.

## Validation terminology

**Spec/reference validated** means the implemented software behavior is derived from official OpenWebNet documentation, cross-checked with established implementations where useful and covered by deterministic tests.

**Hardware validated** additionally requires representative traffic and behavior from the real target MH201/MyHome installation.

Until physical validation is available, software tests must never be described as proof that a specific 4200C, HomeTouch, KW4691, actuator or energy meter accepts a command in the target installation.
