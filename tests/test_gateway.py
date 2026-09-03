"""Tests for the BTicino MyHome gateway lifecycle."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.bticino_myhome.gateway import BticinoGateway, BticinoGatewayError


def _gateway() -> BticinoGateway:
    return BticinoGateway(host="127.0.0.1", port=20000, password="pwd")


def test_async_test_connection_success() -> None:
    """Verify successful connection test returns True."""
    async def scenario() -> None:
        gateway = _gateway()
        session = MagicMock()
        session.test_connection = AsyncMock(return_value={"Success": True})
        session.close = AsyncMock()

        with (
            patch("custom_components.bticino_myhome.gateway.OWNdSession", return_value=session),
            pytest.raises(BticinoGatewayError, match="command_session_missing"),
        ):
            await gateway.async_send("*1*1*21##")

        session.test_connection.assert_awaited_once()
        session.close.assert_awaited_once()

    asyncio.run(scenario())


def test_async_test_connection_failure_is_typed() -> None:
    """Verify failed connection test raises BticinoGatewayError."""
    async def scenario() -> None:
        gateway = _gateway()
        session = MagicMock()
        session.test_connection = AsyncMock(return_value={"Success": False, "Message": "auth_failed"})
        session.close = AsyncMock()

        with (
            patch("custom_components.bticino_myhome.gateway.OWNdSession", return_value=session),
            pytest.raises(BticinoGatewayError, match="auth_failed"),
        ):
            await gateway.async_test_connection()

        session.test_connection.assert_awaited_once()
        session.close.assert_awaited_once()

    asyncio.run(scenario())


def test_async_connect_starts_worker_and_async_close_cancels_it() -> None:
    """Verify async_connect starts the event worker and async_close cancels it."""
    async def scenario() -> None:
        gateway = _gateway()
        command = MagicMock()
        command.connect = AsyncMock(return_value={"Success": True})
        command.close = AsyncMock()

        event = MagicMock()
        event.connect = AsyncMock(return_value={"Success": True})
        event.close = AsyncMock()
        stop_event = asyncio.Event()

        async def wait_for_event() -> str:
            await stop_event.wait()
            return "*1*1*21##"

        event.get_next = AsyncMock(side_effect=wait_for_event)

        with (
            patch("custom_components.bticino_myhome.gateway.OWNCommandSession", return_value=command),
            patch("custom_components.bticino_myhome.gateway.OWNEventSession", return_value=event),
        ):
            await gateway.async_connect()
            assert gateway._event_task is not None
            await asyncio.sleep(0)
            assert event.get_next.await_count == 1
            assert gateway.connected is True

            await asyncio.wait_for(gateway.async_close(), timeout=1.0)

        command.connect.assert_awaited_once()
        event.connect.assert_awaited_once()
        command.close.assert_awaited_once()
        event.close.assert_awaited_once()
        assert gateway._event_task is None
        assert gateway.connected is False

    asyncio.run(scenario())


def test_event_loop_normalizes_frame_and_notifies_listeners() -> None:
    """Verify _event_loop normalizes frames and notifies listeners before exiting."""
    async def scenario() -> None:
        gateway = _gateway()
        event_session = MagicMock()
        event_session.get_next = AsyncMock(
            side_effect=["*1*1*21##", asyncio.CancelledError()]
        )
        event_session.close = AsyncMock()
        gateway._event_session = event_session
        gateway._set_connected(True)

        raw_listener = MagicMock()
        normalized_listener = MagicMock()
        connection_listener = MagicMock()
        gateway.add_listener(raw_listener)
        gateway.add_event_listener(normalized_listener)
        gateway.add_connection_listener(connection_listener)

        with pytest.raises(asyncio.CancelledError):
            await asyncio.wait_for(gateway._event_loop(), timeout=1.0)

        raw_listener.assert_called_once_with("*1*1*21##")
        normalized_listener.assert_called_once()
        normalized = normalized_listener.call_args.args[0]
        assert normalized.device_type == "light"
        assert normalized.state == "on"
        assert connection_listener.call_args_list[-1].args == (False,)
        event_session.close.assert_awaited_once()
        assert gateway._event_session is None

    asyncio.run(scenario())


def test_event_loop_reconnects_after_connection_error() -> None:
    """Verify the event loop reconnects after a ConnectionError."""
    async def scenario() -> None:
        gateway = _gateway()
        first = MagicMock()
        first.connect = AsyncMock(return_value={"Success": True})
        first.get_next = AsyncMock(side_effect=ConnectionError("lost"))
        first.close = AsyncMock()
        second = MagicMock()
        second.connect = AsyncMock(return_value={"Success": True})
        second.get_next = AsyncMock(side_effect=["*1*1*21##", asyncio.CancelledError()])
        second.close = AsyncMock()

        with (
            patch(
                "custom_components.bticino_myhome.gateway.OWNEventSession",
                side_effect=[first, second],
            ),
            patch("custom_components.bticino_myhome.gateway.asyncio.sleep", new=AsyncMock()),
            pytest.raises(asyncio.CancelledError),
        ):
            await asyncio.wait_for(gateway._event_loop(), timeout=1.0)

        first.connect.assert_awaited_once()
        first.close.assert_awaited_once()
        second.connect.assert_awaited_once()
        second.close.assert_awaited_once()
        assert gateway.connected is False

    asyncio.run(scenario())


def test_listener_exceptions_do_not_stop_event_loop() -> None:
    """Verify exceptions in listeners do not stop the event loop."""
    async def scenario() -> None:
        gateway = _gateway()
        event_session = MagicMock()
        event_session.get_next = AsyncMock(
            side_effect=["*1*1*21##", asyncio.CancelledError()]
        )
        event_session.close = AsyncMock()
        gateway._event_session = event_session

        failing_listener = MagicMock(side_effect=RuntimeError("listener failed"))
        healthy_listener = MagicMock()
        gateway.add_listener(failing_listener)
        gateway.add_listener(healthy_listener)

        with pytest.raises(asyncio.CancelledError):
            await asyncio.wait_for(gateway._event_loop(), timeout=1.0)

        failing_listener.assert_called_once()
        healthy_listener.assert_called_once_with("*1*1*21##")
        event_session.close.assert_awaited_once()

    asyncio.run(scenario())


def test_async_send_uses_command_session() -> None:
    """Verify async_send uses the command session."""
    async def scenario() -> None:
        gateway = _gateway()
        command = MagicMock()
        command.send = AsyncMock()
        gateway._command_session = command

        await gateway.async_send("*1*1*21##")

        command.send.assert_awaited_once_with(message="*1*1*21##", is_status_request=False)

    asyncio.run(scenario())


def test_async_send_raises_on_missing_command_session() -> None:
    """Verify async_send raises BticinoGatewayError when command session is missing."""
    async def scenario() -> None:
        gateway = _gateway()
        gateway._command_session = None

        with pytest.raises(BticinoGatewayError, match="command_session_missing"):
            await gateway.async_send("*1*1*21##")

    asyncio.run(scenario())


def test_async_send_propagates_timeout() -> None:
    """Verify async_send propagates timeout as BticinoGatewayError."""
    async def scenario() -> None:
        gateway = _gateway()
        command = MagicMock()
        command.send = AsyncMock(side_effect=TimeoutError("send_timeout"))
        command.close = AsyncMock()
        gateway._command_session = command

        with pytest.raises(BticinoGatewayError, match="send_timeout"):
            await gateway.async_send("*1*1*21##")

        command.close.assert_awaited_once()
        assert gateway._command_session is None

    asyncio.run(scenario())


def test_add_listener_returns_remover() -> None:
    """Verify add_listener returns a callable that removes the listener."""
    gateway = _gateway()
    callback = MagicMock()
    remover = gateway.add_listener(callback)

    assert callback in gateway._listeners
    remover()
    assert callback not in gateway._listeners


def test_add_event_listener_returns_remover() -> None:
    """Verify add_event_listener returns a callable that removes the listener."""
    gateway = _gateway()
    callback = MagicMock()
    remover = gateway.add_event_listener(callback)

    assert callback in gateway._event_listeners
    remover()
    assert callback not in gateway._event_listeners


def test_add_connection_listener_returns_remover() -> None:
    """Verify add_connection_listener returns a callable that removes the listener."""
    gateway = _gateway()
    callback = MagicMock()
    remover = gateway.add_connection_listener(callback)

    assert callback in gateway._connection_listeners
    remover()
    assert callback not in gateway._connection_listeners


def test_connection_listener_notified_on_state_change() -> None:
    """Verify connection listeners are notified on state changes."""
    gateway = _gateway()
    callback = MagicMock()
    gateway.add_connection_listener(callback)

    callback.assert_called_once_with(False)

    gateway._set_connected(True)
    callback.assert_called_with(True)

    gateway._set_connected(True)
    assert callback.call_count == 2


def test_gateway_property_returns_ownd_gateway() -> None:
    """Verify gateway property returns the OWNd gateway instance."""
    gateway = _gateway()
    assert gateway.gateway is not None
    assert gateway.gateway.host == "127.0.0.1"
    assert gateway.gateway.port == 20000


def test_connected_property_tracks_session_state() -> None:
    """Verify connected property tracks session state."""
    gateway = _gateway()
    assert gateway.connected is False

    gateway._set_connected(True)
    assert gateway.connected is True

    gateway._set_connected(False)
    assert gateway.connected is False


def test_async_close_is_idempotent() -> None:
    """Verify async_close can be called multiple times safely."""
    async def scenario() -> None:
        gateway = _gateway()
        await gateway.async_close()
        await gateway.async_close()
        assert gateway._closing is True

    asyncio.run(scenario())


def test_event_loop_exits_cleanly_on_closing_flag() -> None:
    """Verify _event_loop exits cleanly when _closing flag is set."""
    async def scenario() -> None:
        gateway = _gateway()
        event_session = MagicMock()
        event_session.get_next = AsyncMock(side_effect=asyncio.CancelledError())
        event_session.close = AsyncMock()
        gateway._event_session = event_session
        gateway._set_connected(True)
        gateway._closing = True

        await asyncio.wait_for(gateway._event_loop(), timeout=1.0)

        assert gateway._closing is True
        assert gateway.connected is False
        event_session.close.assert_awaited_once()

    asyncio.run(scenario())
