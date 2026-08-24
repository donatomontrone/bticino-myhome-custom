#!/usr/bin/env python3
"""OpenWebNet event monitor for a BTicino/Legrand MH201.

This tool is intentionally read-only: it opens an OpenWebNet EVENT session and
prints the frames emitted by the gateway. It does not send alarm/light/etc.
commands.

Usage:
  python tools/openwebnet_monitor.py 192.168.1.50 --password 12345
  python tools/openwebnet_monitor.py 192.168.1.50 --password-file password.txt

If you do not provide a password, the tool prompts for it without echoing.
The password is never printed or written to the capture file.
"""
from __future__ import annotations

import argparse
import asyncio
import getpass
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from OWNd.connection import OWNEventSession, OWNGateway


class _NoSecretsFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return True


def _timestamp() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="milliseconds")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ascolta e registra i frame OpenWebNet ricevuti dal MH201."
    )
    parser.add_argument("host", help="IP/hostname locale del MH201")
    parser.add_argument("--port", type=int, default=20000, help="Porta OpenWebNet (default: 20000)")
    parser.add_argument("--password", help="Password OpenWebNet (sconsigliato: ometterla e usare il prompt)")
    parser.add_argument("--password-file", type=Path, help="File contenente solo la password OpenWebNet")
    parser.add_argument("--output", type=Path, help="File di cattura; se omesso stampa solo sul terminale")
    parser.add_argument("--seconds", type=float, default=0, help="Durata in secondi; 0 = fino a Ctrl+C")
    parser.add_argument("--keepalive", action="store_true", help="Mostra anche messaggi non-frame restituiti da OWNd")
    return parser


def _read_password(args: argparse.Namespace) -> str | None:
    if args.password is not None:
        return args.password
    if args.password_file:
        return args.password_file.read_text(encoding="utf-8").strip() or None
    return getpass.getpass("Password OpenWebNet (invio se non richiesta): ") or None


async def _run(args: argparse.Namespace) -> None:
    password = _read_password(args)
    gateway = OWNGateway(
        {
            "address": args.host,
            "port": args.port,
            "password": password,
            "modelName": "MH201",
            "manufacturer": "BTicino S.p.A.",
        }
    )
    session = OWNEventSession(gateway=gateway, logger=logging.getLogger("OWNd"))
    output = args.output.open("a", encoding="utf-8") if args.output else None

    def emit(direction: str, payload: object) -> None:
        text = str(payload).strip()
        if not text and not args.keepalive:
            return
        line = f"{_timestamp()} {direction} {text}"
        print(line, flush=True)
        if output:
            output.write(line + "\n")
            output.flush()

    try:
        print(f"Connessione EVENT a {args.host}:{args.port} ...", flush=True)
        result = await session.connect()
        if result is None or result.get("Success") is False:
            raise RuntimeError((result or {}).get("Message", "connessione fallita"))
        print("Connesso. Monitor in sola lettura; non vengono inviati comandi. Ctrl+C per terminare.", flush=True)

        async def reader() -> None:
            while True:
                message = await session.get_next()
                if message is None:
                    await asyncio.sleep(0.1)
                    continue
                emit("RX", message)

        task = asyncio.create_task(reader())
        try:
            if args.seconds > 0:
                await asyncio.sleep(args.seconds)
            else:
                await asyncio.Event().wait()
        finally:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
    finally:
        try:
            await session.close()
        except Exception:
            pass
        if output:
            output.close()


def main() -> int:
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    args = _build_parser().parse_args()
    try:
        asyncio.run(_run(args))
    except KeyboardInterrupt:
        print("\nMonitor terminato.")
    except Exception as err:  # noqa: BLE001
        print(f"ERRORE: {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
