import logging
from datetime import UTC, datetime
from typing import Annotated, Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.portfolio import InvestmentProfile
from app.domain.entities.notification import NotificationEvent
from app.domain.schemas import (
    AuthResponse,
    ChangePasswordRequest,
    LoginRequest,
    MessageResponse,
    NotificationSettingsResponse,
    NotificationSettingsUpdateRequest,
    ProfileResponse,
    QuizProfileResult,
    QuizSubmissionRequest,
    RefreshTokenRequest,
    TokenPairResponse,
    UserCreate,
    UserUpdateRequest,
    UserResponse,
)
from app.config.settings import get_settings
from app.application.use_cases.notification_email_service import NotificationEmailService
from app.infrastructure.database import get_db
from app.infrastructure.external.ses_email_sender import SesEmailSender
from app.infrastructure.external.smtp_email_sender import SmtpEmailSender
from app.infrastructure.repositories import NotificationPreferenceRepository, ProfileRepository, UserRepository
from app.infrastructure.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.interfaces.http.dependencies import get_current_user
from app.interfaces.http.dependencies import get_notification_service

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


PROFILE_RULES = {
    "conservador": {
        "name": "Conservador",
        "risk_level": "low",
        "expected_return": "3-6%",
        "volatility_target": 6.0,
        "description": "Preservación de capital, baja tolerancia al riesgo y horizonte corto.",
        "equity_allocation": 20.0,
        "fixed_income_allocation": 80.0,
    },
    "moderado": {
        "name": "Moderado",
        "risk_level": "medium",
        "expected_return": "6-12%",
        "volatility_target": 12.0,
        "description": "Balance entre crecimiento y estabilidad, tolerancia media al riesgo.",
        "equity_allocation": 50.0,
        "fixed_income_allocation": 50.0,
    },
    "agresivo": {
        "name": "Agresivo",
        "risk_level": "high",
        "expected_return": ">12%",
        "volatility_target": 20.0,
        "description": "Búsqueda de alto crecimiento con alta tolerancia a volatilidad y pérdidas.",
        "equity_allocation": 80.0,
        "fixed_income_allocation": 20.0,
    },
}

VARIABLE_INCOME_ASSETS = [
    {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "allocation_percentage": 25,
        "annual_return_percentage": 30.62,
    },
    {
        "symbol": "MSFT",
        "name": "Microsoft Corp.",
        "allocation_percentage": 15,
        "annual_return_percentage": 1.2,
    },
    {
        "symbol": "GOOGL",
        "name": "Alphabet Inc.",
        "allocation_percentage": 10,
        "annual_return_percentage": 111.86,
    },
]


def _build_email_service() -> NotificationEmailService:
    settings = get_settings()
    email_provider = str(getattr(settings, "email_provider", "smtp")).lower()
    if email_provider == "ses":
        email_sender = SesEmailSender(settings=settings)
    else:
        email_sender = SmtpEmailSender(settings=settings)
    return NotificationEmailService(settings=settings, email_sender=email_sender)


def _send_auth_notification_email_fallback(event_type: str, user_id: int, email: str, metadata: dict[str, Any]) -> None:
    event = NotificationEvent(
        event_id=str(uuid4()),
        event_type=event_type,
        occurred_at=datetime.now(UTC),
        user_id=user_id,
        email=email,
        metadata=metadata,
    )
    email_service = _build_email_service()
    email_service.send_event_email(event)


async def _publish_auth_notification(event_type: str, user_id: int, email: str, metadata: dict[str, Any]) -> None:
    settings = get_settings()
    if str(getattr(settings, "email_provider", "smtp")).lower() == "smtp":
        try:
            _send_auth_notification_email_fallback(
                event_type=event_type,
                user_id=user_id,
                email=email,
                metadata=metadata,
            )
            logger.warning("SMTP direct email sent: event_type=%s user_id=%s", event_type, user_id)
        except Exception:
            logger.exception("Unable to send direct SMTP auth notification email: %s", event_type)
        return

    try:
        notification_service = get_notification_service()
        await notification_service.publish_event(
            event_type=event_type,
            user_id=user_id,
            email=email,
            metadata=metadata,
        )
    except Exception:
        logger.exception("Unable to publish auth notification event: %s", event_type)
        try:
            _send_auth_notification_email_fallback(
                event_type=event_type,
                user_id=user_id,
                email=email,
                metadata=metadata,
            )
            logger.info("Fallback email sent directly: event_type=%s user_id=%s", event_type, user_id)
        except Exception:
            logger.exception("Unable to send fallback auth notification email: %s", event_type)


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register_user(payload: UserCreate, session: Annotated[AsyncSession, Depends(get_db)]):
    if payload.password != payload.confirm_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match")

    existing_user = await UserRepository.get_by_email(session, payload.email)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is already registered")

    user = await UserRepository.create(
        session=session,
        email=payload.email,
        name=payload.name,
        phone=payload.phone,
        location=payload.location,
        password_hash=get_password_hash(payload.password),
    )

    tokens = TokenPairResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )

    await _publish_auth_notification(
        event_type="user_registered",
        user_id=user.id,
        email=user.email,
        metadata={"name": user.name, "location": user.location},
    )

    return AuthResponse(user=UserResponse.model_validate(user), tokens=tokens)


