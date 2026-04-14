from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

import app.interfaces.http.routes.auth as auth_module
from app.domain.schemas import ChangePasswordRequest


@pytest.mark.asyncio
async def test_change_password_rejects_invalid_current_password(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = ChangePasswordRequest(current_password="bad-pass", new_password="new-pass")
    current_user = SimpleNamespace(id=7, password_hash="stored-hash")
    session = object()

    monkeypatch.setattr(auth_module, "verify_password", lambda plain, hashed: False)
    update_mock = AsyncMock()
    monkeypatch.setattr(auth_module.UserRepository, "update", update_mock)

    with pytest.raises(HTTPException) as exc_info:
        await auth_module.change_password(payload, session=session, current_user=current_user)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Current password is incorrect"
    update_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_change_password_updates_hash_when_current_password_is_valid(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = ChangePasswordRequest(current_password="old-pass", new_password="new-pass")
    current_user = SimpleNamespace(id=11, password_hash="stored-hash")
    session = object()

    monkeypatch.setattr(auth_module, "verify_password", lambda plain, hashed: True)
    monkeypatch.setattr(auth_module, "get_password_hash", lambda password: f"hashed::{password}")

    update_mock = AsyncMock()
    monkeypatch.setattr(auth_module.UserRepository, "update", update_mock)

    response = await auth_module.change_password(payload, session=session, current_user=current_user)

    assert response.message == "Password updated successfully"
    update_mock.assert_awaited_once_with(
        session,
        current_user.id,
        password_hash="hashed::new-pass",
    )
