import logging
from typing import Optional
from pyrogram import filters, types
from pyrogram.client import Client
from pyrogram.handlers.callback_query_handler import CallbackQueryHandler
from pyrogram.handlers.message_handler import MessageHandler

from apps.users.services import UserService
from apps.users.google import get_oauth_url, process_oauth_callback
from bot.keyboards.common import (
    get_main_menu_keyboard,
    get_language_keyboard,
    get_settings_keyboard,
    get_timezone_regions_keyboard,
    get_timezone_cities_keyboard,
    get_google_sync_keyboard,
    get_confirmation_keyboard,
    get_notification_settings_keyboard,
)
from bot.messages.common import ERROR_MESSAGES
from database.models import User

logger = logging.getLogger("bot")

# User state storage for multi-step processes
user_states = {}


# Command and message handlers
async def register_user(
    client: Client, message: types.Message
) -> Optional[tuple[User, None]]:
    """Register a new user or update existing one."""
    user = message.from_user

    # Register user in database
    db_user, is_new = await UserService.register_user(
        telegram_id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username,
        language_code=user.language_code or "en",
    )

    if is_new:
        logger.info(f"New user registered: {user.id} ({user.first_name})")
    else:
        logger.info(f"Existing user found: {user.id} ({user.first_name})")

    return db_user, is_new


# Settings handlers
async def settings_menu_callback(
    client: Client, callback_query: types.CallbackQuery
) -> None:
    """Handle settings menu callback."""
    user_id = callback_query.from_user.id
    logger.info(f"Settings menu callback from user {user_id}")

    # Get user profile
    user_profile = await UserService.get_user_profile(user_id)

    if not user_profile:
        await callback_query.answer(ERROR_MESSAGES["general"], show_alert=True)
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
    keyboard = get_settings_keyboard(user_profile)

    await callback_query.edit_message_text(text=profile_text, reply_markup=keyboard)

    await callback_query.answer()


async def language_settings_callback(
    client: Client, callback_query: types.CallbackQuery
) -> None:
    """Handle language settings callback."""
    user_id = callback_query.from_user.id
    logger.info(f"Language settings callback from user {user_id}")

    await callback_query.edit_message_text(
        text="🌐 **Select your preferred language:**\n\nThis will change the language for all bot messages.",
        reply_markup=get_language_keyboard(),
    )

    await callback_query.answer()


async def timezone_settings_callback(
    client: Client, callback_query: types.CallbackQuery
) -> None:
    """Handle timezone settings callback."""
    user_id = callback_query.from_user.id
    logger.info(f"Timezone settings callback from user {user_id}")

    await callback_query.edit_message_text(
        text="🕒 **Select your timezone region:**\n\nThis helps provide accurate times for reminders and due dates.",
        reply_markup=get_timezone_regions_keyboard(),
    )

    await callback_query.answer()


async def timezone_region_callback(
    client: Client, callback_query: types.CallbackQuery
) -> None:
    """Handle timezone region selection callback."""
    user_id = callback_query.from_user.id
    data = callback_query.data
    region = data.replace("tz_region_", "").split("_page_")[0]

    # Check if page information is included
    page = 0
    if "_page_" in data:
        page = int(data.split("_page_")[1])

    logger.info(f"Timezone region callback from user {user_id}: {region}, page {page}")

    await callback_query.edit_message_text(
        text=f"🕒 **Select a city in {region}:**\n\nChoose the city closest to your location.",
        reply_markup=get_timezone_cities_keyboard(region, page),
    )

    await callback_query.answer()


async def timezone_city_callback(
    client: Client, callback_query: types.CallbackQuery
) -> None:
    """Handle timezone city selection callback."""
    user_id = callback_query.from_user.id
    data = callback_query.data

    # Extract timezone
    timezone = data.replace("tz_", "")
    logger.info(f"Timezone city callback from user {user_id}: {timezone}")

    # Update user timezone
    user = await UserService.set_timezone(user_id, timezone)

    if user:
        # Get updated user profile
        user_profile = await UserService.get_user_profile(user_id)

        await callback_query.edit_message_text(
            text=f"✅ Your timezone has been set to: {timezone}\n\nAll times will now be displayed in your local timezone.",
            reply_markup=get_settings_keyboard(user_profile),
        )
    else:
        await callback_query.edit_message_text(
            text=ERROR_MESSAGES["general"], reply_markup=get_main_menu_keyboard()
        )

    await callback_query.answer()


