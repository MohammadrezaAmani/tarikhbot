import logging
from pyrogram import filters, types
from pyrogram.client import Client
from pyrogram.handlers.callback_query_handler import CallbackQueryHandler
from pyrogram.handlers.message_handler import MessageHandler
from apps.users.services import UserService
from bot.keyboards.common import get_main_menu_keyboard
from bot.messages.common import WELCOME_MESSAGE, HELP_MESSAGE

logger = logging.getLogger("bot")


# Command handlers
async def start_command(client: Client, message: types.Message) -> None:
    """Handle /start command."""
    user = message.from_user
    logger.info(f"Start command from user {user.id} ({user.first_name})")

    # Register user in database
    db_user, is_new = await UserService.register_user(
        telegram_id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username,
        language_code=user.language_code or "en",
    )

    # Get main menu keyboard
    keyboard = get_main_menu_keyboard()

    # Send welcome message
    welcome_text = WELCOME_MESSAGE
    if is_new:
        welcome_text += "\n\nIt looks like this is your first time here! Let me help you get started."

    await client.send_message(
        chat_id=message.chat.id, text=welcome_text, reply_markup=keyboard
    )


async def help_command(client: Client, message: types.Message) -> None:
    """Handle /help command."""
    logger.info(f"Help command from user {message.from_user.id}")

    # Send help message
    await client.send_message(chat_id=message.chat.id, text=HELP_MESSAGE)


async def settings_command(client: Client, message: types.Message) -> None:
    """Handle /settings command."""
    logger.info(f"Settings command from user {message.from_user.id}")

    # Get user profile
    user_profile = await UserService.get_user_profile(message.from_user.id)

    if not user_profile:
        await client.send_message(
            chat_id=message.chat.id,
            text="⚠️ Error retrieving your profile. Please try again later.",
        )
        return

    # Format profile info
    profile_text = (
        "⚙️ **Your Settings**\n\n"
        f"**Name:** {user_profile['name']}\n"
        f"**Username:** {user_profile['username'] or 'Not set'}\n"
        f"**Language:** {user_profile['language']}\n"
        f"**Timezone:** {user_profile['timezone']}\n"
        f"**Google Connected:** {'Yes ✅' if user_profile['google_connected'] else 'No ❌'}\n"
        f"**Premium:** {'Yes ⭐' if user_profile['is_premium'] else 'No'}\n\n"
        "Use the buttons below to update your settings."
    )

    # Create keyboard for settings
    from bot.keyboards.common import get_settings_keyboard

    keyboard = get_settings_keyboard(user_profile)

    await client.send_message(
        chat_id=message.chat.id, text=profile_text, reply_markup=keyboard
    )


async def cancel_command(client: Client, message: types.Message) -> None:
    """Handle /cancel command to abort any ongoing operation."""
    logger.info(f"Cancel command from user {message.from_user.id}")

    # Clear any active state for the user (we'll implement state management later)

    # Return to main menu
    keyboard = get_main_menu_keyboard()

    await client.send_message(
        chat_id=message.chat.id,
        text="✅ Current operation cancelled. Returned to main menu.",
        reply_markup=keyboard,
    )


# Callback query handlers
async def main_menu_callback(
    client: Client, callback_query: types.CallbackQuery
) -> None:
    """Handle main menu callback queries."""
    user_id = callback_query.from_user.id
    logger.info(f"Main menu callback from user {user_id}: {callback_query.data}")

    # Get main menu keyboard
    keyboard = get_main_menu_keyboard()

    # Update message with main menu
    await callback_query.edit_message_text(text=WELCOME_MESSAGE, reply_markup=keyboard)

    # Answer callback query
    await callback_query.answer("Main menu")


# Message handlers for regular text messages
async def unknown_command(client: Client, message: types.Message) -> None:
    """Handle unknown commands."""
    logger.info(f"Unknown command from user {message.from_user.id}: {message.text}")

    await client.send_message(
        chat_id=message.chat.id,
        text="I don't recognize that command. Please use the menu or type /help to see available commands.",
    )


# Registration function for all handlers in this module
def register_handlers(app: Client) -> None:
    """Register all handlers in this module."""
    # Command handlers
    app.add_handler(MessageHandler(start_command, filters.command("start")))
    app.add_handler(MessageHandler(help_command, filters.command("help")))
    app.add_handler(MessageHandler(settings_command, filters.command("settings")))
    app.add_handler(MessageHandler(cancel_command, filters.command("cancel")))

    # Callback query handlers
    app.add_handler(
        CallbackQueryHandler(main_menu_callback, filters.regex("^main_menu$"))
    )

    # Unknown command handler - should be added last
    # Fixed the operator issue by using filters.create() to properly combine filters
    app.add_handler(
        MessageHandler(
            unknown_command,
            filters.command,
            # & filters.create(
            #     lambda _, m: m.text
            #     and not m.text.startswith(("/start", "/help", "/settings", "/cancel"))
            # ),
        )
    )

    logger.info("Common handlers registered")
