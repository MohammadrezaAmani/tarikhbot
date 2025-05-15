import logging
from pyrogram import filters, types
from pyrogram.client import Client
from pyrogram.handlers.callback_query_handler import CallbackQueryHandler
from pyrogram.handlers.message_handler import MessageHandler
from pyrogram.errors import MessageNotModified

from apps.tasks.services import TaskService
from apps.shared.enums import TaskStatus
from bot.keyboards.tasks import (
    get_task_list_keyboard,
    get_task_detail_keyboard,
    get_task_filter_keyboard,
    get_task_reminder_keyboard,
    get_task_edit_keyboard,
)
from bot.messages.tasks import (
    format_task_details,
    TASK_CREATION_GUIDE,
    NO_TASKS_MESSAGE,
)
from bot.messages.common import SUCCESS_MESSAGES, ERROR_MESSAGES

logger = logging.getLogger("bot")

# User state storage for multi-step task creation and editing
user_states = {}


# Task menu handlers
async def tasks_menu_callback(
    client: Client, callback_query: types.CallbackQuery
) -> None:
    """Handle tasks menu callback."""
    user_id = callback_query.from_user.id
    logger.info(f"Tasks menu callback from user {user_id}")

    # Get user's tasks (default to showing incomplete tasks)
    tasks = await TaskService.get_tasks(
        user_id=user_id, status=TaskStatus.TODO, limit=10
    )

    if tasks:
        # Show task list
        message_text = "📋 **Your Tasks**\n\nHere are your current tasks:"
        keyboard = get_task_list_keyboard(tasks)
    else:
        # No tasks found
        message_text = (
            "📋 **Your Tasks**\n\n"
            "You don't have any active tasks. Tap the button below to create your first task!"
        )
        keyboard = get_task_list_keyboard([])

    await callback_query.edit_message_text(text=message_text, reply_markup=keyboard)

    await callback_query.answer()


async def task_create_callback(
    client: Client, callback_query: types.CallbackQuery
) -> None:
    """Handle task creation callback."""
    user_id = callback_query.from_user.id
    logger.info(f"Task create callback from user {user_id}")

    # Set user state to task creation
    user_states[user_id] = {"state": "creating_task"}

    await callback_query.edit_message_text(text=TASK_CREATION_GUIDE, reply_markup=None)

    await callback_query.answer()


async def task_message_handler(client: Client, message: types.Message) -> None:
    """Handle task creation from user message."""
    user_id = message.from_user.id

    # Check if user is in task creation state
    if user_id in user_states and user_states[user_id].get("state") == "creating_task":
        # Get task details from message
        task_text = message.text.strip()

        # Try to create task with natural language parsing
        task = await TaskService.parse_natural_language(user_id, task_text)

        if task:
            # Task created successfully
            await message.reply_text(SUCCESS_MESSAGES["task_created"])

            # Show task details
            task_details = format_task_details(task)
            await message.reply_text(
                text=task_details, reply_markup=get_task_detail_keyboard(task)
            )
        else:
            # Failed to create task
            await message.reply_text(ERROR_MESSAGES["input"])

        # Clear user state
        del user_states[user_id]

    # If not in task creation state, check if it's a natural language task
    elif message.text and any(
        keyword in message.text.lower() for keyword in ["remind me", "todo", "task"]
    ):
        # Try to create task with natural language parsing
        task = await TaskService.parse_natural_language(user_id, message.text)

        if task:
            # Task created successfully
            await message.reply_text(SUCCESS_MESSAGES["task_created"])

            # Show task details
            task_details = format_task_details(task)
            await message.reply_text(
                text=task_details, reply_markup=get_task_detail_keyboard(task)
            )


async def task_view_callback(
    client: Client, callback_query: types.CallbackQuery
) -> None:
    """Handle task view callback."""
    user_id = callback_query.from_user.id
    task_id = int(callback_query.data.split("_")[-1])
    logger.info(f"Task view callback from user {user_id}: task_id={task_id}")

    # Get task details
    task = await TaskService.get_task(task_id=task_id, user_id=user_id)

    if task:
        # Show task details
        task_details = format_task_details(task, include_subtasks=True)
        keyboard = get_task_detail_keyboard(task)

        try:
            await callback_query.edit_message_text(
                text=task_details, reply_markup=keyboard
            )
        except MessageNotModified:
            # Message content has not changed
            pass
    else:
        await callback_query.answer(ERROR_MESSAGES["not_found"], show_alert=True)

    await callback_query.answer()