async def language_selection_callback(
    client: Client, callback_query: types.CallbackQuery
) -> None:
    """Handle language selection callback."""
    user_id = callback_query.from_user.id
    data = callback_query.data

    # Extract language code
    lang_code = data.replace("lang_", "")
    logger.info(f"Language selection callback from user {user_id}: {lang_code}")

    # Update user language
    user = await UserService.set_language(user_id, lang_code)

    if user:
        # Get updated user profile
        user_profile = await UserService.get_user_profile(user_id)

        await callback_query.edit_message_text(
            text=f"✅ Your language has been set to: {lang_code}\n\nAll messages will now be displayed in your preferred language.",
            reply_markup=get_settings_keyboard(user_profile),
        )
    else:
        await callback_query.edit_message_text(
            text=ERROR_MESSAGES["general"], reply_markup=get_main_menu_keyboard()
        )

    await callback_query.answer()


async def google_connect_callback(
    client: Client, callback_query: types.CallbackQuery
) -> None:
    """Handle Google account connection callback."""
    user_id = callback_query.from_user.id
    logger.info(f"Google connect callback from user {user_id}")

    # Generate OAuth URL
    oauth_url = get_oauth_url()

    # Store user state
    user_states[user_id] = {"awaiting_google_auth": True}

    await callback_query.edit_message_text(
        text=(
            "🔗 **Connect Google Account**\n\n"
            "To connect your Google account, click the link below and authorize the application.\n\n"
            "After authorization, you'll receive a code. Copy that code and send it here.\n\n"
            f"[Click here to authorize]({oauth_url})"
        ),
        disable_web_page_preview=False,
    )

    await callback_query.answer()


async def google_auth_code_handler(client: Client, message: types.Message) -> None:
    """Handle Google authorization code from user."""
    user_id = message.from_user.id

    # Check if user is awaiting Google auth
    if user_id not in user_states or not user_states[user_id].get(
        "awaiting_google_auth"
    ):
        return

    auth_code = message.text.strip()
    logger.info(f"Received Google auth code from user {user_id}")

    # Process the auth code
    success = await process_oauth_callback(auth_code, user_id)

    if success:
        await message.reply_text(
            "✅ Your Google account has been successfully connected!\n\n"
            "You can now use Google Calendar and Gmail integration features."
        )

        # Get updated user profile and show settings
        user_profile = await UserService.get_user_profile(user_id)

        await message.reply_text(
            "⚙️ **Your Settings**\n\n"
            f"**Google Connected:** Yes ✅\n"
            f"**Google Email:** {user_profile.get('google_email', 'Unknown')}\n\n"
            "You can manage your Google integration in Settings.",
            reply_markup=get_settings_keyboard(user_profile),
        )
    else:
        await message.reply_text(
            "❌ Failed to connect your Google account. The authorization code may be invalid or expired.\n\n"
            "Please try again by selecting 'Connect Google Account' in the Settings menu."
        )

    # Clear user state
    if user_id in user_states:
        del user_states[user_id]


async def google_disconnect_callback(
    client: Client, callback_query: types.CallbackQuery
) -> None:
    """Handle Google account disconnection confirmation."""
    user_id = callback_query.from_user.id
    logger.info(f"Google disconnect callback from user {user_id}")

    await callback_query.edit_message_text(
        text="⚠️ Are you sure you want to disconnect your Google account?\n\nThis will disable all Google Calendar and Gmail integrations.",
        reply_markup=get_confirmation_keyboard("google_disconnect"),
    )

    await callback_query.answer()


