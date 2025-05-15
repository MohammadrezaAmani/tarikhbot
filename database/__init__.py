from tortoise import Tortoise
from config.settings import SETTINGS

async def init_db():
    """Initialize database connection."""
    await Tortoise.init(
        db_url=SETTINGS["db_url"],
        modules={"models": ["database.models"]}
    )
    # Generate schemas
    await Tortoise.generate_schemas(safe=True)

async def close_db():
    """Close database connection."""
    await Tortoise.close_connections()

__all__ = ["init_db", "close_db"]