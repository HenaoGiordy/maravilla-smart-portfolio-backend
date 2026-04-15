from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from app.workers import notification_schedule_worker as worker


class DummySessionContext:
    def __init__(self, session_object) -> None:
        self._session_object = session_object

    async def __aenter__(self):
        return self._session_object

    async def __aexit__(self, exc_type, exc, tb):
        return False


@pytest.mark.asyncio
async def test_run_once_returns_zero_when_notifications_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = SimpleNamespace(notifications_enabled=False)
    monkeypatch.setattr(worker, "get_settings", lambda: settings)

    sent_count = await worker.run_once()

    assert sent_count == 0


@pytest.mark.asyncio
async def test_run_once_publishes_and_marks_sent(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = SimpleNamespace(
        notifications_enabled=True,
        email_provider="smtp",
    )
    monkeypatch.setattr(worker, "get_settings", lambda: settings)

    fake_session = object()
    monkeypatch.setattr(worker, "AsyncSessionLocal", lambda: DummySessionContext(fake_session))

    preference = SimpleNamespace(id=5, frequency="daily", last_sent_at=None)
    user = SimpleNamespace(id=99, email="investor@example.com")

    list_mock = AsyncMock(return_value=[(preference, user)])
    mark_sent_mock = AsyncMock(return_value=preference)
    monkeypatch.setattr(worker.NotificationPreferenceRepository, "list_enabled_for_hour", list_mock)
    monkeypatch.setattr(worker.NotificationPreferenceRepository, "mark_sent", mark_sent_mock)

    email_service_mock = Mock()
    monkeypatch.setattr(worker, "_build_email_service", lambda: email_service_mock)

    sent_count = await worker.run_once()

    assert sent_count == 1
    list_mock.assert_awaited_once()
    email_service_mock.send_event_email.assert_called_once()
    mark_sent_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_run_once_skips_when_not_due(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = SimpleNamespace(
        notifications_enabled=True,
        email_provider="smtp",
    )
    monkeypatch.setattr(worker, "get_settings", lambda: settings)

    fake_session = object()
    monkeypatch.setattr(worker, "AsyncSessionLocal", lambda: DummySessionContext(fake_session))

    preference = SimpleNamespace(id=5, frequency="daily", last_sent_at=datetime.now(UTC))
    user = SimpleNamespace(id=99, email="investor@example.com")

    list_mock = AsyncMock(return_value=[(preference, user)])
    mark_sent_mock = AsyncMock(return_value=preference)
    monkeypatch.setattr(worker.NotificationPreferenceRepository, "list_enabled_for_hour", list_mock)
    monkeypatch.setattr(worker.NotificationPreferenceRepository, "mark_sent", mark_sent_mock)

    monkeypatch.setattr(worker, "should_send_now", lambda pref, now: False)

    email_service_mock = Mock()
    monkeypatch.setattr(worker, "_build_email_service", lambda: email_service_mock)

    sent_count = await worker.run_once()

    assert sent_count == 0
    email_service_mock.send_event_email.assert_not_called()
    mark_sent_mock.assert_not_awaited()
