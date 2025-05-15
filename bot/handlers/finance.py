import logging
from datetime import date
from decimal import Decimal
from pyrogram import filters, types
from pyrogram.client import Client
from pyrogram.handlers.callback_query_handler import CallbackQueryHandler
from pyrogram.handlers.message_handler import MessageHandler
from pyrogram.errors import MessageNotModified

from apps.finance.services import FinanceService, CategoryService, BudgetService
from apps.shared.enums import TransactionType
from bot.keyboards.finance import (
    get_finance_menu_keyboard,
    get_transaction_type_keyboard,
    get_transaction_keyboard,
    get_transactions_list_keyboard,
    get_category_selection_keyboard,
    get_report_types_keyboard,
    get_budgets_list_keyboard,
    get_month_selection_keyboard,
)
from bot.messages.finance import (
    format_transaction_details,
    format_monthly_summary,
    TRANSACTION_CREATION_GUIDE,
    NO_TRANSACTIONS_MESSAGE,
)
from bot.messages.common import SUCCESS_MESSAGES, ERROR_MESSAGES, CONFIRMATION_MESSAGES

logger = logging.getLogger("bot")

# User state storage for multi-step finance operations
user_states = {}


# Finance menu handlers
async def finance_menu_callback(
    client: Client, callback_query: types.CallbackQuery
) -> None:
    """Handle finance menu callback."""
    user_id = callback_query.from_user.id
    logger.info(f"Finance menu callback from user {user_id}")

    await callback_query.edit_message_text(
        text=(
            "💰 **Financial Management**\n\n"
            "Track your income and expenses, manage budgets, and view financial reports."
        ),
        reply_markup=get_finance_menu_keyboard(),
    )

    await callback_query.answer()


async def transactions_callback(
    client: Client, callback_query: types.CallbackQuery
) -> None:
    """Handle transactions list callback."""
    user_id = callback_query.from_user.id
    logger.info(f"Transactions callback from user {user_id}")

    # Check if page information is provided
    page = 0
    if "_page_" in callback_query.data:
        page = int(callback_query.data.split("_page_")[1])

    # Get transactions
    transactions = await FinanceService.get_transactions(
        user_id=user_id, limit=10, offset=page * 10
    )

    if transactions:
        # Calculate total pages
        total_count = await FinanceService.get_transaction_count(user_id)
        total_pages = (total_count + 9) // 10  # Ceiling division

        # Show transaction list
        message_text = "💰 **Your Transactions**\n\nHere are your recent transactions:"
        keyboard = get_transactions_list_keyboard(
            transactions=transactions, current_page=page, total_pages=total_pages
        )
    else:
        # No transactions found
        message_text = NO_TRANSACTIONS_MESSAGE
        keyboard = get_transactions_list_keyboard(
            transactions=[], current_page=0, total_pages=1
        )

    await callback_query.edit_message_text(text=message_text, reply_markup=keyboard)

    await callback_query.answer()


async def new_transaction_callback(
    client: Client, callback_query: types.CallbackQuery
) -> None:
    """Handle new transaction callback."""
    user_id = callback_query.from_user.id
    logger.info(f"New transaction callback from user {user_id}")

    await callback_query.edit_message_text(
        text=TRANSACTION_CREATION_GUIDE, reply_markup=get_transaction_type_keyboard()
    )

    await callback_query.answer()


async def transaction_type_callback(
    client: Client, callback_query: types.CallbackQuery
) -> None:
    """Handle transaction type selection callback."""
    user_id = callback_query.from_user.id
    data = callback_query.data

    # Extract transaction type
    transaction_type = data.split("_")[-1]
    logger.info(f"Transaction type callback from user {user_id}: {transaction_type}")

    # Initialize transaction creation state
    user_states[user_id] = {
        "state": "creating_transaction",
        "transaction_type": transaction_type,
    }

    # Get categories for this transaction type
    categories = await CategoryService.get_categories(
        user_id=user_id, transaction_type=TransactionType(transaction_type)
    )

    if categories:
        # Show category selection
        await callback_query.edit_message_text(
            text=f"📂 **Select Category**\n\nPlease select a category for your {TransactionType.get_display_name(TransactionType(transaction_type))}:",
            reply_markup=get_category_selection_keyboard(
                categories=categories,
                transaction_type=TransactionType(transaction_type),
                callback_prefix="finance_category",
            ),
        )
    else:
        # No categories found, ask for amount directly
        await callback_query.edit_message_text(
            text=(
                f"💰 **Enter Amount**\n\n"
                f"Please enter the amount for your {TransactionType.get_display_name(TransactionType(transaction_type))}.\n\n"
                f"Example: 42.50"
            ),
            reply_markup=None,
        )

        # Update state
        user_states[user_id]["state"] = "entering_amount"

    await callback_query.answer()


