import logging
from pyrogram import filters, types
from pyrogram.client import Client
from pyrogram.handlers.callback_query_handler import CallbackQueryHandler
from pyrogram.handlers.message_handler import MessageHandler

from apps.users.services import UserService
from apps.users.google import GoogleAPIClient, get_oauth_url
from apps.tasks.services import TaskService
from bot.messages.common import ERROR_MESSAGES

logger = logging.getLogger("google")

# User state storage for multi-step operations
user_states = {}


async def google_cal_menu_callback(
    client: Client, callback_query: types.CallbackQuery
) -> None:
    """Handle Google Calendar menu callback."""
    user_id = callback_query.from_user.id
    logger.info(f"Google Calendar menu callback from user {user_id}")

    # Check if user has connected Google account
    is_connected = await UserService.is_google_connected(user_id)

    if not is_connected:
        # User hasn't connected Google account
        oauth_url = get_oauth_url()

        await callback_query.edit_message_text(
            text=(
                "📅 **Google Calendar Integration**\n\n"
                "You need to connect your Google account to use this feature.\n\n"
                f"[Click here to connect your Google account]({oauth_url})"
            ),
            reply_markup=types.InlineKeyboardMarkup(
                [
                    [
                        types.InlineKeyboardButton(
                            "◀️ Back to Main Menu", callback_data="main_menu"
                        )
                    ]
                ]
            ),
            disable_web_page_preview=False,
        )
    else:
        # User has connected Google account
        # Initialize Google API client
        google_client = GoogleAPIClient(user_id)

        # Get upcoming events
        try:
            events = await google_client.get_calendar_events(max_results=5)

            if events:
                # Format events
                message_text = "📅 **Your Upcoming Google Calendar Events**\n\n"

                for event in events:
                    title = event.get("summary", "Untitled Event")

                    # Parse start time
                    start = event.get("start", {})
                    if "dateTime" in start:
                        start_time = datetime.fromisoformat(
                            start["dateTime"].replace("Z", "+00:00")
                        )
                        start_str = start_time.strftime("%d %b %Y, %H:%M")
                    else:
                        start_str = start.get("date", "Unknown date")

                    # Add event to message
                    message_text += f"• **{title}** - {start_str}\n"

                # Add keyboard for actions
                keyboard = types.InlineKeyboardMarkup(
                    [
                        [
                            types.InlineKeyboardButton(
                                "🔄 Sync with Tasks", callback_data="google_cal_sync"
                            )
                        ],
                        [
                            types.InlineKeyboardButton(
                                "➕ Create Calendar Event",
                                callback_data="google_cal_create",
                            )
                        ],
                        [
                            types.InlineKeyboardButton(
                                "📋 View All Events",
                                callback_data="google_cal_view_all",
                            )
                        ],
                        [
                            types.InlineKeyboardButton(
                                "◀️ Back to Main Menu", callback_data="main_menu"
                            )
                        ],
                    ]
                )

                await callback_query.edit_message_text(
                    text=message_text, reply_markup=keyboard
                )
            else:
                # No events found
                keyboard = types.InlineKeyboardMarkup(
                    [
                        [
                            types.InlineKeyboardButton(
                                "🔄 Sync with Tasks", callback_data="google_cal_sync"
                            )
                        ],
                        [
                            types.InlineKeyboardButton(
                                "➕ Create Calendar Event",
                                callback_data="google_cal_create",
                            )
                        ],
                        [
                            types.InlineKeyboardButton(
                                "◀️ Back to Main Menu", callback_data="main_menu"
                            )
                        ],
                    ]
                )

                await callback_query.edit_message_text(
                    text=(
                        "📅 **Google Calendar Integration**\n\n"
                        "You don't have any upcoming events in your Google Calendar."
                    ),
                    reply_markup=keyboard,
                )
        except Exception as e:
            logger.exception(f"Error getting Google Calendar events: {e}")

            await callback_query.edit_message_text(
                text=ERROR_MESSAGES["google_auth"],
                reply_markup=types.InlineKeyboardMarkup(
                    [
                        [
                            types.InlineKeyboardButton(
                                "🔄 Reconnect Google Account",
                                callback_data="settings_google_connect",
                            )
                        ],
                        [
                            types.InlineKeyboardButton(
                                "◀️ Back to Main Menu", callback_data="main_menu"
                            )
                        ],
                    ]
                ),
            )

    await callback_query.answer()


