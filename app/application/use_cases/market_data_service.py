from app.domain.entities.market_data import PriceResponse, QuoteResponse, TimeSeriesRequest, TimeSeriesResponse
from app.domain.ports.market_data_provider import MarketDataProviderPort


class MarketDataService:
    def __init__(self, market_data_provider: MarketDataProviderPort) -> None:
        self.market_data_provider = market_data_provider

    async def get_price(self, symbol: str) -> PriceResponse:
        return await self.market_data_provider.get_price(symbol)

    async def get_quote(self, symbol: str) -> QuoteResponse:
        return await self.market_data_provider.get_quote(symbol)

    async def get_time_series(self, symbol: str, interval: str, outputsize: int) -> TimeSeriesResponse:
        request = TimeSeriesRequest(symbol=symbol, interval=interval, outputsize=outputsize)
        return await self.market_data_provider.get_time_series(request)
