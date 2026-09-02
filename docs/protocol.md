# OpenWebNet protocol boundary

The integration intentionally keeps OpenWebNet syntax in one package:

```text
protocol/
  frame.py       Parsed frame model
  parser.py      Wire -> frame
  commands.py    Semantic command -> wire
  normalizer.py  Frame -> semantic event
```

Standard event frames have the shape:

```text
*WHO*WHAT*WHERE##
```

Status requests use the separate form:

```text
*#WHO*WHERE##
```

Status requests are not treated as device events by the parser.

The normalized event model currently provides generic state mappings for:

- WHO=1 lighting;
- WHO=2 automation/covers;
- WHO=3 load management;
- WHO=5 alarm.

WHO=7 and WHO=18 are recognized at the device classification level, while their
installation-specific semantics remain intentionally conservative.
