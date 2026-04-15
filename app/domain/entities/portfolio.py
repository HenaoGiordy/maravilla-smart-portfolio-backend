from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Column, Date, DateTime, Numeric, String, Integer, ForeignKey, Text, Boolean, Index
from sqlalchemy.orm import relationship

from app.infrastructure.database import Base

CASCADING_DELETE_ORPHAN = "all, delete-orphan"


class User(Base):
    """User model."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    phone = Column(String(30), nullable=False)
    location = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    onboarding_completed = Column(Boolean, default=False, nullable=False)
    active_profile_id = Column(Integer, ForeignKey("investment_profiles.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    profiles = relationship(
        "InvestmentProfile",
        back_populates="user",
        cascade=CASCADING_DELETE_ORPHAN,
        foreign_keys="InvestmentProfile.user_id",
    )
    active_profile = relationship("InvestmentProfile", foreign_keys=[active_profile_id], post_update=True)
    notification_preference = relationship(
        "NotificationPreference",
        back_populates="user",
        cascade=CASCADING_DELETE_ORPHAN,
        uselist=False,
    )


class InvestmentProfile(Base):
    """Investment profile model (Bajo/Medio/Alto)."""
    __tablename__ = "investment_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)  # Bajo, Moderado, Agresivo
    risk_level = Column(String(50), nullable=False)  # low, medium, high
    volatility_target = Column(Numeric(5, 2), nullable=False)  # 4-6, 7-10, 12-18
    expected_return = Column(String(100), nullable=True)  # "4-6%", "7-10%", etc.
    score = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    equity_allocation = Column(Numeric(5, 2), nullable=False, default=0)
    fixed_income_allocation = Column(Numeric(5, 2), nullable=False, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="profiles", foreign_keys=[user_id])
    portfolios = relationship("Portfolio", back_populates="profile", cascade=CASCADING_DELETE_ORPHAN)

    __table_args__ = (Index("idx_user_profile", "user_id"),)


class Portfolio(Base):
    """Portfolio model."""
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("investment_profiles.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    total_invested = Column(Numeric(15, 2), default=0, nullable=False)  # Total money invested
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    profile = relationship("InvestmentProfile", back_populates="portfolios")
    holdings = relationship("Holding", back_populates="portfolio", cascade=CASCADING_DELETE_ORPHAN)

    __table_args__ = (Index("idx_profile_portfolio", "profile_id"),)


class Holding(Base):
    """Holding/Asset in portfolio."""
    __tablename__ = "holdings"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    symbol = Column(String(20), nullable=False)  # AAPL, BTC, EUR/USD, etc.
    entry_price = Column(Numeric(15, 4), nullable=False)  # Purchase price per unit
    quantity = Column(Integer, nullable=False)  # Number of units
    purchase_date = Column(Date, nullable=False)  # Date of purchase
    asset_class = Column(String(50), nullable=False)  # stocks, crypto, forex, bonds, etc.
    income_type = Column(String(50), nullable=True)  # dividend, interest, growth, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    portfolio = relationship("Portfolio", back_populates="holdings")

    __table_args__ = (Index("idx_portfolio_holding", "portfolio_id"), Index("idx_symbol_holding", "symbol"),)


class AssetPriceHistory(Base):
    """Historical price data for assets (synced from Twelve Data)."""
    __tablename__ = "asset_price_history"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    date = Column(Date, nullable=False)
    open = Column(Numeric(15, 4), nullable=True)
    high = Column(Numeric(15, 4), nullable=True)
    low = Column(Numeric(15, 4), nullable=True)
    close = Column(Numeric(15, 4), nullable=True)
    volume = Column(Integer, nullable=True)
    interval = Column(String(20), default="1day", nullable=False)  # 1day, 1;hour, etc.
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("idx_symbol_date", "symbol", "date"), Index("idx_symbol_interval", "symbol", "interval"),)


class AssetReference(Base):
    """Reference data for assets (cached from Twelve Data)."""
    __tablename__ = "asset_references"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    exchange = Column(String(50), nullable=True)
    asset_type = Column(String(50), nullable=True)  # stock, crypto, forex, etc.
    currency = Column(String(10), nullable=True)
    last_cached = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class NotificationPreference(Base):
    """User notification settings for variable income updates."""
    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    enabled = Column(Boolean, nullable=False, default=False)
    frequency = Column(String(20), nullable=False, default="daily")
    delivery_hour = Column(Integer, nullable=False, default=8)
    last_sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="notification_preference")
