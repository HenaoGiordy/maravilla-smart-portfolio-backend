from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.schemas import (
    PortfolioCreate,
    PortfolioResponse,
    PortfolioUpdate,
)
from app.interfaces.http.dependencies import get_current_user
from app.infrastructure.database import get_db
from app.infrastructure.repositories import PortfolioRepository, ProfileRepository
from app.infrastructure.cache import RedisCache

router = APIRouter(prefix="/portfolios", tags=["portfolios"])


@router.post("", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
async def create_portfolio(
    profile_id: int,
    portfolio: PortfolioCreate,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new portfolio."""
    # Verify profile exists
    profile = await ProfileRepository.get_by_id(session, profile_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Investment profile not found")
    if profile.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Profile does not belong to user")

    # Create portfolio
    new_portfolio = await PortfolioRepository.create(
        session,
        profile_id=profile_id,
        name=portfolio.name,
        description=portfolio.description,
    )
    return new_portfolio


@router.get("/{portfolio_id}", response_model=PortfolioResponse)
async def get_portfolio(
    portfolio_id: int,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get portfolio details."""
    portfolio = await PortfolioRepository.get_by_id(session, portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")
    profile = await ProfileRepository.get_by_id(session, portfolio.profile_id)
    if not profile or profile.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Portfolio does not belong to user")
    return portfolio


@router.get("", response_model=list[PortfolioResponse])
async def list_portfolios(
    profile_id: int,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List all portfolios for a profile."""
    profile = await ProfileRepository.get_by_id(session, profile_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Investment profile not found")
    if profile.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Profile does not belong to user")
    portfolios = await PortfolioRepository.list_by_profile(session, profile_id)
    return portfolios


@router.put("/{portfolio_id}", response_model=PortfolioResponse)
async def update_portfolio(
    portfolio_id: int,
    portfolio_update: PortfolioUpdate,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update portfolio."""
    existing_portfolio = await PortfolioRepository.get_by_id(session, portfolio_id)
    if not existing_portfolio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")
    profile = await ProfileRepository.get_by_id(session, existing_portfolio.profile_id)
    if not profile or profile.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Portfolio does not belong to user")

    portfolio = await PortfolioRepository.update(
        session,
        portfolio_id,
        **portfolio_update.model_dump(exclude_unset=True),
    )
    if not portfolio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")
    
    # Invalidate cache for this portfolio
    await RedisCache.delete(f"portfolio:performance:{portfolio_id}")
    
    return portfolio


@router.delete("/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_portfolio(
    portfolio_id: int,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete portfolio."""
    existing_portfolio = await PortfolioRepository.get_by_id(session, portfolio_id)
    if not existing_portfolio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")
    profile = await ProfileRepository.get_by_id(session, existing_portfolio.profile_id)
    if not profile or profile.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Portfolio does not belong to user")

    success = await PortfolioRepository.delete(session, portfolio_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")
    
    # Invalidate cache for this portfolio
    await RedisCache.delete(f"portfolio:performance:{portfolio_id}")
