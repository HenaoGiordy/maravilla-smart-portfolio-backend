from typing import Any

import httpx
from fastapi import HTTPException

from app.config.settings import Settings
from app.domain.entities.market_data import PriceResponse, QuoteResponse, TimeSeriesRequest, TimeSeriesResponse
from app.domain.ports.market_data_provider import MarketDataProviderPort
from app.infrastructure.cache import RedisCache


class TwelveDataClient(MarketDataProviderPort):
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        request_params = {
            **params,
            "apikey": self._settings.twelve_data_api_key,
        }

        try:
            async with httpx.AsyncClient(timeout=self._settings.twelve_data_timeout_seconds) as client:
                response = await client.get(f"{self._settings.twelve_data_base_url}{path}", params=request_params)
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPStatusError as error:
            raise HTTPException(status_code=error.response.status_code, detail="Error calling Twelve Data") from error
        except httpx.RequestError as error:
            raise HTTPException(status_code=503, detail="Twelve Data unavailable") from error

        if payload.get("status") == "error":
            raise HTTPException(status_code=400, detail=payload.get("message", "Twelve Data error"))

        return payload

    async def get_price(self, symbol: str) -> PriceResponse:
        # Check cache
        cache_key = f"asset:price:{symbol}"
        cached = await RedisCache.get(cache_key)
        if cached:
            return PriceResponse(**cached)
        
        payload = await self._get("/price", {"symbol": symbol})
        response = PriceResponse(symbol=symbol, price=float(payload["price"]))
        
        # Cache for 1 hour
        await RedisCache.set(cache_key, response.model_dump())
        
        return response

    async def get_quote(self, symbol: str) -> QuoteResponse:
        # Check cache
        cache_key = f"asset:quote:{symbol}"
        cached = await RedisCache.get(cache_key)
        if cached:
            return QuoteResponse(**cached)
        
        payload = await self._get("/quote", {"symbol": symbol})
        response = QuoteResponse(
            symbol=payload.get("symbol", symbol),
            name=payload.get("name"),
            exchange=payload.get("exchange"),
            currency=payload.get("currency"),
            timestamp=int(payload["timestamp"]) if payload.get("timestamp") else None,
            datetime=payload.get("datetime"),
            open=float(payload["open"]) if payload.get("open") else None,
            high=float(payload["high"]) if payload.get("high") else None,
            low=float(payload["low"]) if payload.get("low") else None,
            close=float(payload["close"]) if payload.get("close") else None,
            volume=int(payload["volume"]) if payload.get("volume") else None,
            change=float(payload["change"]) if payload.get("change") else None,
            percent_change=float(payload["percent_change"]) if payload.get("percent_change") else None,
        )
        
        # Cache for 1 hour
        await RedisCache.set(cache_key, response.model_dump())
        
        return response

    async def get_time_series(self, params: TimeSeriesRequest) -> TimeSeriesResponse:
        # Check cache
        cache_key = f"asset:timeseries:{params.symbol}:{params.interval}"
        cached = await RedisCache.get(cache_key)
        if cached:
            return TimeSeriesResponse(**cached)
        
        payload = await self._get(
            "/time_series",
            {
                "symbol": params.symbol,
                "interval": params.interval,
                "outputsize": params.outputsize,
            },
        )
        response = TimeSeriesResponse(
            meta=payload.get("meta", {}),
            values=payload.get("values", []),
        )
        
        # Cache for 1 hour
        await RedisCache.set(cache_key, response.model_dump())
        
        return response
