from typing import Any

from pydantic import BaseModel, Field


class PriceResponse(BaseModel):
    symbol: str
    price: float


class QuoteResponse(BaseModel):
    symbol: str
    name: str | None = None
    exchange: str | None = None
    currency: str | None = None
    timestamp: int | None = None
    datetime: str | None = None
    open: float | None = None
    high: float | None = None
    low: float | None = None
    close: float | None = None
    volume: int | None = None
    change: float | None = None
    percent_change: float | None = None


class TimeSeriesRequest(BaseModel):
    symbol: str
    interval: str = "1day"
    outputsize: int = Field(default=30, ge=1, le=5000)


class TimeSeriesResponse(BaseModel):
    meta: dict[str, Any]
    values: list[dict[str, Any]]


class DailyGainItem(BaseModel):
    symbol: str
    name: str | None = None
    close: float | None = None
    change: float | None = None
    percent_change: float | None = None
    annual_return: float | None = None
