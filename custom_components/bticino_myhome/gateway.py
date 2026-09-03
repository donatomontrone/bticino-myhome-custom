"""BTicino MyHome gateway lifecycle management."""
from __future__ import annotations

import asyncio
import contextlib
import logging
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from OWNd.connection import OWNCommandSession, OWNEventSession, OWNGateway, OWNSession
from OWNd.message import OWNMessage, OWNSignaling

from .protocol import NormalizedEvent, normalize_frame, parse_frame

if TYPE_CHECKING:
    from .discovery import DiscoveredGateway

_LOGGER = logging.getLogger(__name__)

_COMMAND_TIMEOUT = 10.0
_CONNECT_TIMEOUT = 10.0
_CLOSE_TIMEOUT = 5.0
_RECONNECT_INITIAL_DELAY = 1.0
_RECONNECT_MAX_DELAY = 60.0
_AUTH_FAILURES = {
    "password_error",
    "password_required",
    "password_retry",
    "negociation_error",
    "negotiation_error",
}

TaskCreator = Callable[[Coroutine[Any, Any, None], str], asyncio.Task[None]]


@dataclass(frozen=True, slots=True)
class BticinoCommandResult:
    """Result of one command-channel exchange."""

    acknowledged: bool
    responses: tuple[str, ...] = ()


class BticinoGatewayError(Exception):
    """Base error raised by the integration gateway layer."""


class BticinoGatewayConnectionError(BticinoGatewayError):
    """Raised when an OpenWebNet transport cannot be established or used."""


class BticinoGatewayAuthError(BticinoGatewayConnectionError):
    """Raised when OpenWebNet authentication is rejected."""


class BticinoGatewayCommandError(BticinoGatewayError):
    """Raised when a command-channel exchange fails."""


class BticinoGatewayCommandRejected(BticinoGatewayCommandError):
    """Raised when the gateway returns NACK for a command."""


class BticinoGatewayProtocolError(BticinoGatewayCommandError):
    """Raised when the command channel returns an unexpected signaling frame."""


def _connection_exception(message: str) -> BticinoGatewayConnectionError:
    normalized = message.strip() or "connection_failed"
    if normalized in _AUTH_FAILURES:
        return BticinoGatewayAuthError(normalized)
    return BticinoGatewayConnectionError(normalized)


