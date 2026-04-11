from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal

from app.domain.schemas import PortfolioPerformance, HoldingSnapshot
from app.infrastructure.database import get_db
from app.infrastructure.repositories import PortfolioRepository, HoldingRepository
from app.infrastructure.cache import RedisCache
from app.application.use_cases.market_data_service import MarketDataService
from app.interfaces.http.dependencies import get_market_data_service

router = APIRouter(prefix="/performance", tags=["performance"])


@router.get("/{portfolio_id}", response_model=PortfolioPerformance)
async def get_portfolio_performance(
    portfolio_id: int,
    session: AsyncSession = Depends(get_db),
    market_service: MarketDataService = Depends(get_market_data_service),
):
    """
    Calculate portfolio performance:
    - Total value (current market prices)
    - Return percentage
    - Asset distribution
    """
    # Check cache first
    cache_key = f"portfolio:performance:{portfolio_id}"
    cached_data = await RedisCache.get(cache_key)
    if cached_data:
        return PortfolioPerformance(**cached_data)

    # Get portfolio
    portfolio = await PortfolioRepository.get_by_id(session, portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")

    # Get holdings
    holdings = await HoldingRepository.list_by_portfolio(session, portfolio_id)
    
    if not holdings:
        # Empty portfolio
        performance = PortfolioPerformance(
            portfolio_id=portfolio_id,
            total_value=0.0,
            total_invested=0.0,
            total_return=0.0,
            return_percentage=0.0,
            volatility=None,
            distribution={},
        )
        await RedisCache.set(cache_key, performance.model_dump())
        return performance

    # Fetch current prices for each holding
    total_value = 0.0
    total_invested = 0.0
    distribution = {}
    
    for holding in holdings:
        entry_value = float(holding.entry_price) * holding.quantity
        total_invested += entry_value
        
        try:
            # Get current price from Twelve Data
            quote = await market_service.get_quote(holding.symbol)
            current_price = quote.close or quote.price or float(holding.entry_price)
        except Exception:
            # Fallback to entry price if API fails
            current_price = float(holding.entry_price)
        
        current_value = current_price * holding.quantity
        total_value += current_value
        distribution[holding.symbol] = round((current_value / (total_value + 0.001)) * 100, 2)

    total_return = total_value - total_invested
    return_percentage = (total_return / total_invested * 100) if total_invested > 0 else 0.0

    performance = PortfolioPerformance(
        portfolio_id=portfolio_id,
        total_value=round(total_value, 2),
        total_invested=round(total_invested, 2),
        total_return=round(total_return, 2),
        return_percentage=round(return_percentage, 2),
        volatility=None,  # Can be calculated from price history
        distribution=distribution,
    )

    # Cache for 5 minutes
    await RedisCache.set(cache_key, performance.model_dump(), ttl=300)
    
    return performance


@router.get("/{portfolio_id}/holdings", response_model=list[HoldingSnapshot])
async def get_holdings_snapshot(
    portfolio_id: int,
    session: AsyncSession = Depends(get_db),
    market_service: MarketDataService = Depends(get_market_data_service),
):
    """
    Get detailed snapshot of each holding with current prices and returns.
    """
    portfolio = await PortfolioRepository.get_by_id(session, portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")

    holdings = await HoldingRepository.list_by_portfolio(session, portfolio_id)
    
    # Calculate total value first
    total_value = 0.0
    snapshots_data = []
    
    for holding in holdings:
        try:
            quote = await market_service.get_quote(holding.symbol)
            current_price = quote.close or quote.price or float(holding.entry_price)
        except Exception:
            current_price = float(holding.entry_price)
        
        entry_value = float(holding.entry_price) * holding.quantity
        current_value = current_price * holding.quantity
        total_value += current_value
        
        snapshot = {
            "id": holding.id,
            "symbol": holding.symbol,
            "quantity": holding.quantity,
            "entry_price": float(holding.entry_price),
            "current_price": current_price,
            "entry_value": round(entry_value, 2),
            "current_value": round(current_value, 2),
            "return_amount": round(current_value - entry_value, 2),
            "return_percentage": round(((current_value - entry_value) / entry_value * 100) if entry_value > 0 else 0, 2),
            "asset_class": holding.asset_class,
            "percentage_of_portfolio": 0.0,  # Will calculate after total
        }
        snapshots_data.append(snapshot)
    
    # Calculate percentages
    for snapshot in snapshots_data:
        snapshot["percentage_of_portfolio"] = round((snapshot["current_value"] / (total_value + 0.001)) * 100, 2)
    
    return [HoldingSnapshot(**s) for s in snapshots_data]
