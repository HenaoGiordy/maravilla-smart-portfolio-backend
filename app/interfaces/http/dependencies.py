from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.market_data_service import MarketDataService
from app.application.use_cases.notification_service import NotificationService
from app.config.settings import get_settings
from app.infrastructure.database import get_db
from app.infrastructure.external.sns_notification_publisher import SnsNotificationPublisher
from app.infrastructure.external.twelve_data_client import TwelveDataClient
from app.infrastructure.repositories import UserRepository
from app.infrastructure.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_market_data_service() -> MarketDataService:
    settings = get_settings()
    provider = TwelveDataClient(settings=settings)
    return MarketDataService(market_data_provider=provider)


def get_notification_service() -> NotificationService:
    settings = get_settings()
    publisher = SnsNotificationPublisher(settings=settings)
    return NotificationService(notification_publisher=publisher)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise credentials_exception
        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = int(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exception

    user = await UserRepository.get_by_id(session, user_id)
    if user is None:
        raise credentials_exception
    return user
