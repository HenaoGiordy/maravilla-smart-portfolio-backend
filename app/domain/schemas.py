from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel


# ============ User Models ============
class UserCreate(BaseModel):
    email: str
    name: str


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Investment Profile Models ============
class ProfileCreate(BaseModel):
    name: str
    risk_level: str  # low, medium, high
    volatility_target: float
    expected_return: Optional[str] = None
    description: Optional[str] = None


class ProfileResponse(BaseModel):
    id: int
    user_id: int
    name: str
    risk_level: str
    volatility_target: float
    expected_return: Optional[str] = None
    description: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Portfolio Models ============
class PortfolioCreate(BaseModel):
    name: str
    description: Optional[str] = None


class PortfolioUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class PortfolioResponse(BaseModel):
    id: int
    profile_id: int
    name: str
    description: Optional[str] = None
    total_invested: Decimal
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ Holding Models ============
class HoldingCreate(BaseModel):
    symbol: str
    entry_price: float
    quantity: int
    purchase_date: date
    asset_class: str  # stocks, crypto, forex, bonds
    income_type: Optional[str] = None  # dividend, interest, growth


class HoldingUpdate(BaseModel):
    entry_price: Optional[float] = None
    quantity: Optional[int] = None
    purchase_date: Optional[date] = None
    income_type: Optional[str] = None


class HoldingResponse(BaseModel):
    id: int
    portfolio_id: int
    symbol: str
    entry_price: float
    quantity: int
    purchase_date: date
    asset_class: str
    income_type: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ Performance Models ============
class PortfolioPerformance(BaseModel):
    portfolio_id: int
    total_value: float
    total_invested: float
    total_return: float  # total_value - total_invested
    return_percentage: float  # (total_return / total_invested) * 100
    volatility: Optional[float] = None  # calculated from holdings
    distribution: dict  # symbol -> percentage distribution


class HoldingSnapshot(BaseModel):
    id: int
    symbol: str
    quantity: int
    entry_price: float
    current_price: float
    entry_value: float  # entry_price * quantity
    current_value: float  # current_price * quantity
    return_amount: float
    return_percentage: float
    asset_class: str
    percentage_of_portfolio: float
