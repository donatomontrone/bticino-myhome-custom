# OpenWebNet protocol boundary

The integration intentionally keeps OpenWebNet syntax in one package:

```text
protocol/
  frame.py              Parsed frame model
  parser.py             Wire -> frame
  commands.py           Generic semantic command -> wire helpers
  normalizer.py         Frame -> semantic event
  thermoregulation.py   WHO=4 constants, states and command builders
```

Standard event frames have the shape:

```text
*WHO*WHAT*WHERE##
```

The parser accepts OpenWebNet parameterized WHERE forms such as `#1` on received
standard events, while requests and dimension writes are still excluded from the
device-event path.

Status requests use the separate form:

```text
*#WHO*WHERE##
```

Status requests are not treated as device events by the parser.

Generic normalized-state mappings remain intentionally small. WHO=4 numeric
semantics live in `thermoregulation.py` because they are defined by the public
BTicino/Legrand OpenWebNet thermoregulation specification and should not be mixed
with unrelated families.

The WHO=4 software model currently covers:

- documented heating / conditioning / generic operation families;
- anti-freeze, thermal-protection and generic-protection states;
- manual / programming / OFF mode families;
- zone commands routed through the central-unit `#WHERE` form;
- DIM=14 setpoint writes with temperature plus operation-mode value;
- conservative DIM=19 active-output decoding.

This is specification-aligned software behavior, not a claim of physical MH201
validation. Gateway/installation-specific behavior remains experimental until a
real capture campaign is available.

The generic normalized event model provides state mappings for:

- WHO=1 lighting;
- WHO=2 automation/covers;
- WHO=3 load management;
- WHO=4 thermoregulation through its dedicated module;
- WHO=5 alarm.

WHO=7 and WHO=18 are recognized at the device classification level, while their
installation-specific semantics remain intentionally conservative.
