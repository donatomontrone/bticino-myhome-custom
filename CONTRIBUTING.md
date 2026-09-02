# Contributing

Thanks for contributing to BTicino MyHome MH201.

## Scope

This project targets local BTicino/Legrand MyHome SCS installations using an MH201 gateway and OpenWebNet. It does not implement WHO=22, media-player, audio, music, or sound-diffusion functionality.

Protocol behavior must be based on documented OpenWebNet semantics or real captures from compatible installations. Do not infer unsupported WHO/WHAT behavior from unrelated protocols.

## Development environment

Use Python 3.12 or 3.13. The development environment is pinned to the integration's minimum supported Home Assistant release and OWNd version.

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

## Validation

Run the same checks used by CI before opening a pull request:

```bash
python -m pytest
ruff check .
mypy
```

The integration also has dedicated GitHub Actions for Home Assistant hassfest validation and HACS validation.

## Protocol changes

When adding or changing protocol support, add a fixture/test for the observed frame and document its semantics. Prefer centralized command builders and normalized events over raw OpenWebNet strings in entity implementations.

For discovery changes, preserve the distinction between passive observations, active probes, and manually configured devices.

## Pull requests

Keep changes focused and include tests for regressions. Do not add cloud dependencies for local gateway control. Avoid protocol guesses where no reliable capture or specification is available.