async def task_mark_done_callback(
    client: Client, callback_query: types.CallbackQuery
) -> None:
    """Handle task mark as done callback."""
    user_id = callback_query.from_user.id
    task_id = int(callback_query.data.split("_")[-1])
    logger.info(f"Task mark done callback from user {user_id}: task_id={task_id}")

    # Mark task as done
    task = await TaskService.complete_task(task_id=task_id, user_id=user_id)

    if task:
        # Show updated task details
        task_details = format_task_details(task)
        keyboard = get_task_detail_keyboard(task)

        await callback_query.edit_message_text(text=task_details, reply_markup=keyboard)

        await callback_query.answer("Task marked as done!")
    else:
        await callback_query.answer(ERROR_MESSAGES["not_found"], show_alert=True)


async def task_mark_todo_callback(
    client: Client, callback_query: types.CallbackQuery
) -> None:
    """Handle task mark as to-do callback."""
    user_id = callback_query.from_user.id
    task_id = int(callback_query.data.split("_")[-1])
    logger.info(f"Task mark todo callback from user {user_id}: task_id={task_id}")

    # Update task status
    task = await TaskService.update_task(
        task_id=task_id, user_id=user_id, status=TaskStatus.TODO, completed_at=None
    )

    if task:
        # Show updated task details
        task_details = format_task_details(task)
        keyboard = get_task_detail_keyboard(task)

        await callback_query.edit_message_text(text=task_details, reply_markup=keyboard)

        await callback_query.answer("Task marked as to-do!")
    else:
        await callback_query.answer(ERROR_MESSAGES["not_found"], show_alert=True)


async def task_delete_callback(
    client: Client, callback_query: types.CallbackQuery
) -> None:
    """Handle task delete callback."""
    user_id = callback_query.from_user.id
    task_id = int(callback_query.data.split("_")[-1])
    logger.info(f"Task delete callback from user {user_id}: task_id={task_id}")

    # Show confirmation
    await callback_query.edit_message_text(
        text="⚠️ Are you sure you want to delete this task? This cannot be undone.",
        reply_markup=get_confirmation_keyboard(f"task_delete_{task_id}"),
    )

    await callback_query.answer()


async def task_delete_confirm_callback(
    client: Client, callback_query: types.CallbackQuery
) -> None:
    """Handle task delete confirmation callback."""
    user_id = callback_query.from_user.id
    task_id = int(callback_query.data.split("_")[2])
    logger.info(f"Task delete confirm callback from user {user_id}: task_id={task_id}")

    # Delete task
    success = await TaskService.delete_task(task_id=task_id, user_id=user_id)

    if success:
        # Show success message and return to task list
        await callback_query.edit_message_text(
            text=SUCCESS_MESSAGES["task_deleted"], reply_markup=None
        )

        # Get user's tasks
        tasks = await TaskService.get_tasks(
            user_id=user_id, status=TaskStatus.TODO, limit=10
        )

        # Show task list
        message_text = "📋 **Your Tasks**\n\nHere are your current tasks:"
        keyboard = get_task_list_keyboard(tasks)

        await client.send_message(
            chat_id=user_id, text=message_text, reply_markup=keyboard
        )
    else:
        await callback_query.answer(ERROR_MESSAGES["general"], show_alert=True)

    await callback_query.answer()


async def task_delete_cancel_callback(
    client: Client, callback_query: types.CallbackQuery
) -> None:
    """Handle task delete cancellation callback."""
    user_id = callback_query.from_user.id
    task_id = int(callback_query.data.split("_")[2])
    logger.info(f"Task delete cancel callback from user {user_id}: task_id={task_id}")

    # Return to task view
    task = await TaskService.get_task(task_id=task_id, user_id=user_id)

    if task:
        # Show task details
        task_details = format_task_details(task)
        keyboard = get_task_detail_keyboard(task)

        await callback_query.edit_message_text(text=task_details, reply_markup=keyboard)
    else:
        await callback_query.answer(ERROR_MESSAGES["not_found"], show_alert=True)

    await callback_query.answer("Deletion cancelled")


async def task_edit_callback(
    client: Client, callback_query: types.CallbackQuery
) -> None:
    """Handle task edit callback."""
    user_id = callback_query.from_user.id
    task_id = int(callback_query.data.split("_")[-1])
    logger.info(f"Task edit callback from user {user_id}: task_id={task_id}")

    task = await TaskService.get_task(task_id=task_id, user_id=user_id)

    if task:
        # Show edit options
        await callback_query.edit_message_text(
            text="✏️ **Edit Task**\n\nSelect which aspect of the task you want to edit:",
            reply_markup=get_task_edit_keyboard(task_id),
        )
    else:
        await callback_query.answer(ERROR_MESSAGES["not_found"], show_alert=True)

    await callback_query.answer()