async def google_cal_sync_callback(
    client: Client, callback_query: types.CallbackQuery
) -> None:
    """Handle Google Calendar sync callback."""
    user_id = callback_query.from_user.id
    logger.info(f"Google Calendar sync callback from user {user_id}")

    # Initialize Google API client
    GoogleAPIClient(user_id)

    # Get user tasks with due dates
    tasks = await TaskService.get_tasks(
        user_id=user_id, due_date_from=datetime.now(), limit=50
    )

    # Filter tasks to only those with due dates
    tasks_with_due_dates = [task for task in tasks if task.due_date]

    if not tasks_with_due_dates:
        await callback_query.edit_message_text(
            text=(
                "📅 **Google Calendar Sync**\n\n"
                "You don't have any tasks with due dates to sync with Google Calendar."
            ),
            reply_markup=types.InlineKeyboardMarkup(
                [
                    [
                        types.InlineKeyboardButton(
                            "◀️ Back", callback_data="google_cal_menu"
                        )
                    ]
                ]
            ),
        )
        await callback_query.answer()
        return

    # Show confirmation
    await callback_query.edit_message_text(
        text=(
            "📅 **Google Calendar Sync**\n\n"
            f"You have {len(tasks_with_due_dates)} tasks with due dates that can be synced with Google Calendar.\n\n"
            "Do you want to sync these tasks to your calendar?"
        ),
        reply_markup=types.InlineKeyboardMarkup(
            [
                [
                    types.InlineKeyboardButton(
                        "✅ Sync Now", callback_data="google_cal_sync_confirm"
                    ),
                    types.InlineKeyboardButton(
                        "❌ Cancel", callback_data="google_cal_menu"
                    ),
                ]
            ]
        ),
    )

    # Store tasks in user state
    user_states[user_id] = {"tasks_to_sync": tasks_with_due_dates}

    await callback_query.answer()


async def google_cal_sync_confirm_callback(
    client: Client, callback_query: types.CallbackQuery
) -> None:
    """Handle Google Calendar sync confirmation callback."""
    user_id = callback_query.from_user.id
    logger.info(f"Google Calendar sync confirmation callback from user {user_id}")

    # Check if user has tasks to sync
    if user_id not in user_states or "tasks_to_sync" not in user_states[user_id]:
        await callback_query.answer(ERROR_MESSAGES["general"], show_alert=True)
        return

    # Get tasks to sync
    tasks = user_states[user_id]["tasks_to_sync"]

    # Initialize Google API client
    google_client = GoogleAPIClient(user_id)

    # Start syncing
    await callback_query.edit_message_text(
        text="🔄 **Syncing tasks with Google Calendar...**\n\nThis may take a moment."
    )

    # Sync tasks
    success_count = 0
    error_count = 0

    for task in tasks:
        # Check if task already has a Google Calendar event ID
        if task.google_calendar_event_id:
            # Update existing event
            result = await google_client.update_calendar_event(
                event_id=task.google_calendar_event_id,
                summary=task.title,
                start_time=task.due_date,
                end_time=task.due_date + timedelta(hours=1),
                description=task.description,
            )
        else:
            # Create new event
            result = await google_client.create_calendar_event(
                summary=task.title,
                start_time=task.due_date,
                end_time=task.due_date + timedelta(hours=1),
                description=task.description,
            )

            # Update task with Google Calendar event ID
            if result:
                await TaskService.set_google_calendar_id(
                    task_id=task.id, user_id=user_id, calendar_event_id=result.get("id")
                )

        if result:
            success_count += 1
        else:
            error_count += 1

    # Show results
    await callback_query.edit_message_text(
        text=(
            "📅 **Google Calendar Sync Results**\n\n"
            f"✅ Successfully synced: {success_count} tasks\n"
            f"❌ Failed to sync: {error_count} tasks\n\n"
            "You can view these events in your Google Calendar."
        ),
        reply_markup=types.InlineKeyboardMarkup(
            [[types.InlineKeyboardButton("◀️ Back", callback_data="google_cal_menu")]]
        ),
    )

    # Clear user state
    if user_id in user_states:
        del user_states[user_id]

    await callback_query.answer()