@router.post("/login", response_model=AuthResponse)
async def login_user(payload: LoginRequest, session: Annotated[AsyncSession, Depends(get_db)]):
    user = await UserRepository.get_by_email(session, payload.email)
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    tokens = TokenPairResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )

    return AuthResponse(user=UserResponse.model_validate(user), tokens=tokens)


@router.post("/refresh", response_model=TokenPairResponse)
async def refresh_token(payload: RefreshTokenRequest, session: Annotated[AsyncSession, Depends(get_db)]):
    try:
        decoded = decode_token(payload.refresh_token)
        if decoded.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
        user_id = int(decoded.get("sub"))
    except (JWTError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user = await UserRepository.get_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return TokenPairResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: Annotated[Any, Depends(get_current_user)]):
    return UserResponse.model_validate(current_user)


@router.patch("/me", response_model=UserResponse)
async def update_me(
    payload: UserUpdateRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Any, Depends(get_current_user)],
):
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        return UserResponse.model_validate(current_user)

    new_email = updates.get("email")
    if new_email and new_email != current_user.email:
        existing_user = await UserRepository.get_by_email(session, new_email)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is already registered")

    updated_user = await UserRepository.update(session, current_user.id, **updates)
    if not updated_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return UserResponse.model_validate(updated_user)


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    payload: ChangePasswordRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Any, Depends(get_current_user)],
):
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")

    if payload.current_password == payload.new_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New password must be different")

    await UserRepository.update(
        session,
        current_user.id,
        password_hash=get_password_hash(payload.new_password),
    )

    return MessageResponse(message="Password updated successfully")


@router.get("/active-profile", response_model=ProfileResponse)
async def get_active_profile(
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Any, Depends(get_current_user)],
):
    if not current_user.active_profile_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active profile not found")
    profile = await ProfileRepository.get_by_id(session, current_user.active_profile_id)
    if not profile or profile.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active profile not found")
    return ProfileResponse.model_validate(profile)


def classify_profile(score: int) -> str:
    if 10 <= score <= 15:
        return "conservador"
    if 16 <= score <= 22:
        return "moderado"
    return "agresivo"


@router.post("/quiz-profile", response_model=QuizProfileResult)
async def submit_quiz_profile(
    payload: QuizSubmissionRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Any, Depends(get_current_user)],
):
    if len(payload.answers) != 10:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quiz must include 10 answers")

    question_ids = sorted(answer.question_id for answer in payload.answers)
    expected_ids = list(range(1, 11))
    if question_ids != expected_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Question IDs must be 1 through 10")

    if any(answer.score < 1 or answer.score > 3 for answer in payload.answers):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Each answer score must be between 1 and 3")

    total_score = sum(answer.score for answer in payload.answers)
    profile_key = classify_profile(total_score)
    profile_data = PROFILE_RULES[profile_key]

    await session.execute(
        update(InvestmentProfile)
        .where(InvestmentProfile.user_id == current_user.id)
        .values(is_active=False)
    )
    await session.commit()

    profile = await ProfileRepository.create(
        session=session,
        user_id=current_user.id,
        name=profile_data["name"],
        risk_level=profile_data["risk_level"],
        volatility_target=profile_data["volatility_target"],
        expected_return=profile_data["expected_return"],
        description=profile_data["description"],
        equity_allocation=profile_data["equity_allocation"],
        fixed_income_allocation=profile_data["fixed_income_allocation"],
        score=total_score,
    )

    await UserRepository.update(
        session=session,
        user_id=current_user.id,
        onboarding_completed=True,
        active_profile_id=profile.id,
    )

    await _publish_auth_notification(
        event_type="profile_assigned",
        user_id=current_user.id,
        email=current_user.email,
        metadata={
            "profile_name": profile_data["name"],
            "risk_level": profile_data["risk_level"],
            "score": total_score,
            "profile_id": profile.id,
        },
    )

    return QuizProfileResult(
        score=total_score,
        profile_name=profile_data["name"],
        risk_level=profile_data["risk_level"],
        expected_return=profile_data["expected_return"],
        description=profile_data["description"],
    )


@router.get("/notifications/settings", response_model=NotificationSettingsResponse)
async def get_notification_settings(
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Any, Depends(get_current_user)],
):
    preference = await NotificationPreferenceRepository.get_or_create_default(session, current_user.id)
    return NotificationSettingsResponse.model_validate(preference)


@router.put("/notifications/settings", response_model=NotificationSettingsResponse)
async def update_notification_settings(
    payload: NotificationSettingsUpdateRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Any, Depends(get_current_user)],
):
    if payload.delivery_hour < 0 or payload.delivery_hour > 23:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Delivery hour must be between 0 and 23")

    preference = await NotificationPreferenceRepository.update(
        session,
        current_user.id,
        enabled=payload.enabled,
        frequency=payload.frequency,
        delivery_hour=payload.delivery_hour,
    )
    return NotificationSettingsResponse.model_validate(preference)


@router.post("/notifications/send-now", response_model=MessageResponse)
async def send_notification_now(current_user: Annotated[Any, Depends(get_current_user)]):
    await _publish_auth_notification(
        event_type="variable_income_update",
        user_id=current_user.id,
        email=current_user.email,
        metadata={
            "category": "Renta Variable",
            "segment": "Acciones y ETFs",
            "assets": VARIABLE_INCOME_ASSETS,
        },
    )
    return MessageResponse(message="Notification queued successfully")