async def task_filter_callback(
    client: Client, callback_query: types.CallbackQuery
) -> None:
    """Handle task filter callback."""
    user_id = callback_query.from_user.id
    logger.info(f"Task filter callback from user {user_id}")

    # Initialize filter state if not exists
    if user_id not in user_states or "task_filters" not in user_states[user_id]:
        user_states[user_id] = {"task_filters": {}}

    # Show filter options
    await callback_query.edit_message_text(
        text="🔍 **Filter Tasks**\n\nUse the options below to filter your tasks:",
        reply_markup=get_task_filter_keyboard(user_states[user_id]["task_filters"]),
    )

    await callback_query.answer()


async def task_filter_apply_callback(
    client: Client, callback_query: types.CallbackQuery
) -> None:
    """Handle task filter apply callback."""
    user_id = callback_query.from_user.id
    logger.info(f"Task filter apply callback from user {user_id}")

    # Get filters from user state
    filters = (
        user_states[user_id].get("task_filters", {}) if user_id in user_states else {}
    )

    # Apply filters to task query
    tasks = await TaskService.get_tasks(
        user_id=user_id,
        status=filters.get("status"),
        priority=filters.get("priority"),
        project_id=filters.get("project_id"),
        due_date_from=filters.get("due_date_from"),
        due_date_to=filters.get("due_date_to"),
        tag_ids=filters.get("tag_ids"),
        limit=10,
    )

    if tasks:
        # Show filtered task list
        message_text = (
            "📋 **Filtered Tasks**\n\nHere are your tasks matching the filters:"
        )
        keyboard = get_task_list_keyboard(tasks)
    else:
        # No tasks found
        message_text = NO_TASKS_MESSAGE
        keyboard = get_task_list_keyboard([])

    await callback_query.edit_message_text(text=message_text, reply_markup=keyboard)

    await callback_query.answer("Filters applied")


async def task_reminder_callback(
    client: Client, callback_query: types.CallbackQuery
) -> None:
    """Handle task reminder setting callback."""
    user_id = callback_query.from_user.id
    task_id = int(callback_query.data.split("_")[-1])
    logger.info(f"Task reminder callback from user {user_id}: task_id={task_id}")

    # Show reminder options
    await callback_query.edit_message_text(
        text="⏰ **Set Reminder**\n\nWhen would you like to be reminded about this task?",
        reply_markup=get_task_reminder_keyboard(task_id),
    )

    await callback_query.answer()


# Registration function for all task handlers
def register_handlers(app: Client) -> None:
    """Register all handlers in this module."""
    # Task menu and list callbacks
    app.add_handler(
        CallbackQueryHandler(tasks_menu_callback, filters.regex("^tasks_menu$"))
    )
    app.add_handler(
        CallbackQueryHandler(task_create_callback, filters.regex("^task_create$"))
    )
    app.add_handler(
        CallbackQueryHandler(task_view_callback, filters.regex("^task_view_[0-9]+$"))
    )

    # Task action callbacks
    app.add_handler(
        CallbackQueryHandler(
            task_mark_done_callback, filters.regex("^task_mark_done_[0-9]+$")
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            task_mark_todo_callback, filters.regex("^task_mark_todo_[0-9]+$")
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            task_delete_callback, filters.regex("^task_delete_[0-9]+$")
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            task_delete_confirm_callback, filters.regex("^task_delete_[0-9]+_confirm$")
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            task_delete_cancel_callback, filters.regex("^task_delete_[0-9]+_cancel$")
        )
    )
    app.add_handler(
        CallbackQueryHandler(task_edit_callback, filters.regex("^task_edit_[0-9]+$"))
    )
    app.add_handler(
        CallbackQueryHandler(
            task_reminder_callback, filters.regex("^task_reminder_[0-9]+$")
        )
    )

    # Task filter callbacks
    app.add_handler(
        CallbackQueryHandler(task_filter_callback, filters.regex("^task_filter$"))
    )
    app.add_handler(
        CallbackQueryHandler(
            task_filter_apply_callback, filters.regex("^task_filter_apply$")
        )
    )

    # Natural language task creation handler
    app.add_handler(
        MessageHandler(task_message_handler, filters.text & ~filters.command)
    )

    logger.info("Task handlers registered")
