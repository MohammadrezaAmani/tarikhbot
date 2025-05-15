#!/usr/bin/env python3
import asyncio
import sys
import argparse
from pathlib import Path

project_root = Path(__file__).parent
sys.path.append(str(project_root))

from config.logging import configure_logging  # noqa
from bot.client import bot  # noqa
from database import init_db, close_db  # noqa

logger = configure_logging()


async def start_bot():
    """Start the bot and keep it running."""
    try:
        logger.info("Starting Task Manager Bot")
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.exception(f"Error starting bot: {e}")
    finally:
        await bot.stop()


async def init_database():
    """Initialize the database."""
    try:
        logger.info("Initializing database")
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.exception(f"Error initializing database: {e}")
    finally:
        await close_db()


def main():
    """Main entry point with command line parsing."""
    parser = argparse.ArgumentParser(description="Task Manager Bot CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    subparsers.add_parser("start", help="Start the bot")

    subparsers.add_parser("init_db", help="Initialize the database")

    args = parser.parse_args()

    if args.command == "start":
        asyncio.run(start_bot())
    elif args.command == "init_db":
        asyncio.run(init_database())
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
