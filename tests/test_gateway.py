from __future__ import annotations

import asyncio
from collections.abc import Awaitable
from typing import Any

import pytest

from custom_components.bticino_myhome import gateway as gateway_module
from custom_components.bticino_myhome.gateway import BticinoGateway, BticinoGatewayError


class FakeGateway:
    def __init__(self, data: dict[str, Any]) -> None:
        self.data = data


class FakeSession:
    def __init__(self, *, result: dict[str, Any] | None = None) -> None:
        self.result = result or {"Success": True}
        self.closed = False
        self.send_started = asyncio.Event()
        self.release_send = asyncio.Event()
        self.release_next = asyncio.Event()

    async def connect(self) -> dict[str, Any]:
        return self.result

    async def test_connection(self) -> dict[str, Any]:
        return self.result

    async def send(self, **_: Any) -> None:
        self.send_started.set()
        await self.release_send.wait()

    async def get_next(self) -> str | None:
        await self.release_next.wait()
        return None

    async def close(self) -> None:
        self.closed = True


class SequenceEventFactory:
    def __init__(self, sessions: list[FakeSession]) -> None:
        self.sessions = iter(sessions)

    def __call__(self, **_: Any) -> FakeSession:
        return next(self.sessions)


def install_fakes(
    monkeypatch: pytest.MonkeyPatch,
    *,
    command: FakeSession | None = None,
    event: FakeSession | None = None,
    test: FakeSession | None = None,
) -> tuple[FakeSession, FakeSession, FakeSession]:
    command = command or FakeSession()
    event = event or FakeSession()
    test = test or FakeSession()

    monkeypatch.setattr(gateway_module, "OWNGateway", FakeGateway)
    monkeypatch.setattr(
        gateway_module,
        "OWNCommandSession",
        lambda **_: command,
    )
    monkeypatch.setattr(
        gateway_module,
        "OWNEventSession",
        lambda **_: event,
    )
    monkeypatch.setattr(
        gateway_module,
        "OWNSession",
        lambda **_: test,
    )
    return command, event, test


def run(coro: Awaitable[Any]) -> Any:
    return asyncio.run(coro)


def test_async_test_connection_closes_temporary_session(monkeypatch: pytest.MonkeyPatch) -> None:
    _, _, test = install_fakes(monkeypatch)
    gateway = BticinoGateway("192.0.2.10", 20000, "12345")

    assert run(gateway.async_test_connection()) is True
    assert test.closed is True


def test_async_connect_closes_command_session_when_event_connection_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = FakeSession()
    event = FakeSession(result={"Success": False, "Message": "event unavailable"})
    install_fakes(monkeypatch, command=command, event=event)
    gateway = BticinoGateway("192.0.2.10", 20000, "12345")

    with pytest.raises(BticinoGatewayError, match="event unavailable"):
        run(gateway.async_connect())

    assert command.closed is True
    assert event.closed is True
    assert gateway.connected is False


def test_async_send_timeout_closes_command_session(monkeypatch: pytest.MonkeyPatch) -> None:
    command = FakeSession()
    install_fakes(monkeypatch, command=command)
    monkeypatch.setattr(gateway_module, "_COMMAND_TIMEOUT", 0.01)
    gateway = BticinoGateway("192.0.2.10", 20000, "12345")

    with pytest.raises(BticinoGatewayError):
        run(gateway.async_send("*1*1*2##"))

    assert command.closed is True
    assert gateway.connected is False


def test_async_close_cancels_event_worker_and_closes_sessions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command, event, _ = install_fakes(monkeypatch)
    gateway = BticinoGateway("192.0.2.10", 20000, "12345")

    async def scenario() -> None:
        await gateway.async_connect()
        await asyncio.sleep(0)
        assert gateway.connected is True
        await gateway.async_close()

    run(scenario())

    assert command.closed is True
    assert event.closed is True
    assert gateway.connected is False
    assert gateway._event_task is None


def test_event_worker_reconnects_after_closed_event_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = FakeSession()
    first_event = FakeSession()
    second_event = FakeSession()
    install_fakes(monkeypatch, command=command, event=first_event)
    monkeypatch.setattr(
        gateway_module,
        "OWNEventSession",
        SequenceEventFactory([first_event, second_event]),
    )
    monkeypatch.setattr(gateway_module, "_RECONNECT_INITIAL_DELAY", 0.01)
    gateway = BticinoGateway("192.0.2.10", 20000, "12345")

    async def scenario() -> None:
        await gateway.async_connect()
        first_event.release_next.set()
        await asyncio.sleep(0.03)
        assert first_event.closed is True
        assert gateway.connected is True
        await gateway.async_close()

    run(scenario())
    assert second_event.closed is True
