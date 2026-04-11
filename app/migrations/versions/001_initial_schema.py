"""Initial schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create User table
    op.create_table(
        'user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email', name='uq_user_email')
    )
    op.create_index(op.f('ix_user_id'), 'user', ['id'], unique=False)

    # Create InvestmentProfile table
    op.create_table(
        'investment_profile',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('risk_level', sa.String(length=50), nullable=False),
        sa.Column('volatility_target', sa.Float(), nullable=True),
        sa.Column('expected_return', sa.Float(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_investment_profile_user_id'), 'investment_profile', ['user_id'], unique=False)

    # Create Portfolio table
    op.create_table(
        'portfolio',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('profile_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('total_invested', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['profile_id'], ['investment_profile.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_portfolio_profile_id'), 'portfolio', ['profile_id'], unique=False)

    # Create Holding table
    op.create_table(
        'holding',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('portfolio_id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('entry_price', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('purchase_date', sa.Date(), nullable=False),
        sa.Column('asset_class', sa.String(length=50), nullable=True),
        sa.Column('income_type', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['portfolio_id'], ['portfolio.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_holding_portfolio_id'), 'holding', ['portfolio_id'], unique=False)
    op.create_index(op.f('ix_holding_symbol'), 'holding', ['symbol'], unique=False)

    # Create AssetReference table
    op.create_table(
        'asset_reference',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('exchange', sa.String(length=20), nullable=True),
        sa.Column('asset_type', sa.String(length=50), nullable=True),
        sa.Column('currency', sa.String(length=10), nullable=True),
        sa.Column('last_cached', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('symbol', name='uq_asset_reference_symbol')
    )
    op.create_index(op.f('ix_asset_reference_symbol'), 'asset_reference', ['symbol'], unique=True)

    # Create AssetPriceHistory table
    op.create_table(
        'asset_price_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('open_price', sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column('high_price', sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column('low_price', sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column('close_price', sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column('volume', sa.Integer(), nullable=True),
        sa.Column('interval', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_asset_price_history_symbol'), 'asset_price_history', ['symbol'], unique=False)
    op.create_index(op.f('ix_asset_price_history_date'), 'asset_price_history', ['date'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_asset_price_history_date'), table_name='asset_price_history')
    op.drop_index(op.f('ix_asset_price_history_symbol'), table_name='asset_price_history')
    op.drop_table('asset_price_history')

    op.drop_index(op.f('ix_asset_reference_symbol'), table_name='asset_reference')
    op.drop_table('asset_reference')

    op.drop_index(op.f('ix_holding_symbol'), table_name='holding')
    op.drop_index(op.f('ix_holding_portfolio_id'), table_name='holding')
    op.drop_table('holding')

    op.drop_index(op.f('ix_portfolio_profile_id'), table_name='portfolio')
    op.drop_table('portfolio')

    op.drop_index(op.f('ix_investment_profile_user_id'), table_name='investment_profile')
    op.drop_table('investment_profile')

    op.drop_index(op.f('ix_user_id'), table_name='user')
    op.drop_table('user')
