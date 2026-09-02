"""BTicino MyHome gateway lifecycle management."""
from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from typing import Any

from OWNd.connection import OWNCommandSession, OWNEventSession, OWNGateway, OWNSession

from .const import CONF_GATEWAY_HOST, CONF_GATEWAY_PASSWORD, CONF_GATEWAY_PORT
from .protocol import NormalizedEvent

_LOGGER = logging.getLogger(__name__)

_COMMAND_TIMEOUT = 10.0
_CONNECT_TIMEOUT = 10.0
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
        self._gateway = OWNGateway(host=host, port=port, password=password)
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
            try:
                await session.close()
            except Exception:
                _LOGGER.warning("Failed to close OWNd test session", exc_info=True)

    async def async_connect(self, task_creator: Callable[[Callable[[], Any], str], asyncio.Task[Any]] | None = None) -> None:
        """Connect command/event sessions and start the persistent event worker."""
        self._closing = False
        await self._connect_command_session()
        try:
            await self._connect_event_session()
        except Exception:
            await self._close_command_session()
            raise

        if self._event_task is None or self._event_task.done():
            coro = self._event_loop()
            if task_creator is not None:
                self._event_task = task_creator(coro, "bticino_myhome-event-loop")
            else:
                try:
                    self._event_task = asyncio.create_task(coro, name="bticino_myhome-event-loop")
                except RuntimeError:
                    # No running event loop (e.g., during some test scenarios)
                    _LOGGER.debug("Cannot create event loop task - no running event loop")

    async def _connect_command_session(self) -> None:
        """Open command session for sending frames."""
        if self._command_session is not None:
            return
        session = OWNCommandSession(gateway=self._gateway, logger=_LOGGER)
        try:
            async with asyncio.timeout(_CONNECT_TIMEOUT):
                result = await session.connect()
            _LOGGER.debug("Command session connected: %s", result)
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

    async def _connect_event_session(self) -> None:
        """Open event session for receiving frames."""
        if self._event_session is not None:
            return
        session = OWNEventSession(gateway=self._gateway, logger=_LOGGER)
        try:
            async with asyncio.timeout(_CONNECT_TIMEOUT):
                result = await session.connect()
            _LOGGER.debug("Event session connected: %s", result)
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

    async def _event_loop(self) -> None:
        """Read event frames and recover the event session after failures."""
        backoff = _RECONNECT_INITIAL_DELAY
        while not self._closing:
            try:
                await self._connect_event_session()
                session = self._event_session
                while True:
                    message = await session.get_next()
                    if message is None:
                        self._set_connected(False)
                        await self._close_event_session()
                        await asyncio.sleep(backoff)
                        backoff = min(backoff * 2, _RECONNECT_MAX_DELAY)
                        continue
                    self._set_connected(True)
                    backoff = _RECONNECT_INITIAL_DELAY
                    raw = str(message).strip()
                    _LOGGER.debug("OpenWebNet RX: %s", raw)

                    raw_listeners: tuple[Callable[[str], None], ...] = tuple(self._listeners)
                    for raw_listener in raw_listeners:
                        try:
                            raw_listener(raw)
                        except Exception:
                            _LOGGER.exception("OpenWebNet raw listener failed")

                    try:
                        event = NormalizedEvent.from_openwebnet(raw)
                    except ValueError:
                        continue

                    if event is not None:
                        event_listeners: tuple[Callable[[NormalizedEvent], None], ...] = tuple(self._event_listeners)
                        for event_listener in event_listeners:
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
                try:
                    await asyncio.sleep(backoff)
                except asyncio.CancelledError:
                    raise
                backoff = min(backoff * 2, _RECONNECT_MAX_DELAY)
            except Exception as err:
                self._set_connected(False)
                _LOGGER.exception("MH201 event worker failed: %s", err)
                await self._close_event_session()
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, _RECONNECT_MAX_DELAY)
        self._set_connected(False)

    async def async_send(self, frame: str, is_status_request: bool = False) -> None:
        """Send an OpenWebNet frame via the command session."""
        while not self._closing:
            try:
                session = self._command_session
                if session is None:
                    raise BticinoGatewayError("command_session_missing")
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
            return
        raise BticinoGatewayError("gateway_closing")

    def add_listener(self, callback: Callable[[str], None]) -> Callable[[], None]:
        """Subscribe to raw OpenWebNet event frames."""
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
        """Subscribe to gateway connection-state changes."""
        self._connection_listeners.add(callback)
        callback(self._connected)

        def _remove() -> None:
            self._connection_listeners.discard(callback)

        return _remove

    def _set_connected(self, connected: bool) -> None:
        if self._connected == connected:
            return
        self._connected = connected
        listeners: tuple[Callable[[bool], None], ...] = tuple(self._connection_listeners)
        for listener in listeners:
            try:
                listener(connected)
            except Exception:
                _LOGGER.exception("Connection-state listener failed")

    async def _close_command_session(self) -> None:
        session = self._command_session
        if session is None:
            return
        self._command_session = None
        await self._safe_close(session)

    async def _close_event_session(self) -> None:
        session = self._event_session
        if session is None:
            return
        self._event_session = None
        await self._safe_close(session)

    async def async_close(self) -> None:
        """Close command/event sessions and cancel the event worker."""
        self._closing = True
        if self._event_task is not None and not self._event_task.done():
            self._event_task.cancel()
            try:
                await self._event_task
            except asyncio.CancelledError:
                pass
        await self._close_command_session()
        await self._close_event_session()
        self._set_connected(False)

    async def _safe_close(self, session: OWNSession) -> None:
        try:
            await session.close()
        except Exception:
            _LOGGER.warning("Failed to close OWNd session", exc_info=True)


async def async_discover_gateways(timeout: int = 5) -> list[dict[str, Any]]:
    """Discover MH201 gateways via OWNd's SSDP/OWS discovery."""
    # Lazy import to avoid circular dependency
    from .discovery import BticinoDiscovery
    
    try:
        gateways = await BticinoDiscovery.discover_gateways(timeout=timeout)
    except Exception as err:
        _LOGGER.warning("OWS/SSDP gateway discovery failed: %s", err)
        return []

    result = []
    for gw in gateways:
        result.append({
            "host": gw.get("host"),
            "port": gw.get("port", 20000),
            "serial": gw.get("serial"),
            "model": gw.get("modelName") or "OpenWebNet Gateway",
            "manufacturer": gw.get("manufacturer"),
        })
    return [item for item in result if item["host"]]
