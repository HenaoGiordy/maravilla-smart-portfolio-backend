import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Annotated

from app.application.use_cases.market_data_service import MarketDataService
from app.domain.entities.market_data import DailyGainItem, PriceResponse, QuoteResponse, TimeSeriesResponse
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


@router.get("/daily-gains", response_model=list[DailyGainItem])
async def get_daily_gains(
    symbols: Annotated[list[str], Query(..., min_length=1)],
    service: MarketDataService = Depends(get_market_data_service),
) -> list[DailyGainItem]:
    if len(symbols) != 3:
        raise HTTPException(status_code=400, detail="Exactly 3 symbols are required")

    upper_symbols = [s.upper() for s in symbols]

    quotes, time_series = await asyncio.gather(
        asyncio.gather(*[service.get_quote(s) for s in upper_symbols], return_exceptions=True),
        asyncio.gather(*[service.get_time_series(s, "1day", 252) for s in upper_symbols], return_exceptions=True),
    )

    result = []
    for symbol, quote, ts in zip(upper_symbols, quotes, time_series):
        annual_return = None
        if not isinstance(ts, Exception):
            values = ts.values
            if len(values) >= 2:
                try:
                    latest = float(values[0]["close"])
                    oldest = float(values[-1]["close"])
                    if oldest > 0:
                        annual_return = round((latest - oldest) / oldest * 100, 2)
                except (KeyError, ValueError):
                    pass

        if isinstance(quote, Exception):
            result.append(DailyGainItem(symbol=symbol, annual_return=annual_return))
        else:
            result.append(DailyGainItem(
                symbol=quote.symbol,
                name=quote.name,
                close=quote.close,
                change=quote.change,
                percent_change=quote.percent_change,
                annual_return=annual_return,
            ))

    return result
