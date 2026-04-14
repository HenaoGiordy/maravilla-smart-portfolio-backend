from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.schemas import (
    HoldingCreate,
    HoldingResponse,
    HoldingUpdate,
)
from app.interfaces.http.dependencies import get_current_user
from app.infrastructure.database import get_db
from app.infrastructure.repositories import HoldingRepository, PortfolioRepository, ProfileRepository
from app.infrastructure.cache import RedisCache

router = APIRouter(prefix="/holdings", tags=["holdings"])


@router.post("", response_model=HoldingResponse, status_code=status.HTTP_201_CREATED)
async def create_holding(
    portfolio_id: int,
    holding: HoldingCreate,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Add a new asset holding to portfolio."""
    # Verify portfolio exists
    portfolio = await PortfolioRepository.get_by_id(session, portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")
    profile = await ProfileRepository.get_by_id(session, portfolio.profile_id)
    if not profile or profile.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Portfolio does not belong to user")

    # Create holding
    new_holding = await HoldingRepository.create(
        session,
        portfolio_id=portfolio_id,
        symbol=holding.symbol,
        entry_price=holding.entry_price,
        quantity=holding.quantity,
        purchase_date=holding.purchase_date,
        asset_class=holding.asset_class,
        income_type=holding.income_type,
    )
    
    # Invalidate portfolio performance cache
    await RedisCache.delete(f"portfolio:performance:{portfolio_id}")
    
    return new_holding


@router.get("/{holding_id}", response_model=HoldingResponse)
async def get_holding(
    holding_id: int,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get holding details."""
    holding = await HoldingRepository.get_by_id(session, holding_id)
    if not holding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Holding not found")
    portfolio = await PortfolioRepository.get_by_id(session, holding.portfolio_id)
    profile = await ProfileRepository.get_by_id(session, portfolio.profile_id) if portfolio else None
    if not profile or profile.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Holding does not belong to user")
    return holding


@router.get("", response_model=list[HoldingResponse])
async def list_holdings(
    portfolio_id: int,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List all holdings in a portfolio."""
    portfolio = await PortfolioRepository.get_by_id(session, portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")
    profile = await ProfileRepository.get_by_id(session, portfolio.profile_id)
    if not profile or profile.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Portfolio does not belong to user")
    holdings = await HoldingRepository.list_by_portfolio(session, portfolio_id)
    return holdings


@router.put("/{holding_id}", response_model=HoldingResponse)
async def update_holding(
    holding_id: int,
    holding_update: HoldingUpdate,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update holding."""
    holding = await HoldingRepository.get_by_id(session, holding_id)
    if not holding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Holding not found")

    portfolio = await PortfolioRepository.get_by_id(session, holding.portfolio_id)
    profile = await ProfileRepository.get_by_id(session, portfolio.profile_id) if portfolio else None
    if not profile or profile.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Holding does not belong to user")
    
    portfolio_id = holding.portfolio_id
    
    # Update holding
    updated_holding = await HoldingRepository.update(
        session,
        holding_id,
        **holding_update.model_dump(exclude_unset=True),
    )
    
    # Invalidate portfolio performance cache
    await RedisCache.delete(f"portfolio:performance:{portfolio_id}")
    
    return updated_holding


@router.delete("/{holding_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_holding(
    holding_id: int,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete holding."""
    holding = await HoldingRepository.get_by_id(session, holding_id)
    if not holding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Holding not found")

    portfolio = await PortfolioRepository.get_by_id(session, holding.portfolio_id)
    profile = await ProfileRepository.get_by_id(session, portfolio.profile_id) if portfolio else None
    if not profile or profile.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Holding does not belong to user")
    
    portfolio_id = holding.portfolio_id
    success = await HoldingRepository.delete(session, holding_id)
    
    if success:
        # Invalidate portfolio performance cache
        await RedisCache.delete(f"portfolio:performance:{portfolio_id}")
