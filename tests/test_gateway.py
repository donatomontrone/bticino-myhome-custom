from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.bticino_myhome.gateway import BticinoGateway, BticinoGatewayError


def _gateway() -> BticinoGateway:
    with patch("custom_components.bticino_myhome.gateway.OWNGateway"):
        return BticinoGateway("192.0.2.10", 20000, "password")


def test_async_test_connection_success() -> None:
    gateway = _gateway()
    session = MagicMock()
    session.test_connection = AsyncMock(return_value={"Success": True})
    session.close = AsyncMock()

    with patch(
        "custom_components.bticino_myhome.gateway.OWNSession", return_value=session
    ) as session_class:
        assert asyncio.run(gateway.async_test_connection()) is True

    session_class.assert_called_once()
    session.test_connection.assert_awaited_once()
    session.close.assert_awaited_once()


def test_async_test_connection_failure_is_typed() -> None:
    gateway = _gateway()
    session = MagicMock()
    session.test_connection = AsyncMock(
        return_value={"Success": False, "Message": "authentication_failed"}
    )
    session.close = AsyncMock()

    with patch("custom_components.bticino_myhome.gateway.OWNSession", return_value=session):
        with pytest.raises(BticinoGatewayError, match="authentication_failed"):
            asyncio.run(gateway.async_test_connection())

    session.close.assert_awaited_once()


def test_async_connect_opens_command_and_event_sessions() -> None:
    gateway = _gateway()
    command = MagicMock()
    command.connect = AsyncMock(return_value={"Success": True})
    command.close = AsyncMock()
    event = MagicMock()
    event.connect = AsyncMock(return_value={"Success": True})
    event.close = AsyncMock()
    event.get_next = AsyncMock(side_effect=asyncio.CancelledError())

    with (
        patch("custom_components.bticino_myhome.gateway.OWNCommandSession", return_value=command),
        patch("custom_components.bticino_myhome.gateway.OWNEventSession", return_value=event),
    ):
        asyncio.run(gateway.async_connect())
        assert gateway.connected is True
        assert gateway._event_task is not None
        asyncio.run(gateway.async_close())

    command.connect.assert_awaited_once()
    event.connect.assert_awaited_once()
    command.close.assert_awaited_once()
    event.close.assert_awaited_once()
    assert gateway.connected is False


def test_event_loop_normalizes_frame_and_notifies_listeners() -> None:
    gateway = _gateway()
    event_session = MagicMock()
    event_session.get_next = AsyncMock(side_effect=["*1*1*21##", asyncio.CancelledError()])
    event_session.close = AsyncMock()
    gateway._event_session = event_session

    raw_listener = MagicMock()
    normalized_listener = MagicMock()
    connection_listener = MagicMock()
    gateway.add_listener(raw_listener)
    gateway.add_event_listener(normalized_listener)
    gateway.add_connection_listener(connection_listener)

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(gateway._event_loop())

    raw_listener.assert_called_once_with("*1*1*21##")
    normalized_listener.assert_called_once()
    normalized = normalized_listener.call_args.args[0]
    assert normalized.device_type == "light"
    assert normalized.state == "on"
    assert connection_listener.call_args_list[-1].args == (True,)


def test_event_loop_reconnects_after_connection_error() -> None:
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
    ):
        with pytest.raises(asyncio.CancelledError):
            asyncio.run(gateway._event_loop())

    first.connect.assert_awaited_once()
    first.close.assert_awaited_once()
    second.connect.assert_awaited_once()
    # After CancelledError, the event loop exits and _set_connected(False) is called
    # in the exception handler before the CancelledError propagates.
    assert gateway.connected is False


def test_listener_exceptions_do_not_stop_event_loop() -> None:
    gateway = _gateway()
    event_session = MagicMock()
    event_session.get_next = AsyncMock(side_effect=["*1*1*21##", asyncio.CancelledError()])
    gateway._event_session = event_session

    failing_listener = MagicMock(side_effect=RuntimeError("listener failed"))
    healthy_listener = MagicMock()
    gateway.add_listener(failing_listener)
    gateway.add_listener(healthy_listener)

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(gateway._event_loop())

    failing_listener.assert_called_once()
    healthy_listener.assert_called_once_with("*1*1*21##")


def test_async_send_uses_command_session() -> None:
    gateway = _gateway()
    session = MagicMock()
    session.connect = AsyncMock(return_value={"Success": True})
    session.send = AsyncMock()
    session.close = AsyncMock()

    with patch(
        "custom_components.bticino_myhome.gateway.OWNCommandSession", return_value=session
    ):
        asyncio.run(gateway.async_send("*1*1*21##"))

    session.connect.assert_awaited_once()
    session.send.assert_awaited_once_with(message="*1*1*21##", is_status_request=False)


def test_async_send_wraps_connection_errors() -> None:
    gateway = _gateway()
    session = MagicMock()
    session.connect = AsyncMock(return_value={"Success": True})
    session.send = AsyncMock(side_effect=ConnectionError("send failed"))
    session.close = AsyncMock()

    with patch(
        "custom_components.bticino_myhome.gateway.OWNCommandSession", return_value=session
    ):
        with pytest.raises(BticinoGatewayError, match="send failed"):
            asyncio.run(gateway.async_send("*1*1*21##"))

    session.close.assert_awaited_once()
    assert gateway._command_session is None


def test_async_send_rejects_closed_gateway() -> None:
    gateway = _gateway()
    asyncio.run(gateway.async_close())

    with pytest.raises(BticinoGatewayError, match="gateway_closing"):
        asyncio.run(gateway.async_send("*1*1*21##"))


def test_async_close_is_idempotent() -> None:
    gateway = _gateway()
    asyncio.run(gateway.async_close())
    asyncio.run(gateway.async_close())
    assert gateway.connected is False