async def category_selection_callback(
    client: Client, callback_query: types.CallbackQuery
) -> None:
    """Handle category selection callback."""
    user_id = callback_query.from_user.id
    data = callback_query.data

    # Extract category ID
    category_id = data.split("_")[-1]
    logger.info(f"Category selection callback from user {user_id}: {category_id}")

    # Update user state
    if user_id in user_states:
        if category_id == "none":
            user_states[user_id]["category_id"] = None
        else:
            user_states[user_id]["category_id"] = int(category_id)

        # Move to amount entry
        await callback_query.edit_message_text(
            text=(
                "💰 **Enter Amount**\n\n"
                "Please enter the amount for this transaction.\n\n"
                "Example: 42.50"
            ),
            reply_markup=None,
        )

        user_states[user_id]["state"] = "entering_amount"
    else:
        # User state not found
        await callback_query.answer(ERROR_MESSAGES["general"], show_alert=True)

    await callback_query.answer()


async def transaction_amount_handler(client: Client, message: types.Message) -> None:
    """Handle transaction amount from user."""
    user_id = message.from_user.id

    # Check if user is entering a transaction amount
    if (
        user_id in user_states
        and user_states[user_id].get("state") == "entering_amount"
    ):
        # Try to parse amount
        try:
            amount = Decimal(message.text.strip())

            # Update user state
            user_states[user_id]["amount"] = amount
            user_states[user_id]["state"] = "entering_description"

            # Ask for description
            await message.reply_text(
                "📝 **Enter Description** (optional)\n\n"
                "Please enter a description for this transaction, or tap Skip."
            )

            # Add skip button
            await client.send_message(
                chat_id=user_id,
                text="Skip description?",
                reply_markup=types.InlineKeyboardMarkup(
                    [
                        [
                            types.InlineKeyboardButton(
                                "Skip", callback_data="finance_skip_description"
                            )
                        ]
                    ]
                ),
            )
        except ValueError:
            # Invalid amount
            await message.reply_text("❌ Please enter a valid amount (e.g., 42.50).")

    # Check if user is entering a transaction description
    elif (
        user_id in user_states
        and user_states[user_id].get("state") == "entering_description"
    ):
        # Update user state
        user_states[user_id]["description"] = message.text.strip()

        # Create the transaction
        transaction = await FinanceService.create_transaction(
            user_id=user_id,
            amount=user_states[user_id]["amount"],
            transaction_type=TransactionType(user_states[user_id]["transaction_type"]),
            date=date.today(),
            description=user_states[user_id]["description"],
            category_id=user_states[user_id].get("category_id"),
        )

        if transaction:
            # Show success message
            await message.reply_text(SUCCESS_MESSAGES["transaction_created"])

            # Show transaction details
            transaction_details = format_transaction_details(transaction)
            await message.reply_text(
                text=transaction_details,
                reply_markup=get_transaction_keyboard(transaction),
            )
        else:
            # Failed to create transaction
            await message.reply_text(ERROR_MESSAGES["general"])

        # Clear user state
        del user_states[user_id]


async def skip_description_callback(
    client: Client, callback_query: types.CallbackQuery
) -> None:
    """Handle skip description callback."""
    user_id = callback_query.from_user.id
    logger.info(f"Skip description callback from user {user_id}")

    # Check if user is in the right state
    if (
        user_id in user_states
        and user_states[user_id].get("state") == "entering_description"
    ):
        # Create the transaction without description
        transaction = await FinanceService.create_transaction(
            user_id=user_id,
            amount=user_states[user_id]["amount"],
            transaction_type=TransactionType(user_states[user_id]["transaction_type"]),
            date=date.today(),
            category_id=user_states[user_id].get("category_id"),
        )

        if transaction:
            # Show success message
            await callback_query.edit_message_text(
                SUCCESS_MESSAGES["transaction_created"]
            )

            # Show transaction details
            transaction_details = format_transaction_details(transaction)
            await client.send_message(
                chat_id=user_id,
                text=transaction_details,
                reply_markup=get_transaction_keyboard(transaction),
            )
        else:
            # Failed to create transaction
            await callback_query.edit_message_text(ERROR_MESSAGES["general"])

        # Clear user state
        del user_states[user_id]
    else:
        # User not in right state
        await callback_query.answer(ERROR_MESSAGES["general"], show_alert=True)

    await callback_query.answer()


