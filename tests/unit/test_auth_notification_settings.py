from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException

import app.interfaces.http.routes.auth as auth_module
from app.domain.schemas import NotificationSettingsUpdateRequest


@pytest.mark.asyncio
async def test_get_notification_settings_returns_repository_result(monkeypatch: pytest.MonkeyPatch) -> None:
    session = object()
    current_user = SimpleNamespace(id=9)
    preference = SimpleNamespace(enabled=True, frequency="weekly", delivery_hour=14)

    get_or_create_mock = AsyncMock(return_value=preference)
    monkeypatch.setattr(auth_module.NotificationPreferenceRepository, "get_or_create_default", get_or_create_mock)

    response = await auth_module.get_notification_settings(session=session, current_user=current_user)

    assert response.enabled is True
    assert response.frequency == "weekly"
    assert response.delivery_hour == 14
    get_or_create_mock.assert_awaited_once_with(session, 9)


@pytest.mark.asyncio
async def test_update_notification_settings_rejects_invalid_hour() -> None:
    payload = NotificationSettingsUpdateRequest(enabled=True, frequency="daily", delivery_hour=26)
    session = object()
    current_user = SimpleNamespace(id=1)

    with pytest.raises(HTTPException) as exc_info:
        await auth_module.update_notification_settings(payload, session=session, current_user=current_user)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Delivery hour must be between 0 and 23"


@pytest.mark.asyncio
async def test_send_notification_now_queues_event(monkeypatch: pytest.MonkeyPatch) -> None:
    current_user = SimpleNamespace(id=55, email="test@example.com")

    send_now_mock = AsyncMock()
    monkeypatch.setattr(auth_module, "_send_auth_notification_now", send_now_mock)

    response = await auth_module.send_notification_now(current_user=current_user)

    assert response.message == "Notification sent successfully"
    send_now_mock.assert_awaited_once_with(
        event_type="variable_income_update",
        user_id=55,
        email="test@example.com",
        metadata={
            "category": "Renta Variable",
            "segment": "Acciones y ETFs",
            "assets": auth_module.VARIABLE_INCOME_ASSETS,
        },
    )