class BticinoGateway:
    """Own the local OpenWebNet command and event sessions."""

    def __init__(
        self,
        host: str,
        port: int,
        password: str | None,
        identity: str | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self.password = password
        self.identity = identity or f"{host.strip().lower()}:{port}"
        self._gateway = OWNGateway({"address": host, "port": port, "password": password})
        self._command_session: OWNCommandSession | None = None
        self._event_session: OWNEventSession | None = None
        self._event_task: asyncio.Task[None] | None = None
        self._command_reconnect_task: asyncio.Task[None] | None = None
        self._task_creator: TaskCreator | None = None
        self._closing = False
        self._command_connected = False
        self._event_connected = False
        self._command_lock = asyncio.Lock()
        self._listeners: set[Callable[[str], None]] = set()
        self._event_listeners: set[Callable[[NormalizedEvent], None]] = set()
        self._connection_listeners: set[Callable[[bool], None]] = set()

    @property
    def connected(self) -> bool:
        return self._command_connected and self._event_connected

    @property
    def command_connected(self) -> bool:
        return self._command_connected

    @property
    def event_connected(self) -> bool:
        return self._event_connected

    @property
    def gateway(self) -> OWNGateway:
        return self._gateway

    async def async_test_connection(self) -> bool:
        session = OWNSession(gateway=self._gateway, connection_type="test", logger=_LOGGER)
        try:
            async with asyncio.timeout(_CONNECT_TIMEOUT):
                result = await session.test_connection()
            if not result or result.get("Success") is not True:
                raise _connection_exception(str((result or {}).get("Message", "connection_failed")))
            return True
        except BticinoGatewayError:
            raise
        except (ConnectionError, TimeoutError, asyncio.IncompleteReadError) as err:
            raise BticinoGatewayConnectionError(str(err)) from err
        except Exception as err:
            raise BticinoGatewayConnectionError(str(err)) from err
        finally:
            await self._safe_close(session)

    async def async_connect(self, task_creator: TaskCreator | None = None) -> None:
        self._closing = False
        self._task_creator = task_creator
        await self._connect_command_session()
        try:
            await self._connect_event_session()
        except Exception:
            await self._close_command_session()
            raise
        if self._event_task is None or self._event_task.done():
            self._event_task = self._create_task(
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
            self._set_command_connected(False)
            raise BticinoGatewayConnectionError("command_connection_timeout") from err
        except Exception as err:
            await self._safe_close(session)
            self._set_command_connected(False)
            raise BticinoGatewayConnectionError(f"command_connection_failed: {err}") from err
        if not result or result.get("Success") is not True:
            await self._safe_close(session)
            self._set_command_connected(False)
            raise _connection_exception(str((result or {}).get("Message", "command_connection_failed")))
        self._command_session = session
        self._set_command_connected(True)
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
            self._set_event_connected(False)
            raise BticinoGatewayConnectionError("event_connection_timeout") from err
        except Exception as err:
            await self._safe_close(session)
            self._set_event_connected(False)
            raise BticinoGatewayConnectionError(f"event_connection_failed: {err}") from err
        if not result or result.get("Success") is not True:
            await self._safe_close(session)
            self._set_event_connected(False)
            raise _connection_exception(str((result or {}).get("Message", "event_connection_failed")))
        self._event_session = session
        self._set_event_connected(True)
        if self._command_session is None:
            self._start_command_recovery()
        _LOGGER.debug("OpenWebNet event session connected")

    async def _read_event_raw(self, session: OWNEventSession) -> str:
        """Read one event frame without delegating reconnect ownership to OWNd."""
        reader = getattr(session, "_stream_reader", None)
        if reader is None:
            raise BticinoGatewayConnectionError("event_stream_unavailable")
        data = await reader.readuntil(OWNSession.SEPARATOR)
        return data.decode().strip()

    async def _event_loop(self) -> None:
        backoff = _RECONNECT_INITIAL_DELAY
        try:
            while not self._closing:
                try:
                    await self._connect_event_session()
                    session = self._event_session
                    if session is None:
                        raise BticinoGatewayConnectionError("event_session_missing")
                    while not self._closing:
                        raw = await self._read_event_raw(session)
                        backoff = _RECONNECT_INITIAL_DELAY
                        self._dispatch_raw(raw, source="event")
                except asyncio.CancelledError:
                    raise
                except (
                    ConnectionError,
                    TimeoutError,
                    asyncio.IncompleteReadError,
                    BticinoGatewayError,
                ) as err:
                    self._set_event_connected(False)
                    _LOGGER.debug(
                        "MH201 event connection retry after %s in %.1fs",
                        err,
                        backoff,
                    )
                    await self._close_event_session()
                    await asyncio.sleep(backoff)
                    backoff = min(backoff * 2, _RECONNECT_MAX_DELAY)
                except Exception as err:
                    self._set_event_connected(False)
                    _LOGGER.exception("MH201 event worker failed: %s", err)
                    await self._close_event_session()
                    await asyncio.sleep(backoff)
                    backoff = min(backoff * 2, _RECONNECT_MAX_DELAY)
        finally:
            self._set_event_connected(False)
            await self._close_event_session()

    async def _exchange_command(
        self, session: OWNCommandSession, frame: str
    ) -> BticinoCommandResult:
        """Exchange one command while retaining data frames OWNd normally discards.

        OWNd's public ``send`` method consumes status responses and owns its own
        retransmission/reconnect loop. The integration needs the response frames
        for state hydration and must not blindly retransmit ambiguous writes, so
        the already-negotiated session is used directly after connection setup.
        """
        writer = getattr(session, "_stream_writer", None)
        reader = getattr(session, "_stream_reader", None)
        if writer is None or reader is None:
            raise BticinoGatewayConnectionError("command_stream_unavailable")

        writer.write(str(frame).encode())
        await writer.drain()
        responses: list[str] = []

        while True:
            raw_response = await reader.readuntil(OWNSession.SEPARATOR)
            raw = raw_response.decode().strip()
            parsed = OWNMessage.parse(raw)
            if isinstance(parsed, OWNSignaling):
                if parsed.is_ack():
                    return BticinoCommandResult(True, tuple(responses))
                if parsed.is_nack():
                    return BticinoCommandResult(False, tuple(responses))
                raise BticinoGatewayProtocolError(f"unexpected_command_signaling:{raw}")
            responses.append(raw)

    async def async_send(
        self, frame: str, is_status_request: bool = False
    ) -> BticinoCommandResult:
        if self._closing:
            raise BticinoGatewayConnectionError("gateway_closing")
        async with self._command_lock:
            if self._closing:
                raise BticinoGatewayConnectionError("gateway_closing")
            if self._command_session is None:
                try:
                    await self._connect_command_session()
                except BticinoGatewayError:
                    self._start_command_recovery()
                    raise
            session = self._command_session
            if session is None:
                raise BticinoGatewayConnectionError("command_session_missing")
            try:
                _LOGGER.debug("OpenWebNet TX: %s", frame)
                async with asyncio.timeout(_COMMAND_TIMEOUT):
                    result = await self._exchange_command(session, frame)
                for response in result.responses:
                    self._dispatch_raw(response, source="command")
                if not result.acknowledged:
                    raise BticinoGatewayCommandRejected(f"command_rejected:{frame}")
                if not is_status_request:
                    _LOGGER.debug("OpenWebNet command acknowledged: %s", frame)
                return result
            except asyncio.CancelledError:
                raise
            except BticinoGatewayCommandRejected:
                raise
            except BticinoGatewayProtocolError:
                await self._close_command_session()
                self._start_command_recovery()
                raise
            except (ConnectionError, TimeoutError, asyncio.IncompleteReadError) as err:
                await self._close_command_session()
                self._start_command_recovery()
                raise BticinoGatewayCommandError(str(err)) from err
            except BticinoGatewayError:
                await self._close_command_session()
                self._start_command_recovery()
                raise
            except Exception as err:
                await self._close_command_session()
                self._start_command_recovery()
                raise BticinoGatewayCommandError(str(err)) from err

    def _dispatch_raw(self, raw: str, *, source: str) -> None:
        """Dispatch one raw frame through both integration listener layers."""
        raw = raw.strip()
        if not raw:
            return
        _LOGGER.debug("OpenWebNet RX (%s): %s", source, raw)
        for raw_listener in tuple(self._listeners):
            try:
                raw_listener(raw)
            except Exception:
                _LOGGER.exception("OpenWebNet raw listener failed")
        frame = parse_frame(raw)
        if frame is None:
            return
        event = normalize_frame(frame)
        for event_listener in tuple(self._event_listeners):
            try:
                event_listener(event)
            except Exception:
                _LOGGER.exception("OpenWebNet normalized event listener failed")

    def _start_command_recovery(self) -> None:
        if self._closing or not self._event_connected:
            return
        task = self._command_reconnect_task
        if task is not None and not task.done():
            return
        self._command_reconnect_task = self._create_task(
            self._command_reconnect_loop(), "bticino_myhome-command-reconnect"
        )

    async def _command_reconnect_loop(self) -> None:
        backoff = _RECONNECT_INITIAL_DELAY
        try:
            while not self._closing and self._event_connected and self._command_session is None:
                try:
                    async with self._command_lock:
                        if self._command_session is None:
                            await self._connect_command_session()
                    return
                except asyncio.CancelledError:
                    raise
                except BticinoGatewayError as err:
                    _LOGGER.debug(
                        "MH201 command connection retry after %s in %.1fs",
                        err,
                        backoff,
                    )
                    await asyncio.sleep(backoff)
                    backoff = min(backoff * 2, _RECONNECT_MAX_DELAY)
        finally:
            if self._command_reconnect_task is asyncio.current_task():
                self._command_reconnect_task = None

    def _create_task(
        self, coroutine: Coroutine[Any, Any, None], name: str
    ) -> asyncio.Task[None]:
        if self._task_creator is not None:
            return self._task_creator(coroutine, name)
        return asyncio.create_task(coroutine, name=name)

    def add_listener(self, callback: Callable[[str], None]) -> Callable[[], None]:
        self._listeners.add(callback)

        def _remove() -> None:
            self._listeners.discard(callback)

        return _remove

    def add_event_listener(
        self, callback: Callable[[NormalizedEvent], None]
    ) -> Callable[[], None]:
        self._event_listeners.add(callback)

        def _remove() -> None:
            self._event_listeners.discard(callback)

        return _remove

    def add_connection_listener(self, callback: Callable[[bool], None]) -> Callable[[], None]:
        self._connection_listeners.add(callback)
        callback(self.connected)

        def _remove() -> None:
            self._connection_listeners.discard(callback)

        return _remove

    def _set_command_connected(self, connected: bool) -> None:
        previous_aggregate = self.connected
        previous_channel = self._command_connected
        self._command_connected = connected
        if previous_channel != connected and not self._closing:
            _LOGGER.info(
                "MH201 command channel %s",
                "available" if connected else "unavailable",
            )
        self._notify_connection_change(previous_aggregate)

    def _set_event_connected(self, connected: bool) -> None:
        previous_aggregate = self.connected
        previous_channel = self._event_connected
        self._event_connected = connected
        if previous_channel != connected and not self._closing:
            _LOGGER.info(
                "MH201 event channel %s",
                "available" if connected else "unavailable",
            )
        self._notify_connection_change(previous_aggregate)

    def _notify_connection_change(self, previous: bool) -> None:
        connected = self.connected
        if previous == connected:
            return
        for listener in tuple(self._connection_listeners):
            try:
                listener(connected)
            except Exception:
                _LOGGER.exception("Connection-state listener failed")

    async def _close_command_session(self) -> None:
        session = self._command_session
        self._command_session = None
        self._set_command_connected(False)
        if session is not None:
            await self._safe_close(session)

    async def _close_event_session(self) -> None:
        session = self._event_session
        self._event_session = None
        self._set_event_connected(False)
        if session is not None:
            await self._safe_close(session)

    async def async_close(self) -> None:
        self._closing = True
        command_reconnect_task = self._command_reconnect_task
        self._command_reconnect_task = None
        if command_reconnect_task is not None and not command_reconnect_task.done():
            command_reconnect_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await command_reconnect_task
        event_task = self._event_task
        self._event_task = None
        if event_task is not None and not event_task.done():
            event_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await event_task
        await self._close_command_session()
        await self._close_event_session()

    async def _safe_close(self, session: OWNSession) -> None:
        try:
            async with asyncio.timeout(_CLOSE_TIMEOUT):
                await session.close()
        except TimeoutError:
            _LOGGER.warning("Timed out closing OWNd session")
        except Exception:
            _LOGGER.warning("Failed to close OWNd session", exc_info=True)


async def async_discover_gateways(timeout: int = 5) -> list[DiscoveredGateway]:
    from .discovery import BticinoDiscovery

    return await BticinoDiscovery.discover_gateways(timeout=timeout)
