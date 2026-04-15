import pytest
from unittest.mock import AsyncMock, MagicMock
from app.domain.entities.market_data import PriceResponse, QuoteResponse, TimeSeriesRequest, TimeSeriesResponse

from app.application.use_cases.market_data_service import MarketDataService


@pytest.fixture
def mock_provider():
    provider = MagicMock()
    provider.get_price = AsyncMock()
    provider.get_quote = AsyncMock()
    provider.get_time_series = AsyncMock()
    return provider


@pytest.fixture
def service(mock_provider):
    return MarketDataService(market_data_provider=mock_provider)


class TestMarketDataServiceInit:
    def test_stores_provider(self, mock_provider):
        service = MarketDataService(market_data_provider=mock_provider)
        assert service.market_data_provider is mock_provider


class TestGetPrice:
    @pytest.mark.asyncio
    async def test_returns_provider_response(self, service, mock_provider):
        expected = PriceResponse(symbol="AAPL", price=150.0)
        mock_provider.get_price.return_value = expected

        result = await service.get_price("AAPL")

        assert result == expected

    @pytest.mark.asyncio
    async def test_calls_provider_with_symbol(self, service, mock_provider):
        mock_provider.get_price.return_value = PriceResponse(symbol="AAPL", price=150.0)

        await service.get_price("AAPL")

        mock_provider.get_price.assert_called_once_with("AAPL")

    @pytest.mark.asyncio
    async def test_propagates_provider_exception(self, service, mock_provider):
        mock_provider.get_price.side_effect = Exception("Provider error")

        with pytest.raises(Exception, match="Provider error"):
            await service.get_price("AAPL")


class TestGetQuote:
    @pytest.mark.asyncio
    async def test_returns_provider_response(self, service, mock_provider):
        expected = QuoteResponse(symbol="TSLA", bid=200.0, ask=200.5)
        mock_provider.get_quote.return_value = expected

        result = await service.get_quote("TSLA")

        assert result == expected

    @pytest.mark.asyncio
    async def test_calls_provider_with_symbol(self, service, mock_provider):
        mock_provider.get_quote.return_value = QuoteResponse(symbol="TSLA", bid=200.0, ask=200.5)

        await service.get_quote("TSLA")

        mock_provider.get_quote.assert_called_once_with("TSLA")

    @pytest.mark.asyncio
    async def test_propagates_provider_exception(self, service, mock_provider):
        mock_provider.get_quote.side_effect = ValueError("Invalid symbol")

        with pytest.raises(ValueError, match="Invalid symbol"):
            await service.get_quote("INVALID")


class TestGetTimeSeries:
    @pytest.mark.asyncio
    async def test_returns_provider_response(self, service, mock_provider):
        
        expected = TimeSeriesResponse(
         meta={
            "symbol": "MSFT",
            "interval": "1min"
          },
          values=[]
         )

        mock_provider.get_time_series.return_value = expected

        result = await service.get_time_series("MSFT", "1min", 10)

        assert result == expected

    @pytest.mark.asyncio
    async def test_builds_correct_request(self, service, mock_provider):
        mock_provider.get_time_series.return_value = TimeSeriesResponse(  
          meta={
          "symbol": "MSFT",
          "interval": "1min"
           },
          values=[]
        )   


        await service.get_time_series("MSFT", "1min", 10)

        call_args = mock_provider.get_time_series.call_args
        request: TimeSeriesRequest = call_args[0][0]

        assert request.symbol == "MSFT"
        assert request.interval == "1min"
        assert request.outputsize == 10

    @pytest.mark.asyncio
    async def test_calls_provider_once(self, service, mock_provider):
        mock_provider.get_time_series.return_value = TimeSeriesResponse(
          meta={
          "symbol": "MSFT",
          "interval": "1min"
           },
          values=[]
        )

        await service.get_time_series("MSFT", "5min", 50)

        mock_provider.get_time_series.assert_called_once()

    @pytest.mark.asyncio
    async def test_propagates_provider_exception(self, service, mock_provider):
        mock_provider.get_time_series.side_effect = RuntimeError("Timeout")

        with pytest.raises(RuntimeError, match="Timeout"):
            await service.get_time_series("MSFT", "1min", 10)