async def view_transaction_callback(
    client: Client, callback_query: types.CallbackQuery
) -> None:
    """Handle view transaction callback."""
    user_id = callback_query.from_user.id
    transaction_id = int(callback_query.data.split("_")[-1])
    logger.info(
        f"View transaction callback from user {user_id}: transaction_id={transaction_id}"
    )

    # Get transaction details
    transaction = await FinanceService.get_transaction(
        transaction_id=transaction_id, user_id=user_id
    )

    if transaction:
        # Show transaction details
        transaction_details = format_transaction_details(transaction)
        keyboard = get_transaction_keyboard(transaction)

        try:
            await callback_query.edit_message_text(
                text=transaction_details, reply_markup=keyboard
            )
        except MessageNotModified:
            # Message content has not changed
            pass
    else:
        await callback_query.answer(ERROR_MESSAGES["not_found"], show_alert=True)

    await callback_query.answer()


async def delete_transaction_callback(
    client: Client, callback_query: types.CallbackQuery
) -> None:
    """Handle delete transaction callback."""
    user_id = callback_query.from_user.id
    transaction_id = int(callback_query.data.split("_")[-1])
    logger.info(
        f"Delete transaction callback from user {user_id}: transaction_id={transaction_id}"
    )

    # Show confirmation
    await callback_query.edit_message_text(
        text=CONFIRMATION_MESSAGES["delete_transaction"],
        reply_markup=types.InlineKeyboardMarkup(
            [
                [
                    types.InlineKeyboardButton(
                        "✅ Yes",
                        callback_data=f"finance_delete_confirm_{transaction_id}",
                    ),
                    types.InlineKeyboardButton(
                        "❌ No", callback_data=f"finance_delete_cancel_{transaction_id}"
                    ),
                ]
            ]
        ),
    )

    await callback_query.answer()


async def delete_transaction_confirm_callback(
    client: Client, callback_query: types.CallbackQuery
) -> None:
    """Handle delete transaction confirmation callback."""
    user_id = callback_query.from_user.id
    transaction_id = int(callback_query.data.split("_")[-1])
    logger.info(
        f"Delete transaction confirm callback from user {user_id}: transaction_id={transaction_id}"
    )

    # Delete transaction
    success = await FinanceService.delete_transaction(
        transaction_id=transaction_id, user_id=user_id
    )

    if success:
        # Show success message and return to transaction list
        await callback_query.edit_message_text(
            text=SUCCESS_MESSAGES["transaction_deleted"],
            reply_markup=types.InlineKeyboardMarkup(
                [
                    [
                        types.InlineKeyboardButton(
                            "◀️ Back to Transactions",
                            callback_data="finance_transactions",
                        )
                    ]
                ]
            ),
        )
    else:
        await callback_query.answer(ERROR_MESSAGES["general"], show_alert=True)

    await callback_query.answer()


async def budgets_callback(client: Client, callback_query: types.CallbackQuery) -> None:
    """Handle budgets list callback."""
    user_id = callback_query.from_user.id
    logger.info(f"Budgets callback from user {user_id}")

    # Get budgets
    budgets = await BudgetService.get_budgets(user_id=user_id, active_only=True)

    if budgets:
        # Show budget list
        message_text = "💼 **Your Budgets**\n\nHere are your active budgets:"
        keyboard = get_budgets_list_keyboard(
            budgets=budgets, current_page=0, total_pages=1
        )
    else:
        # No budgets found
        message_text = (
            "💼 **Your Budgets**\n\n"
            "You don't have any active budgets. Tap the button below to create your first budget!"
        )
        keyboard = get_budgets_list_keyboard(budgets=[], current_page=0, total_pages=1)

    await callback_query.edit_message_text(text=message_text, reply_markup=keyboard)

    await callback_query.answer()