async def google_disconnect_confirm_callback(
    client: Client, callback_query: types.CallbackQuery
) -> None:
    """Handle Google account disconnection confirmation."""
    user_id = callback_query.from_user.id
    logger.info(f"Google disconnect confirmation from user {user_id}")

    # Disconnect Google account
    success = await UserService.google_disconnect(user_id)

    if success:
        # Get updated user profile
        user_profile = await UserService.get_user_profile(user_id)

        await callback_query.edit_message_text(
            text="✅ Your Google account has been disconnected.\n\nGoogle Calendar and Gmail integrations are now disabled.",
            reply_markup=get_settings_keyboard(user_profile),
        )
    else:
        await callback_query.edit_message_text(
            text=ERROR_MESSAGES["general"], reply_markup=get_main_menu_keyboard()
        )

    await callback_query.answer()


async def google_disconnect_cancel_callback(
    client: Client, callback_query: types.CallbackQuery
) -> None:
    """Handle Google account disconnection cancellation."""
    user_id = callback_query.from_user.id
    logger.info(f"Google disconnect cancellation from user {user_id}")

    # Get user profile
    user_profile = await UserService.get_user_profile(user_id)

    await callback_query.edit_message_text(
        text="Operation cancelled. Your Google account remains connected.",
        reply_markup=get_settings_keyboard(user_profile),
    )

    await callback_query.answer()


async def google_sync_settings_callback(
    client: Client, callback_query: types.CallbackQuery
) -> None:
    """Handle Google sync settings callback."""
    user_id = callback_query.from_user.id
    logger.info(f"Google sync settings callback from user {user_id}")

    # Get Google auth for the user
    google_auth = await UserService.get_google_auth(user_id)

    if not google_auth:
        await callback_query.answer(ERROR_MESSAGES["google_auth"], show_alert=True)
        return

    await callback_query.edit_message_text(
        text=(
            "🔄 **Google Sync Settings**\n\n"
            f"Connected Account: {google_auth.get('email', 'Unknown')}\n\n"
            "Toggle which Google services you want to sync with the bot:"
        ),
        reply_markup=get_google_sync_keyboard(google_auth),
    )

    await callback_query.answer()


async def notification_settings_callback(
    client: Client, callback_query: types.CallbackQuery
) -> None:
    """Handle notification settings callback."""
    user_id = callback_query.from_user.id
    logger.info(f"Notification settings callback from user {user_id}")

    # Get user profile
    user_profile = await UserService.get_user_profile(user_id)

    await callback_query.edit_message_text(
        text=(
            "🔔 **Notification Settings**\n\n"
            "Configure when and how you receive notifications from the bot:"
        ),
        reply_markup=get_notification_settings_keyboard(user_profile),
    )

    await callback_query.answer()


# Registration function for all handlers in this module
def register_handlers(app: Client) -> None:
    """Register all handlers in this module."""
    # Callback query handlers
    app.add_handler(
        CallbackQueryHandler(settings_menu_callback, filters.regex("^settings_menu$"))
    )
    app.add_handler(
        CallbackQueryHandler(
            language_settings_callback, filters.regex("^settings_language$")
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            timezone_settings_callback, filters.regex("^settings_timezone$")
        )
    )
    app.add_handler(
        CallbackQueryHandler(timezone_region_callback, filters.regex("^tz_region_"))
    )
    app.add_handler(
        CallbackQueryHandler(
            timezone_city_callback, filters.regex("^tz_[A-Za-z]+/[A-Za-z_]+")
        )
    )
    app.add_handler(
        CallbackQueryHandler(language_selection_callback, filters.regex("^lang_"))
    )

    # Google integration handlers
    app.add_handler(
        CallbackQueryHandler(
            google_connect_callback, filters.regex("^settings_google_connect$")
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            google_disconnect_callback, filters.regex("^settings_google_disconnect$")
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            google_disconnect_confirm_callback,
            filters.regex("^google_disconnect_confirm$"),
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            google_disconnect_cancel_callback,
            filters.regex("^google_disconnect_cancel$"),
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            google_sync_settings_callback, filters.regex("^settings_google_sync$")
        )
    )

    # Message handler for Google auth code
    app.add_handler(
        MessageHandler(
            google_auth_code_handler,
            filters.text & filters.regex("^[a-zA-Z0-9_-]{10,}$"),
        )
    )

    # Notification settings
    app.add_handler(
        CallbackQueryHandler(
            notification_settings_callback, filters.regex("^settings_notifications$")
        )
    )

    logger.info("Auth handlers registered")