async def google_gmail_menu_callback(
    client: Client, callback_query: types.CallbackQuery
) -> None:
    """Handle Gmail menu callback."""
    user_id = callback_query.from_user.id
    logger.info(f"Gmail menu callback from user {user_id}")

    # Check if user has connected Google account
    is_connected = await UserService.is_google_connected(user_id)

    if not is_connected:
        # User hasn't connected Google account
        oauth_url = get_oauth_url()

        await callback_query.edit_message_text(
            text=(
                "📧 **Gmail Integration**\n\n"
                "You need to connect your Google account to use this feature.\n\n"
                f"[Click here to connect your Google account]({oauth_url})"
            ),
            reply_markup=types.InlineKeyboardMarkup(
                [
                    [
                        types.InlineKeyboardButton(
                            "◀️ Back to Main Menu", callback_data="main_menu"
                        )
                    ]
                ]
            ),
            disable_web_page_preview=False,
        )
    else:
        # User has connected Google account
        keyboard = types.InlineKeyboardMarkup(
            [
                [
                    types.InlineKeyboardButton(
                        "📊 Send Monthly Report", callback_data="gmail_send_report"
                    )
                ],
                [
                    types.InlineKeyboardButton(
                        "📋 Send Task Summary", callback_data="gmail_send_tasks"
                    )
                ],
                [
                    types.InlineKeyboardButton(
                        "⚙️ Email Settings", callback_data="gmail_settings"
                    )
                ],
                [
                    types.InlineKeyboardButton(
                        "◀️ Back to Main Menu", callback_data="main_menu"
                    )
                ],
            ]
        )

        await callback_query.edit_message_text(
            text=(
                "📧 **Gmail Integration**\n\n"
                "You can send financial reports and task summaries via Gmail."
            ),
            reply_markup=keyboard,
        )

    await callback_query.answer()


async def gmail_send_report_callback(
    client: Client, callback_query: types.CallbackQuery
) -> None:
    """Handle Gmail send report callback."""
    user_id = callback_query.from_user.id
    logger.info(f"Gmail send report callback from user {user_id}")

    # Set user state for email input
    user_states[user_id] = {"state": "entering_email", "action": "send_report"}

    await callback_query.edit_message_text(
        text=(
            "📧 **Send Financial Report**\n\n"
            "Please enter the email address where you'd like to receive the report:"
        ),
        reply_markup=None,
    )

    await callback_query.answer()


