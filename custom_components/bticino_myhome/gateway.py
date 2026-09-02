"""Local OpenWebNet gateway management for BTicino/Legrand MyHome."""
from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from typing import Any

from OWNd.connection import OWNCommandSession, OWNEventSession, OWNGateway, OWNSession
from OWNd.discovery import find_gateways

from .protocol import NormalizedEvent, normalize_frame, parse_frame

_LOGGER = logging.getLogger(__name__)


class BticinoGatewayError(Exception):
    """Raised when the gateway cannot be reached or used."""


class BticinoGateway:
    """Own the local OpenWebNet command and event sessions.

    OWNd 0.7.49 performs the actual TCP I/O with asyncio streams. This class
    owns the two OWNd sessions, exposes a small stable API to Home Assistant,
    and adds lifecycle/availability handling around them.
    """

    def __init__(self, host: str, port: int, password: str | None) -> None:
        self.host = host
        self.port = port
        self.password = password or None
        self._gateway = OWNGateway({
            "address": host,
            "port": port,
            "password": self.password,
            "modelName": "MH201",
            "manufacturer": "BTicino S.p.A.",
        })
        self._command_session: OWNCommandSession | None = None
        self._event_session: OWNEventSession | None = None
        self._event_task: asyncio.Task[None] | None = None
        self._send_lock = asyncio.Lock()
        self._listeners: set[Callable[[str], None]] = set()
        self._event_listeners: set[Callable[[NormalizedEvent], None]] = set()
        self._connection_listeners: set[Callable[[bool], None]] = set()
        self._connected = False
        self._closing = False

    @property
    def connected(self) -> bool:
        return self._connected

    async def async_test_connection(self) -> bool:
        """Validate OpenWebNet negotiation without keeping a session."""
        session = OWNSession(gateway=self._gateway, connection_type="test", logger=_LOGGER)
        try:
            result = await session.test_connection()
            if not result or result.get("Success") is not True:
                raise BticinoGatewayError((result or {}).get("Message", "connection_failed"))
            return True
        except BticinoGatewayError:
            raise
        except (ConnectionError, asyncio.TimeoutError) as err:
            raise BticinoGatewayError(str(err)) from err
        except Exception as err:  # noqa: BLE001
            raise BticinoGatewayError(str(err)) from err
        finally:
            try:
                await session.close()
            except Exception:  # noqa: BLE001
                _LOGGER.debug("Errore chiusura test session", exc_info=True)

    async def async_connect(self, *, task_creator: Callable[[Any, str], asyncio.Task] | None = None) -> None:
        """Connect command/event sessions and start the persistent event worker."""
        self._closing = False
        await self._connect_command_session()
        await self._connect_event_session()
        if self._event_task is None or self._event_task.done():
            coro = self._event_loop()
            if task_creator is not None:
                self._event_task = task_creator(coro, f"bticino-myhome-events-{self.host}")
            else:
                self._event_task = asyncio.create_task(coro, name=f"bticino-myhome-events-{self.host}")

    async def _connect_command_session(self) -> None:
        if self._command_session is not None:
            return
        session = OWNCommandSession(gateway=self._gateway, logger=_LOGGER)
        result = await session.connect()
        if not result or result.get("Success") is not True:
            await self._safe_close(session)
            raise BticinoGatewayError((result or {}).get("Message", "command_connection_failed"))
        self._command_session = session

    async def _connect_event_session(self) -> None:
        if self._event_session is not None:
            return
        session = OWNEventSession(gateway=self._gateway, logger=_LOGGER)
        result = await session.connect()
        if not result or result.get("Success") is not True:
            await self._safe_close(session)
            raise BticinoGatewayError((result or {}).get("Message", "event_connection_failed"))
        self._event_session = session
        self._set_connected(True)

    async def _event_loop(self) -> None:
        """Read event frames and recover the event session after failures."""
        backoff = 1.0
        while not self._closing:
            try:
                await self._connect_event_session()
                session = self._event_session
                if session is None:
                    raise BticinoGatewayError("event_session_missing")
                message = await session.get_next()
                if message is None:
                    self._set_connected(False)
                    # OWNd may already have reconnected internally. Give it one
                    # event-loop turn before reading again.
                    await asyncio.sleep(0)
                    continue
                self._set_connected(True)
                backoff = 1.0
                raw = str(message).strip()
                _LOGGER.debug("OpenWebNet RX: %s", raw)
                for listener in tuple(self._listeners):
                    try:
                        listener(raw)
                    except Exception:  # noqa: BLE001
                        _LOGGER.exception("Listener OpenWebNet non riuscito")

                frame = parse_frame(raw)
                if frame is not None:
                    event = normalize_frame(frame)
                    for listener in tuple(self._event_listeners):
                        try:
                            listener(event)
                        except Exception:  # noqa: BLE001
                            _LOGGER.exception("Listener evento OpenWebNet non riuscito")
            except asyncio.CancelledError:
                raise
            except (ConnectionError, asyncio.TimeoutError, BticinoGatewayError) as err:
                self._set_connected(False)
                _LOGGER.info(
                    "Connessione eventi MH201 non disponibile (%s). Riprovo tra %.1fs",
                    err, backoff,
                )
                await self._close_event_session()
                try:
                    await asyncio.sleep(backoff)
                except asyncio.CancelledError:
                    raise
                backoff = min(backoff * 2, 60.0)
            except Exception as err:  # noqa: BLE001
                self._set_connected(False)
                _LOGGER.exception("Worker eventi MH201 terminato in errore: %s", err)
                await self._close_event_session()
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 60.0)
        self._set_connected(False)

    async def async_send(self, frame: str, *, is_status_request: bool = False) -> None:
        """Send a raw OpenWebNet frame through OWNd's command session."""
        if self._closing:
            raise BticinoGatewayError("gateway_closing")
        async with self._send_lock:
            try:
                await self._connect_command_session()
                session = self._command_session
                if session is None:
                    raise BticinoGatewayError("command_session_missing")
                _LOGGER.debug("OpenWebNet TX: %s", frame)
                # OWNd 0.7.49 handles ACK/NACK and its own command-session
                # reconnect internally. Its send() API intentionally returns
                # no success value, so absence of an exception is the only
                # public success indication available to us.
                await session.send(message=frame, is_status_request=is_status_request)
            except asyncio.CancelledError:
                raise
            except (ConnectionError, asyncio.TimeoutError) as err:
                await self._close_command_session()
                raise BticinoGatewayError(str(err)) from err
            except Exception as err:  # noqa: BLE001
                await self._close_command_session()
                raise BticinoGatewayError(str(err)) from err

    def add_listener(self, callback: Callable[[str], None]) -> Callable[[], None]:
        self._listeners.add(callback)
        def _remove() -> None:
            self._listeners.discard(callback)
        return _remove

    def add_event_listener(self, callback: Callable[[NormalizedEvent], None]) -> Callable[[], None]:
        """Subscribe to parsed and normalized OpenWebNet events."""
        self._event_listeners.add(callback)

        def _remove() -> None:
            self._event_listeners.discard(callback)

        return _remove

    def add_connection_listener(self, callback: Callable[[bool], None]) -> Callable[[], None]:
        self._connection_listeners.add(callback)
        callback(self._connected)
        def _remove() -> None:
            self._connection_listeners.discard(callback)
        return _remove

    def _set_connected(self, connected: bool) -> None:
        if self._connected == connected:
            return
        self._connected = connected
        for listener in tuple(self._connection_listeners):
            try:
                listener(connected)
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Listener stato connessione non riuscito")

    @staticmethod
    async def _safe_close(session: Any) -> None:
        try:
            await session.close()
        except Exception:  # noqa: BLE001
            _LOGGER.debug("Errore chiusura sessione OWNd", exc_info=True)

    async def _close_command_session(self) -> None:
        session, self._command_session = self._command_session, None
        if session is not None:
            await self._safe_close(session)

    async def _close_event_session(self) -> None:
        session, self._event_session = self._event_session, None
        self._set_connected(False)
        if session is not None:
            await self._safe_close(session)

    async def async_close(self) -> None:
        """Stop the event worker and close all local OpenWebNet sessions."""
        self._closing = True
        current = asyncio.current_task()
        task = self._event_task
        self._event_task = None
        if task is not None and task is not current and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        await self._close_event_session()
        await self._close_command_session()
        self._listeners.clear()
        self._event_listeners.clear()
        self._connection_listeners.clear()


async def async_discover_gateways(timeout: int = 5) -> list[dict[str, Any]]:
    """Discover OpenWebNet gateways on the local LAN using OWNd SSDP."""
    del timeout  # OWNd 0.7.49 exposes no timeout argument on find_gateways().
    try:
        gateways = await find_gateways()
    except Exception as err:  # noqa: BLE001
        _LOGGER.warning("Discovery SSDP fallita: %s", err)
        return []
    result: list[dict[str, Any]] = []
    for gw in gateways:
        result.append({
            "host": gw.get("address"),
            "port": gw.get("port") or 20000,
            "serial": gw.get("serialNumber"),
            "model": gw.get("modelName") or "OpenWebNet Gateway",
            "manufacturer": gw.get("manufacturer"),
        })
    return [item for item in result if item["host"]]
