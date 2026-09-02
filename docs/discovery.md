# Discovery model

## Passive learning

Passive learning opens the event session and sends no discovery command.
When a real OpenWebNet event is received, the event is mapped to a supported
`DiscoveredDevice` and presented to the user for selection.

This is the safest mechanism for installations where the bus address space is
not known.

## Active discovery

Active discovery sends status requests for supported WHO/WHERE ranges.
A status request alone never creates a device. A matching event observed by the
event listener is required before the endpoint enters the discovery result.

This avoids manufacturing devices for unused addresses.

Scenario candidates are different: scenarios are virtual endpoints and can be
registered explicitly as candidates when the user enables the scenario option.

## Manual registration

Manual registration is the fallback for endpoints that cannot be discovered
through an observable event. The user supplies WHO, WHERE, type and optional
name.

## Inventory merge

The device key is `WHO-WHERE`.

When a passive event confirms an existing active candidate, the passive record
replaces the generic active candidate while preserving the user-selected name.
