from abc import ABC, abstractmethod

from app.domain.entities.market_data import PriceResponse, QuoteResponse, TimeSeriesRequest, TimeSeriesResponse


class MarketDataProviderPort(ABC):
    @abstractmethod
    async def get_price(self, symbol: str) -> PriceResponse:
        raise NotImplementedError

    @abstractmethod
    async def get_quote(self, symbol: str) -> QuoteResponse:
        raise NotImplementedError

    @abstractmethod
    async def get_time_series(self, params: TimeSeriesRequest) -> TimeSeriesResponse:
        raise NotImplementedError
