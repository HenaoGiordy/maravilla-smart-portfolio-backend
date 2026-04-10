from fastapi import APIRouter, Depends, Query

from app.application.use_cases.market_data_service import MarketDataService
from app.domain.entities.market_data import PriceResponse, QuoteResponse, TimeSeriesResponse
from app.interfaces.http.dependencies import get_market_data_service


router = APIRouter(prefix="/market-data", tags=["market-data"])


@router.get("/price", response_model=PriceResponse)
async def get_price(
    symbol: str = Query(..., min_length=1),
    service: MarketDataService = Depends(get_market_data_service),
) -> PriceResponse:
    return await service.get_price(symbol=symbol)


@router.get("/quote", response_model=QuoteResponse)
async def get_quote(
    symbol: str = Query(..., min_length=1),
    service: MarketDataService = Depends(get_market_data_service),
) -> QuoteResponse:
    return await service.get_quote(symbol=symbol)


@router.get("/time-series", response_model=TimeSeriesResponse)
async def get_time_series(
    symbol: str = Query(..., min_length=1),
    interval: str = Query(default="1day", min_length=2),
    outputsize: int = Query(default=30, ge=1, le=5000),
    service: MarketDataService = Depends(get_market_data_service),
) -> TimeSeriesResponse:
    return await service.get_time_series(symbol=symbol, interval=interval, outputsize=outputsize)