async def gmail_email_handler(client: Client, message: types.Message) -> None:
    """Handle email address input for Gmail operations."""
    user_id = message.from_user.id

    # Check if user is entering an email address
    if user_id in user_states and user_states[user_id].get("state") == "entering_email":
        email = message.text.strip()

        # Basic email validation
        if "@" in email and "." in email:
            # Store email in user state
            user_states[user_id]["email"] = email

            # Check what action to perform
            action = user_states[user_id].get("action")

            if action == "send_report":
                # Initialize Google API client
                google_client = GoogleAPIClient(user_id)

                # Get current month and year
                now = datetime.now()
                month = now.month
                year = now.year

                # Get monthly summary
                from apps.finance.services import FinanceService

                summary = await FinanceService.get_monthly_summary(
                    user_id=user_id, year=year, month=month
                )

                # Format email subject and body
                from bot.messages.finance import format_monthly_summary

                subject = f"Financial Report - {month}/{year}"
                body = f"Here is your financial report for {month}/{year}:\n\n"

                # Add summary to body
                body += (
                    format_monthly_summary(summary)
                    .replace("**", "")
                    .replace("\n\n", "\n")
                )

                # Create HTML version
                html_body = f"<h1>Financial Report - {month}/{year}</h1>"
                html_body += f"<p>Here is your financial report for {month}/{year}:</p>"

                # Add summary to HTML body
                html_body += "<h2>Summary</h2>"
                html_body += f"<p>Income: {summary['income']}<br>"
                html_body += f"Expenses: {summary['expenses']}<br>"
                html_body += f"Balance: {summary['balance']}</p>"

                # Add expense breakdown
                html_body += "<h2>Top Expense Categories</h2><ul>"
                for category in summary.get("expense_by_category", [])[:5]:
                    name = category.get("category_name", "Uncategorized")
                    amount = category.get("amount", 0)
                    percentage = category.get("percentage", 0)
                    html_body += f"<li>{name}: {amount} ({percentage:.1f}%)</li>"
                html_body += "</ul>"

                # Send email
                success = await google_client.send_email(
                    to=email, subject=subject, body=body, html_body=html_body
                )

                if success:
                    await message.reply_text("✅ Financial report sent successfully!")
                else:
                    await message.reply_text(ERROR_MESSAGES["google_auth"])

            elif action == "send_tasks":
                # Initialize Google API client
                google_client = GoogleAPIClient(user_id)

                # Get active tasks
                tasks = await TaskService.get_tasks(
                    user_id=user_id, status="todo", limit=50
                )

                # Format email subject and body
                subject = "Task Summary"
                body = "Here is your current task summary:\n\n"

                # Add tasks to body
                if tasks:
                    for i, task in enumerate(tasks, 1):
                        priority = task.priority
                        due_date = (
                            task.due_date.strftime("%d %b")
                            if task.due_date
                            else "No due date"
                        )
                        body += f"{i}. {task.title} - Priority: {priority}, Due: {due_date}\n"
                else:
                    body += "You don't have any active tasks."

                # Create HTML version
                html_body = "<h1>Task Summary</h1>"
                html_body += "<p>Here is your current task summary:</p>"

                # Add tasks to HTML body
                if tasks:
                    html_body += "<ul>"
                    for task in tasks:
                        priority = task.priority
                        due_date = (
                            task.due_date.strftime("%d %b")
                            if task.due_date
                            else "No due date"
                        )
                        html_body += f"<li><strong>{task.title}</strong> - Priority: {priority}, Due: {due_date}</li>"
                    html_body += "</ul>"
                else:
                    html_body += "<p>You don't have any active tasks.</p>"

                # Send email
                success = await google_client.send_email(
                    to=email, subject=subject, body=body, html_body=html_body
                )

                if success:
                    await message.reply_text("✅ Task summary sent successfully!")
                else:
                    await message.reply_text(ERROR_MESSAGES["google_auth"])

            # Clear user state
            del user_states[user_id]
        else:
            # Invalid email
            await message.reply_text("❌ Please enter a valid email address.")


# Registration function for all Google handlers
def register_handlers(app: Client) -> None:
    """Register all handlers in this module."""
    # Google Calendar handlers
    app.add_handler(
        CallbackQueryHandler(
            google_cal_menu_callback, filters.regex("^google_cal_menu$")
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            google_cal_sync_callback, filters.regex("^google_cal_sync$")
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            google_cal_sync_confirm_callback, filters.regex("^google_cal_sync_confirm$")
        )
    )

    # Gmail handlers
    app.add_handler(
        CallbackQueryHandler(
            google_gmail_menu_callback, filters.regex("^google_gmail_menu$")
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            gmail_send_report_callback, filters.regex("^gmail_send_report$")
        )
    )

    # Email input handler
    app.add_handler(
        MessageHandler(gmail_email_handler, filters.text & filters.regex("@"))
    )

    logger.info("Google handlers registered")
