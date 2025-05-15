from typing import Optional, Dict, Any, Union
import asyncio
import logging
from pathlib import Path

from pyrogram import Client, types, errors
from pyrogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup

from config.settings import SETTINGS
from config.logging import configure_logging
from database import init_db, close_db
from config.scheduler import scheduler
from bot.handlers.common import register_handlers as register_handlers_common

# Setup logger
logger = logging.getLogger("bot")


class BotClient:
    """Pyrogram client for the Telegram Bot."""

    def __init__(self):
        """Initialize the bot client."""
        self.app = Client(
            "task_manager_bot",
            api_id=SETTINGS["api_id"],
            api_hash=SETTINGS["api_hash"],
            bot_token=SETTINGS["bot_token"],
            workdir=str(Path(__file__).parent.parent),
            plugins={"root": "bot.handlers"},
        )

        self._is_running = False
        self._media_folder = Path(SETTINGS["media"]["root"])

        # Ensure media folder exists
        self._media_folder.mkdir(exist_ok=True, parents=True)

        # Create logs folder if it doesn't exist
        logs_folder = Path(__file__).parent.parent / "logs"
        logs_folder.mkdir(exist_ok=True)

        # Configure logging
        configure_logging()

    async def start(self):
        """Start the bot client and initialize the database."""
        if self._is_running:
            logger.warning("Bot is already running")
            return

        logger.info("Starting bot client")

        # Initialize database
        await init_db()

        # Start the scheduler
        await scheduler.start()

        # Start the bot
        await self.app.start()
        self._is_running = True

        bot_info = await self.app.get_me()
        logger.info(f"Bot started: @{bot_info.username} ({bot_info.id})")

        # Keep the bot running
        while self._is_running:
            await asyncio.sleep(1)

    async def stop(self):
        """Stop the bot client and close the database."""
        if not self._is_running:
            logger.warning("Bot is not running")
            return

        logger.info("Stopping bot client")

        # Stop the bot
        await self.app.stop()

        # Stop the scheduler
        await scheduler.shutdown()

        # Close the database
        await close_db()

        self._is_running = False
        logger.info("Bot stopped")

    async def restart(self):
        """Restart the bot client."""
        logger.info("Restarting bot client")
        await self.stop()
        await self.start()

    async def send_message(
        self,
        chat_id: Union[int, str],
        text: str,
        parse_mode: str = "md",
        disable_web_page_preview: bool = True,
        disable_notification: bool = False,
        reply_to_message_id: Optional[int] = None,
        schedule_date: Optional[int] = None,
        reply_markup: Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, None] = None,
    ) -> Optional[types.Message]:
        """Send a message with error handling."""
        try:
            return await self.app.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=parse_mode,
                disable_web_page_preview=disable_web_page_preview,
                disable_notification=disable_notification,
                reply_to_message_id=reply_to_message_id,
                schedule_date=schedule_date,
                reply_markup=reply_markup,
            )
        except errors.RPCError as e:
            logger.error(f"Error sending message to {chat_id}: {e}")
            return None

    async def send_document(
        self,
        chat_id: Union[int, str],
        document: Union[str, bytes, Path],
        caption: Optional[str] = None,
        parse_mode: str = "md",
        disable_notification: bool = False,
        reply_to_message_id: Optional[int] = None,
        schedule_date: Optional[int] = None,
        reply_markup: Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, None] = None,
    ) -> Optional[types.Message]:
        """Send a document with error handling."""
        try:
            return await self.app.send_document(
                chat_id=chat_id,
                document=document,
                caption=caption,
                parse_mode=parse_mode,
                disable_notification=disable_notification,
                reply_to_message_id=reply_to_message_id,
                schedule_date=schedule_date,
                reply_markup=reply_markup,
            )
        except errors.RPCError as e:
            logger.error(f"Error sending document to {chat_id}: {e}")
            return None

    async def send_photo(
        self,
        chat_id: Union[int, str],
        photo: Union[str, bytes, Path],
        caption: Optional[str] = None,
        parse_mode: str = "md",
        disable_notification: bool = False,
        reply_to_message_id: Optional[int] = None,
        schedule_date: Optional[int] = None,
        reply_markup: Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, None] = None,
    ) -> Optional[types.Message]:
        """Send a photo with error handling."""
        try:
            return await self.app.send_photo(
                chat_id=chat_id,
                photo=photo,
                caption=caption,
                parse_mode=parse_mode,
                disable_notification=disable_notification,
                reply_to_message_id=reply_to_message_id,
                schedule_date=schedule_date,
                reply_markup=reply_markup,
            )
        except errors.RPCError as e:
            logger.error(f"Error sending photo to {chat_id}: {e}")
            return None

    def get_media_path(self, user_id: int, filename: str) -> Path:
        """Get the path for a media file."""
        user_folder = self._media_folder / str(user_id)
        user_folder.mkdir(exist_ok=True)
        return user_folder / filename

    async def get_file(self, message: types.Message) -> Optional[Dict[str, Any]]:
        """Download a file from a message."""
        try:
            if message.document:
                file_id = message.document.file_id
                file_name = message.document.file_name
                file_type = "document"
                file_size = message.document.file_size
            elif message.photo:
                file_id = message.photo.file_id
                file_name = f"photo_{message.date}.jpg"
                file_type = "photo"
                file_size = message.photo.file_size
            elif message.video:
                file_id = message.video.file_id
                file_name = message.video.file_name or f"video_{message.date}.mp4"
                file_type = "video"
                file_size = message.video.file_size
            elif message.audio:
                file_id = message.audio.file_id
                file_name = message.audio.file_name or f"audio_{message.date}.mp3"
                file_type = "audio"
                file_size = message.audio.file_size
            elif message.voice:
                file_id = message.voice.file_id
                file_name = f"voice_{message.date}.ogg"
                file_type = "voice"
                file_size = message.voice.file_size
            else:
                logger.warning(f"No file found in message {message.id}")
                return None

            # Download file
            file_path = self.get_media_path(message.from_user.id, file_name)
            await self.app.download_media(message, file_name=str(file_path))

            return {
                "file_id": file_id,
                "file_name": file_name,
                "file_type": file_type,
                "file_size": file_size,
                "file_path": str(file_path),
            }
        except Exception as e:
            logger.error(f"Error downloading file: {e}")
            return None

    @property
    def pyrogram_client(self) -> Client:
        """Get the underlying Pyrogram client."""
        return self.app


# Global instance of the bot client
bot = BotClient()

register_handlers_common(bot.app)