async def reports_callback(client: Client, callback_query: types.CallbackQuery) -> None:
    """Handle financial reports callback."""
    user_id = callback_query.from_user.id
    logger.info(f"Reports callback from user {user_id}")

    await callback_query.edit_message_text(
        text="📊 **Financial Reports**\n\nSelect the type of report you want to view:",
        reply_markup=get_report_types_keyboard(),
    )

    await callback_query.answer()


async def monthly_report_callback(
    client: Client, callback_query: types.CallbackQuery
) -> None:
    """Handle monthly report callback."""
    user_id = callback_query.from_user.id
    logger.info(f"Monthly report callback from user {user_id}")

    # Show month selection
    today = date.today()

    await callback_query.edit_message_text(
        text="📅 **Select Month**\n\nPlease select the month for your financial summary:",
        reply_markup=get_month_selection_keyboard(
            current_year=today.year, current_month=today.month
        ),
    )

    await callback_query.answer()


async def month_selection_callback(
    client: Client, callback_query: types.CallbackQuery
) -> None:
    """Handle month selection callback."""
    user_id = callback_query.from_user.id
    data = callback_query.data

    # Extract year and month
    parts = data.split("_")
    if len(parts) >= 3:
        year = int(parts[-2])
        month = int(parts[-1])
        logger.info(f"Month selection callback from user {user_id}: {year}-{month}")

        # Get monthly summary
        summary = await FinanceService.get_monthly_summary(
            user_id=user_id, year=year, month=month
        )

        # Add year and month to summary
        summary["year"] = year
        summary["month"] = month

        # Format summary
        summary_text = format_monthly_summary(summary)

        # Create keyboard with back button
        keyboard = types.InlineKeyboardMarkup(
            [
                [
                    types.InlineKeyboardButton(
                        "📊 View Chart", callback_data=f"finance_chart_{year}_{month}"
                    )
                ],
                [
                    types.InlineKeyboardButton(
                        "📄 Export as PDF",
                        callback_data=f"finance_export_{year}_{month}",
                    )
                ],
                [types.InlineKeyboardButton("◀️ Back", callback_data="finance_reports")],
            ]
        )

        await callback_query.edit_message_text(text=summary_text, reply_markup=keyboard)
    else:
        await callback_query.answer(ERROR_MESSAGES["input"], show_alert=True)

    await callback_query.answer()


# Registration function for all finance handlers
def register_handlers(app: Client) -> None:
    """Register all handlers in this module."""
    # Finance menu callbacks
    app.add_handler(
        CallbackQueryHandler(finance_menu_callback, filters.regex("^finance_menu$"))
    )
    app.add_handler(
        CallbackQueryHandler(
            transactions_callback, filters.regex("^finance_transactions")
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            new_transaction_callback, filters.regex("^finance_new_transaction$")
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            transaction_type_callback, filters.regex("^finance_transaction_type_")
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            category_selection_callback, filters.regex("^finance_category_")
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            skip_description_callback, filters.regex("^finance_skip_description$")
        )
    )

    # Transaction view and actions
    app.add_handler(
        CallbackQueryHandler(
            view_transaction_callback,
            filters.regex("^finance_view_transaction_[0-9]+$"),
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            delete_transaction_callback,
            filters.regex("^finance_delete_transaction_[0-9]+$"),
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            delete_transaction_confirm_callback,
            filters.regex("^finance_delete_confirm_[0-9]+$"),
        )
    )

    # Budget callbacks
    app.add_handler(
        CallbackQueryHandler(budgets_callback, filters.regex("^finance_budgets"))
    )

    # Report callbacks
    app.add_handler(
        CallbackQueryHandler(reports_callback, filters.regex("^finance_reports$"))
    )
    app.add_handler(
        CallbackQueryHandler(
            monthly_report_callback, filters.regex("^finance_report_monthly$")
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            month_selection_callback, filters.regex("^finance_month_[0-9]+_[0-9]+$")
        )
    )

    # Message handler for transaction amount and description input
    app.add_handler(
        MessageHandler(transaction_amount_handler, filters.text & ~filters.command)
    )

    logger.info("Finance handlers registered")
