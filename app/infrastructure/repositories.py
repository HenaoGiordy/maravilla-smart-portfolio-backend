from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.domain.entities.portfolio import User, InvestmentProfile, Portfolio, Holding


class UserRepository:
    """Repository for User operations."""

    @staticmethod
    async def create(session: AsyncSession, email: str, name: str) -> User:
        user = User(email=email, name=name)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    @staticmethod
    async def get_by_id(session: AsyncSession, user_id: int) -> Optional[User]:
        result = await session.execute(select(User).where(User.id == user_id))
        return result.scalars().first()

    @staticmethod
    async def get_by_email(session: AsyncSession, email: str) -> Optional[User]:
        result = await session.execute(select(User).where(User.email == email))
        return result.scalars().first()


class ProfileRepository:
    """Repository for InvestmentProfile operations."""

    @staticmethod
    async def create(session: AsyncSession, user_id: int, name: str, risk_level: str, volatility_target: float, expected_return: str = None) -> InvestmentProfile:
        profile = InvestmentProfile(
            user_id=user_id,
            name=name,
            risk_level=risk_level,
            volatility_target=volatility_target,
            expected_return=expected_return,
        )
        session.add(profile)
        await session.commit()
        await session.refresh(profile)
        return profile

    @staticmethod
    async def get_by_id(session: AsyncSession, profile_id: int) -> Optional[InvestmentProfile]:
        result = await session.execute(select(InvestmentProfile).where(InvestmentProfile.id == profile_id))
        return result.scalars().first()

    @staticmethod
    async def list_by_user(session: AsyncSession, user_id: int) -> List[InvestmentProfile]:
        result = await session.execute(select(InvestmentProfile).where(InvestmentProfile.user_id == user_id))
        return result.scalars().all()


class PortfolioRepository:
    """Repository for Portfolio operations."""

    @staticmethod
    async def create(session: AsyncSession, profile_id: int, name: str, description: str = None) -> Portfolio:
        portfolio = Portfolio(profile_id=profile_id, name=name, description=description)
        session.add(portfolio)
        await session.commit()
        await session.refresh(portfolio)
        return portfolio

    @staticmethod
    async def get_by_id(session: AsyncSession, portfolio_id: int) -> Optional[Portfolio]:
        result = await session.execute(select(Portfolio).where(Portfolio.id == portfolio_id))
        return result.scalars().first()

    @staticmethod
    async def list_by_profile(session: AsyncSession, profile_id: int) -> List[Portfolio]:
        result = await session.execute(select(Portfolio).where(Portfolio.profile_id == profile_id))
        return result.scalars().all()

    @staticmethod
    async def update(session: AsyncSession, portfolio_id: int, **kwargs) -> Optional[Portfolio]:
        portfolio = await PortfolioRepository.get_by_id(session, portfolio_id)
        if portfolio:
            for key, value in kwargs.items():
                setattr(portfolio, key, value)
            await session.commit()
            await session.refresh(portfolio)
        return portfolio

    @staticmethod
    async def delete(session: AsyncSession, portfolio_id: int) -> bool:
        portfolio = await PortfolioRepository.get_by_id(session, portfolio_id)
        if portfolio:
            await session.delete(portfolio)
            await session.commit()
            return True
        return False


class HoldingRepository:
    """Repository for Holding operations."""

    @staticmethod
    async def create(session: AsyncSession, portfolio_id: int, symbol: str, entry_price: float, quantity: int, purchase_date, asset_class: str, income_type: str = None) -> Holding:
        holding = Holding(
            portfolio_id=portfolio_id,
            symbol=symbol,
            entry_price=entry_price,
            quantity=quantity,
            purchase_date=purchase_date,
            asset_class=asset_class,
            income_type=income_type,
        )
        session.add(holding)
        await session.commit()
        await session.refresh(holding)
        return holding

    @staticmethod
    async def get_by_id(session: AsyncSession, holding_id: int) -> Optional[Holding]:
        result = await session.execute(select(Holding).where(Holding.id == holding_id))
        return result.scalars().first()

    @staticmethod
    async def list_by_portfolio(session: AsyncSession, portfolio_id: int) -> List[Holding]:
        result = await session.execute(select(Holding).where(Holding.portfolio_id == portfolio_id))
        return result.scalars().all()

    @staticmethod
    async def update(session: AsyncSession, holding_id: int, **kwargs) -> Optional[Holding]:
        holding = await HoldingRepository.get_by_id(session, holding_id)
        if holding:
            for key, value in kwargs.items():
                setattr(holding, key, value)
            await session.commit()
            await session.refresh(holding)
        return holding

    @staticmethod
    async def delete(session: AsyncSession, holding_id: int) -> bool:
        holding = await HoldingRepository.get_by_id(session, holding_id)
        if holding:
            await session.delete(holding)
            await session.commit()
            return True
        return False
