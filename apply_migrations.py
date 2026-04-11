

"""Script to apply schema without depending on Alembic CLI."""

import asyncio
import sys
import os
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.config.settings import get_settings
from app.infrastructure.database import Base
from app.domain.entities import portfolio  # noqa: F401

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def apply_migrations():
    """Apply schema using SQLAlchemy metadata."""
    settings = get_settings()

    try:
        engine = create_async_engine(
            str(settings.database_url),
            echo=settings.database_echo,
        )

        async with engine.begin() as conn:
            logger.info("Creating database schema from models...")
            await conn.run_sync(Base.metadata.create_all)

            # Cleanup legacy singular tables created during bootstrap fallback
            await conn.execute(text("DROP TABLE IF EXISTS holding CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS portfolio CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS investment_profile CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS \"user\" CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS asset_reference CASCADE"))

            logger.info("Database schema created successfully")

        await engine.dispose()

    except Exception as e:
        logger.exception("Error applying migrations: %s", e)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(apply_migrations())
