from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class NotificationEvent(BaseModel):
    event_id: str
    event_type: str
    occurred_at: datetime
    user_id: int
    email: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    source: str = "maravilla-smart-portfolio-backend"
    version: str = "1.0"
