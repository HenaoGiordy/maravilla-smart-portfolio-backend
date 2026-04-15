import logging

from app.config.settings import get_settings
from app.infrastructure.external.sqs_notification_consumer import SqsNotificationConsumer


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = get_settings()
    consumer = SqsNotificationConsumer(settings=settings)
    consumer.run_forever()


if __name__ == "__main__":
    main()
