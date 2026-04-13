

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

            await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(30)"))
            await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS location VARCHAR(255)"))
            await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS onboarding_completed BOOLEAN NOT NULL DEFAULT FALSE"))
            await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS active_profile_id INTEGER"))
            await conn.execute(text("ALTER TABLE investment_profiles ADD COLUMN IF NOT EXISTS score INTEGER"))

            await conn.execute(
                text(
                    """
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.table_constraints
                            WHERE constraint_name = 'fk_users_active_profile_id'
                            AND table_name = 'users'
                        ) THEN
                            ALTER TABLE users
                            ADD CONSTRAINT fk_users_active_profile_id
                            FOREIGN KEY (active_profile_id)
                            REFERENCES investment_profiles (id);
                        END IF;
                    END $$;
                    """
                )
            )

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
