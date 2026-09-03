"""Tests for the BTicino MyHome gateway lifecycle."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.bticino_myhome.gateway import (
    BticinoCommandResult,
    BticinoGateway,
    BticinoGatewayCommandRejected,
    BticinoGatewayError,
)


def _gateway() -> BticinoGateway:
    return BticinoGateway("127.0.0.1", 20000, "pwd")


def test_async_test_connection_success_and_close() -> None:
    async def scenario() -> None:
        gateway = _gateway()
        session = MagicMock()
        session.test_connection = AsyncMock(return_value={"Success": True})
        session.close = AsyncMock()
        with patch("custom_components.bticino_myhome.gateway.OWNSession", return_value=session):
            assert await gateway.async_test_connection() is True
        session.test_connection.assert_awaited_once()
        session.close.assert_awaited_once()

    asyncio.run(scenario())


def test_async_connect_starts_worker_and_close_cancels_it() -> None:
    async def scenario() -> None:
        gateway = _gateway()
        command = MagicMock()
        command.connect = AsyncMock(return_value={"Success": True})
        command.close = AsyncMock()
        event = MagicMock()
        event.connect = AsyncMock(return_value={"Success": True})
        event.close = AsyncMock()
        blocker = asyncio.Event()
        created_tasks: list[str] = []

        async def read_raw(_session) -> str:
            await blocker.wait()
            return "*1*1*21##"

        def create_task(coroutine, name: str):
            created_tasks.append(name)
            return asyncio.create_task(coroutine, name=name)

        gateway._read_event_raw = AsyncMock(side_effect=read_raw)
        with (
            patch("custom_components.bticino_myhome.gateway.OWNCommandSession", return_value=command),
            patch("custom_components.bticino_myhome.gateway.OWNEventSession", return_value=event),
        ):
            await gateway.async_connect(create_task)
            await asyncio.sleep(0)
            assert gateway.connected is True
            assert gateway.command_connected is True
            assert gateway.event_connected is True
            assert gateway._event_task is not None
            assert created_tasks == ["bticino_myhome-event-loop"]
            assert gateway._read_event_raw.await_count == 1
            await asyncio.wait_for(gateway.async_close(), timeout=1.0)

        command.close.assert_awaited_once()
        event.close.assert_awaited_once()
        assert gateway._event_task is None
        assert gateway.connected is False

    asyncio.run(scenario())


def test_event_loop_normalizes_and_notifies() -> None:
    async def scenario() -> None:
        gateway = _gateway()
        command = MagicMock()
        command.close = AsyncMock()
        gateway._command_session = command
        gateway._set_command_connected(True)
        event = MagicMock()
        event.close = AsyncMock()
        gateway._event_session = event
        gateway._set_event_connected(True)
        gateway._read_event_raw = AsyncMock(
            side_effect=["*1*1*21##", asyncio.CancelledError()]
        )
        raw_listener = MagicMock()
        normalized_listener = MagicMock()
        gateway.add_listener(raw_listener)
        gateway.add_event_listener(normalized_listener)

        with pytest.raises(asyncio.CancelledError):
            await gateway._event_loop()

        raw_listener.assert_called_once_with("*1*1*21##")
        normalized_event = normalized_listener.call_args.args[0]
        assert normalized_event.who == "1"
        assert normalized_event.where == "21"
        assert normalized_event.state == "on"
        event.close.assert_awaited_once()
        assert gateway.event_connected is False
        assert gateway.connected is False

    asyncio.run(scenario())


def test_async_send_returns_result_and_dispatches_status_response() -> None:
    async def scenario() -> None:
        gateway = _gateway()
        command = MagicMock()
        gateway._command_session = command
        gateway._set_command_connected(True)
        gateway._exchange_command = AsyncMock(
            return_value=BticinoCommandResult(True, ("*1*1*21##",))
        )
        listener = MagicMock()
        gateway.add_event_listener(listener)

        result = await gateway.async_send("*#1*21##", is_status_request=True)

        assert result.acknowledged is True
        assert result.responses == ("*1*1*21##",)
        gateway._exchange_command.assert_awaited_once_with(command, "*#1*21##")
        event = listener.call_args.args[0]
        assert event.who == "1"
        assert event.where == "21"
        assert event.state == "on"

    asyncio.run(scenario())


def test_async_send_reconnects_missing_command_session() -> None:
    async def scenario() -> None:
        gateway = _gateway()
        command = MagicMock()
        command.connect = AsyncMock(return_value={"Success": True})
        command.close = AsyncMock()
        gateway._exchange_command = AsyncMock(return_value=BticinoCommandResult(True))
        with patch(
            "custom_components.bticino_myhome.gateway.OWNCommandSession",
            return_value=command,
        ):
            await gateway.async_send("*1*1*21##")

        command.connect.assert_awaited_once()
        gateway._exchange_command.assert_awaited_once_with(command, "*1*1*21##")
        assert gateway.command_connected is True

    asyncio.run(scenario())


def test_async_send_timeout_closes_session() -> None:
    async def scenario() -> None:
        gateway = _gateway()
        command = MagicMock()
        command.close = AsyncMock()
        gateway._command_session = command
        gateway._set_command_connected(True)
        gateway._exchange_command = AsyncMock(side_effect=TimeoutError("send_timeout"))
        with pytest.raises(BticinoGatewayError, match="send_timeout"):
            await gateway.async_send("*1*1*21##")
        command.close.assert_awaited_once()
        assert gateway._command_session is None
        assert gateway.command_connected is False

    asyncio.run(scenario())


def test_nack_rejects_command_without_dropping_healthy_session() -> None:
    async def scenario() -> None:
        gateway = _gateway()
        command = MagicMock()
        command.close = AsyncMock()
        gateway._command_session = command
        gateway._set_command_connected(True)
        gateway._exchange_command = AsyncMock(return_value=BticinoCommandResult(False))

        with pytest.raises(BticinoGatewayCommandRejected):
            await gateway.async_send("*1*1*21##")

        command.close.assert_not_awaited()
        assert gateway._command_session is command
        assert gateway.command_connected is True

    asyncio.run(scenario())


def test_command_failure_recovers_channel_without_retransmitting_frame() -> None:
    async def scenario() -> None:
        gateway = _gateway()
        failed = MagicMock()
        failed.close = AsyncMock()
        gateway._command_session = failed
        gateway._set_command_connected(True)
        gateway._set_event_connected(True)
        gateway._exchange_command = AsyncMock(side_effect=TimeoutError("send_timeout"))

        recovered = asyncio.Event()
        replacement = MagicMock()

        async def connect() -> dict[str, object]:
            recovered.set()
            return {"Success": True}

        replacement.connect = AsyncMock(side_effect=connect)
        replacement.close = AsyncMock()

        with patch(
            "custom_components.bticino_myhome.gateway.OWNCommandSession",
            return_value=replacement,
        ):
            with pytest.raises(BticinoGatewayError, match="send_timeout"):
                await gateway.async_send("*1*1*21##")
            await asyncio.wait_for(recovered.wait(), timeout=1.0)
            await asyncio.sleep(0)

        gateway._exchange_command.assert_awaited_once_with(failed, "*1*1*21##")
        assert gateway.command_connected is True
        assert gateway.connected is True
        await gateway.async_close()
        replacement.close.assert_awaited_once()

    asyncio.run(scenario())


def test_async_send_serializes_concurrent_commands() -> None:
    async def scenario() -> None:
        gateway = _gateway()
        first_entered = asyncio.Event()
        release_first = asyncio.Event()
        active = 0
        max_active = 0
        calls: list[str] = []
        command = MagicMock()
        gateway._command_session = command
        gateway._set_command_connected(True)

        async def exchange(_session, frame: str) -> BticinoCommandResult:
            nonlocal active, max_active
            active += 1
            max_active = max(max_active, active)
            calls.append(frame)
            if frame == "*1*1*1##":
                first_entered.set()
                await release_first.wait()
            active -= 1
            return BticinoCommandResult(True)

        gateway._exchange_command = AsyncMock(side_effect=exchange)
        first = asyncio.create_task(gateway.async_send("*1*1*1##"))
        await first_entered.wait()
        second = asyncio.create_task(gateway.async_send("*1*0*1##"))
        await asyncio.sleep(0)
        assert calls == ["*1*1*1##"]
        release_first.set()
        await asyncio.gather(first, second)

        assert calls == ["*1*1*1##", "*1*0*1##"]
        assert max_active == 1

    asyncio.run(scenario())


def test_connection_listener_requires_both_channels() -> None:
    gateway = _gateway()
    listener = MagicMock()
    gateway.add_connection_listener(listener)
    listener.assert_called_once_with(False)

    gateway._set_command_connected(True)
    listener.assert_called_once_with(False)

    gateway._set_event_connected(True)
    assert listener.call_args.args == (True,)

    gateway._set_event_connected(False)
    assert listener.call_args.args == (False,)


def test_listener_removers_and_close_are_idempotent() -> None:
    async def scenario() -> None:
        gateway = _gateway()
        raw = MagicMock()
        event = MagicMock()
        connection = MagicMock()
        remove_raw = gateway.add_listener(raw)
        remove_event = gateway.add_event_listener(event)
        remove_connection = gateway.add_connection_listener(connection)
        assert connection.call_args.args == (False,)
        remove_raw()
        remove_event()
        remove_connection()
        assert raw not in gateway._listeners
        assert event not in gateway._event_listeners
        assert connection not in gateway._connection_listeners
        await gateway.async_close()
        await gateway.async_close()

    asyncio.run(scenario())
