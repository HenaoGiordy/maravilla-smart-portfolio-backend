from abc import ABC, abstractmethod

from app.domain.entities.notification import NotificationEvent


class NotificationPublisherPort(ABC):
    @abstractmethod
    async def publish(self, event: NotificationEvent) -> None:
        raise NotImplementedError
