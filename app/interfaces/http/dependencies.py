from app.application.use_cases.market_data_service import MarketDataService
from app.config.settings import get_settings
from app.infrastructure.external.twelve_data_client import TwelveDataClient


def get_market_data_service() -> MarketDataService:
    settings = get_settings()
    provider = TwelveDataClient(settings=settings)
    return MarketDataService(market_data_provider=provider)
