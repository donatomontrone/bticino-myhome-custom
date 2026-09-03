"""BTicino MyHome gateway lifecycle management."""
from __future__ import annotations

import asyncio
import contextlib
import logging
from collections.abc import Callable
from typing import Any

from OWNd.connection import OWNCommandSession, OWNEventSession, OWNGateway, OWNSession

from .protocol import NormalizedEvent, normalize_frame, parse_frame

_LOGGER = logging.getLogger(__name__)

_COMMAND_TIMEOUT = 10.0
_CONNECT_TIMEOUT = 10.0
_CLOSE_TIMEOUT = 5.0
_RECONNECT_INITIAL_DELAY = 1.0
_RECONNECT_MAX_DELAY = 60.0


class BticinoGatewayError(Exception):
    """Raised when the gateway cannot be reached or used."""


class BticinoGateway:
    """Own the local OpenWebNet command and event sessions."""

    def __init__(self, host: str, port: int, password: str | None) -> None:
        self.host = host
        self.port = port
        self.password = password
        # OWNd 0.7.49 uses ``address`` in its gateway configuration mapping.
        self._gateway = OWNGateway({"address": host, "port": port, "password": password})
        self._command_session: OWNCommandSession | None = None
        self._event_session: OWNEventSession | None = None
        self._event_task: asyncio.Task[None] | None = None
        self._closing = False
        self._connected = False
        self._listeners: set[Callable[[str], None]] = set()
        self._event_listeners: set[Callable[[NormalizedEvent], None]] = set()
        self._connection_listeners: set[Callable[[bool], None]] = set()

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def gateway(self) -> OWNGateway:
        return self._gateway

    async def async_test_connection(self) -> bool:
        """Validate OpenWebNet negotiation without keeping a session."""
        session = OWNSession(gateway=self._gateway, connection_type="test", logger=_LOGGER)
        try:
            async with asyncio.timeout(_CONNECT_TIMEOUT):
                result = await session.test_connection()
            if not result or result.get("Success") is not True:
                raise BticinoGatewayError((result or {}).get("Message", "connection_failed"))
            return True
        except BticinoGatewayError:
            raise
        except (ConnectionError, TimeoutError) as err:
            raise BticinoGatewayError(str(err)) from err
        except Exception as err:
            raise BticinoGatewayError(str(err)) from err
        finally:
            await self._safe_close(session)

    async def async_connect(
        self,
        task_creator: Callable[[Any, str], asyncio.Task[None]] | None = None,
    ) -> None:
        """Connect command/event sessions and start the persistent event worker."""
        self._closing = False
        await self._connect_command_session()
        try:
            await self._connect_event_session()
        except Exception:
            await self._close_command_session()
            raise

        if self._event_task is None or self._event_task.done():
            if task_creator is None:
                self._event_task = asyncio.create_task(
                    self._event_loop(), name="bticino_myhome-event-loop"
                )
            else:
                self._event_task = task_creator(
                    self._event_loop(), "bticino_myhome-event-loop"
                )

    async def _connect_command_session(self) -> None:
        if self._command_session is not None:
            return
        session = OWNCommandSession(gateway=self._gateway, logger=_LOGGER)
        try:
            async with asyncio.timeout(_CONNECT_TIMEOUT):
                result = await session.connect()
        except TimeoutError as err:
            await self._safe_close(session)
            raise BticinoGatewayError("command_connection_timeout") from err
        except Exception as err:
            await self._safe_close(session)
            raise BticinoGatewayError(f"command_connection_failed: {err}") from err
        if not result or result.get("Success") is not True:
            await self._safe_close(session)
            raise BticinoGatewayError((result or {}).get("Message", "command_connection_failed"))
        self._command_session = session
        _LOGGER.debug("OpenWebNet command session connected")

    async def _connect_event_session(self) -> None:
        if self._event_session is not None:
            return
        session = OWNEventSession(gateway=self._gateway, logger=_LOGGER)
        try:
            async with asyncio.timeout(_CONNECT_TIMEOUT):
                result = await session.connect()
        except TimeoutError as err:
            await self._safe_close(session)
            raise BticinoGatewayError("event_connection_timeout") from err
        except Exception as err:
            await self._safe_close(session)
            raise BticinoGatewayError(f"event_connection_failed: {err}") from err
        if not result or result.get("Success") is not True:
            await self._safe_close(session)
            raise BticinoGatewayError((result or {}).get("Message", "event_connection_failed"))
        self._event_session = session
        self._set_connected(True)
        _LOGGER.debug("OpenWebNet event session connected")

    async def _event_loop(self) -> None:
        """Read event frames and recover the event session after failures."""
        backoff = _RECONNECT_INITIAL_DELAY
        try:
            while not self._closing:
                try:
                    await self._connect_event_session()
                    session = self._event_session
                    if session is None:
                        raise BticinoGatewayError("event_session_missing")
                    while not self._closing:
                        message = await session.get_next()
                        if message is None:
                            self._set_connected(False)
                            await self._close_event_session()
                            await asyncio.sleep(backoff)
                            backoff = min(backoff * 2, _RECONNECT_MAX_DELAY)
                            break

                        backoff = _RECONNECT_INITIAL_DELAY
                        raw = str(message).strip()
                        _LOGGER.debug("OpenWebNet RX: %s", raw)

                        for raw_listener in tuple(self._listeners):
                            try:
                                raw_listener(raw)
                            except Exception:
                                _LOGGER.exception("OpenWebNet raw listener failed")

                        frame = parse_frame(raw)
                        if frame is None:
                            continue
                        event = normalize_frame(frame)
                        for event_listener in tuple(self._event_listeners):
                            try:
                                event_listener(event)
                            except Exception:
                                _LOGGER.exception("OpenWebNet normalized event listener failed")
                except asyncio.CancelledError:
                    raise
                except (ConnectionError, TimeoutError, BticinoGatewayError) as err:
                    self._set_connected(False)
                    _LOGGER.info(
                        "MH201 event connection unavailable (%s). Retrying in %.1fs",
                        err,
                        backoff,
                    )
                    await self._close_event_session()
                    await asyncio.sleep(backoff)
                    backoff = min(backoff * 2, _RECONNECT_MAX_DELAY)
                except Exception as err:
                    self._set_connected(False)
                    _LOGGER.exception("MH201 event worker failed: %s", err)
                    await self._close_event_session()
                    await asyncio.sleep(backoff)
                    backoff = min(backoff * 2, _RECONNECT_MAX_DELAY)
        finally:
            self._set_connected(False)
            await self._close_event_session()

    async def async_send(self, frame: str, is_status_request: bool = False) -> None:
        """Send an OpenWebNet frame via the command session."""
        if self._closing:
            raise BticinoGatewayError("gateway_closing")
        session = self._command_session
        if session is None:
            raise BticinoGatewayError("command_session_missing")
        try:
            _LOGGER.debug("OpenWebNet TX: %s", frame)
            async with asyncio.timeout(_COMMAND_TIMEOUT):
                await session.send(message=frame, is_status_request=is_status_request)
        except asyncio.CancelledError:
            raise
        except (ConnectionError, TimeoutError) as err:
            await self._close_command_session()
            raise BticinoGatewayError(str(err)) from err
        except Exception as err:
            await self._close_command_session()
            raise BticinoGatewayError(str(err)) from err

    def add_listener(self, callback: Callable[[str], None]) -> Callable[[], None]:
        self._listeners.add(callback)

        def _remove() -> None:
            self._listeners.discard(callback)

        return _remove

    def add_event_listener(self, callback: Callable[[NormalizedEvent], None]) -> Callable[[], None]:
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
            except Exception:
                _LOGGER.exception("Connection-state listener failed")

    async def _close_command_session(self) -> None:
        session = self._command_session
        self._command_session = None
        if session is not None:
            await self._safe_close(session)

    async def _close_event_session(self) -> None:
        session = self._event_session
        self._event_session = None
        if session is not None:
            await self._safe_close(session)
        self._set_connected(False)

    async def async_close(self) -> None:
        """Close command/event sessions and cancel the event worker."""
        self._closing = True
        event_task = self._event_task
        self._event_task = None
        if event_task is not None and not event_task.done():
            event_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await event_task
        await self._close_command_session()
        await self._close_event_session()
        self._set_connected(False)

    async def _safe_close(self, session: OWNSession) -> None:
        try:
            async with asyncio.timeout(_CLOSE_TIMEOUT):
                await session.close()
        except TimeoutError:
            _LOGGER.warning("Timed out closing OWNd session")
        except Exception:
            _LOGGER.warning("Failed to close OWNd session", exc_info=True)


async def async_discover_gateways(timeout: int = 5) -> list[dict[str, Any]]:
    """Discover MH201 gateways via OWNd discovery."""
    from .discovery import BticinoDiscovery

    return await BticinoDiscovery.discover_gateways(timeout=timeout)
