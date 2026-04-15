import asyncio
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from app.application.use_cases.notification_email_service import NotificationEmailService
from app.config.settings import get_settings
from app.domain.entities.notification import NotificationEvent
from app.infrastructure.database import AsyncSessionLocal
from app.infrastructure.external.ses_email_sender import SesEmailSender
from app.infrastructure.external.smtp_email_sender import SmtpEmailSender
from app.infrastructure.repositories import NotificationPreferenceRepository

logger = logging.getLogger(__name__)

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


@dataclass
class SchedulingPreference:
    frequency: str
    last_sent_at: datetime | None


def should_send_now(preference: SchedulingPreference, now: datetime) -> bool:
    if preference.last_sent_at is None:
        return True

    last = preference.last_sent_at
    if preference.frequency == "daily":
        return last.date() < now.date()
    if preference.frequency == "weekly":
        return last.isocalendar().week != now.isocalendar().week or last.year != now.year
    if preference.frequency == "monthly":
        return last.month != now.month or last.year != now.year
    return False


def _build_email_service() -> NotificationEmailService:
    settings = get_settings()
    email_provider = str(getattr(settings, "email_provider", "smtp")).lower()
    if email_provider == "ses":
        email_sender = SesEmailSender(settings=settings)
    else:
        email_sender = SmtpEmailSender(settings=settings)
    return NotificationEmailService(settings=settings, email_sender=email_sender)


async def run_once() -> int:
    settings = get_settings()
    if not settings.notifications_enabled:
        logger.info("Notifications disabled; scheduler skipped")
        return 0

    now = datetime.now(UTC)
    delivery_hour = now.hour
    email_service = _build_email_service()

    sent_count = 0
    async with AsyncSessionLocal() as session:
        pairs = await NotificationPreferenceRepository.list_enabled_for_hour(session, delivery_hour)

        for preference, user in pairs:
            if not should_send_now(
                SchedulingPreference(
                    frequency=preference.frequency,
                    last_sent_at=preference.last_sent_at,
                ),
                now,
            ):
                continue

            try:
                event = NotificationEvent(
                    event_id=str(uuid4()),
                    event_type="variable_income_update",
                    occurred_at=now,
                    user_id=user.id,
                    email=user.email,
                    metadata={
                        "category": "Renta Variable",
                        "segment": "Acciones y ETFs",
                        "assets": VARIABLE_INCOME_ASSETS,
                    },
                )
                email_service.send_event_email(event)
                await NotificationPreferenceRepository.mark_sent(session, preference.id, now)
                sent_count += 1
            except Exception:
                logger.exception("Error sending scheduled notification for user_id=%s", user.id)

    if sent_count:
        logger.info("Scheduled notifications sent: %s", sent_count)
    return sent_count


async def run_forever() -> None:
    settings = get_settings()
    interval = max(30, settings.notifications_scheduler_interval_seconds)
    logger.info("Notification scheduler started with interval=%ss", interval)
    while True:
        try:
            await run_once()
        except Exception:
            logger.exception("Unhandled error in notification scheduler cycle")
        await asyncio.sleep(interval)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_forever())


if __name__ == "__main__":
    main()
