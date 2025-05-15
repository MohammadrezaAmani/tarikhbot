from typing import Dict, List, Optional
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import date

from apps.shared.enums import TransactionType
from database.models import Transaction, Category, Budget

def get_finance_menu_keyboard() -> InlineKeyboardMarkup:
    """Create the finance menu keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("💰 Transactions", callback_data="finance_transactions"),
            InlineKeyboardButton("📊 Reports", callback_data="finance_reports")
        ],
        [
            InlineKeyboardButton("💼 Budgets", callback_data="finance_budgets"),
            InlineKeyboardButton("🔄 Recurring", callback_data="finance_recurring")
        ],
        [
            InlineKeyboardButton("➕ New Transaction", callback_data="finance_new_transaction")
        ],
        [
            InlineKeyboardButton("◀️ Back to Main Menu", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_transaction_type_keyboard(callback_prefix: str = "finance_transaction_type") -> InlineKeyboardMarkup:
    """Create a keyboard for selecting transaction type."""
    keyboard = [
        [
            InlineKeyboardButton(
                f"💰 Income", 
                callback_data=f"{callback_prefix}_{TransactionType.INCOME.value}"
            )
        ],
        [
            InlineKeyboardButton(
                f"💸 Expense", 
                callback_data=f"{callback_prefix}_{TransactionType.EXPENSE.value}"
            )
        ],
        [
            InlineKeyboardButton(
                f"🔄 Transfer", 
                callback_data=f"{callback_prefix}_{TransactionType.TRANSFER.value}"
            )
        ],
        [
            InlineKeyboardButton("◀️ Back", callback_data="finance_menu")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_transaction_keyboard(transaction: Transaction) -> InlineKeyboardMarkup:
    """Create a keyboard for transaction details."""
    keyboard = [
        [
            InlineKeyboardButton("✏️ Edit", callback_data=f"finance_edit_transaction_{transaction.id}"),
            InlineKeyboardButton("🗑️ Delete", callback_data=f"finance_delete_transaction_{transaction.id}")
        ],
        [
            InlineKeyboardButton("🔄 Create Similar", callback_data=f"finance_copy_transaction_{transaction.id}")
        ],
        [
            InlineKeyboardButton("◀️ Back to Transactions", callback_data="finance_transactions")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_transactions_list_keyboard(
    transactions: List[Transaction],
    current_page: int = 0,
    total_pages: int = 1,
    back_callback: str = "finance_menu"
) -> InlineKeyboardMarkup:
    """Create a keyboard for a list of transactions."""
    keyboard = []
    
    # Add transaction buttons
    for transaction in transactions:
        # Create type indicator emoji
        type_emoji = TransactionType.get_emoji(transaction.type)
        
        # Format amount with currency
        amount_str = f"{transaction.amount} {transaction.currency}"
        
        # Format date
        date_str = transaction.date.strftime("%d %b")
        
        # Create button text
        button_text = f"{type_emoji} {date_str} | {amount_str}"
        if transaction.category:
            button_text += f" | {transaction.category.name}"
        
        # Create button
        keyboard.append([
            InlineKeyboardButton(button_text, callback_data=f"finance_view_transaction_{transaction.id}")
        ])
    
    # Add action buttons
    keyboard.append([
        InlineKeyboardButton("➕ New Transaction", callback_data="finance_new_transaction"),
        InlineKeyboardButton("🔍 Filter", callback_data="finance_filter_transactions")
    ])
    
    # Add pagination controls
    pagination_row = []
    
    if current_page > 0:
        pagination_row.append(
            InlineKeyboardButton("◀️ Previous", callback_data=f"finance_transactions_page_{current_page-1}")
        )
    
    if current_page < total_pages - 1:
        pagination_row.append(
            InlineKeyboardButton("Next ▶️", callback_data=f"finance_transactions_page_{current_page+1}")
        )
    
    if pagination_row:
        keyboard.append(pagination_row)
    
    # Add back button
    keyboard.append([
        InlineKeyboardButton("◀️ Back to Menu", callback_data=back_callback)
    ])
    
    return InlineKeyboardMarkup(keyboard)

def get_category_selection_keyboard(
    categories: List[Category],
    transaction_type: TransactionType,
    callback_prefix: str,
    current_page: int = 0,
    items_per_page: int = 6
) -> InlineKeyboardMarkup:
    """Create a keyboard for selecting a category."""
    keyboard = []
    
    # Calculate pagination
    total_pages = (len(categories) + items_per_page - 1) // items_per_page
    start_idx = current_page * items_per_page
    end_idx = min(start_idx + items_per_page, len(categories))
    current_categories = categories[start_idx:end_idx]
    
    # Add category buttons
    for i in range(0, len(current_categories), 2):
        row = []
        for j in range(2):
            if i + j < len(current_categories):
                category = current_categories[i + j]
                icon = category.icon or "📂"
                name = category.name
                row.append(
                    InlineKeyboardButton(
                        f"{icon} {name}", 
                        callback_data=f"{callback_prefix}_{category.id}"
                    )
                )
        keyboard.append(row)
    
    # Add "No Category" option
    keyboard.append([
        InlineKeyboardButton("📋 No Category", callback_data=f"{callback_prefix}_none")
    ])
    
    # Add "Create New Category" option
    keyboard.append([
        InlineKeyboardButton("➕ New Category", callback_data=f"finance_new_category_{transaction_type.value}")
    ])
    
    # Add pagination controls if needed
    pagination_row = []
    
    if current_page > 0:
        pagination_row.append(
            InlineKeyboardButton("◀️ Previous", callback_data=f"{callback_prefix}_page_{current_page-1}")
        )
    
    if current_page < total_pages - 1:
        pagination_row.append(
            InlineKeyboardButton("Next ▶️", callback_data=f"{callback_prefix}_page_{current_page+1}")
        )
    
    if pagination_row:
        keyboard.append(pagination_row)
    
    # Back button
    keyboard.append([
        InlineKeyboardButton("◀️ Back", callback_data="finance_new_transaction")
    ])
    
    return InlineKeyboardMarkup(keyboard)

def get_transaction_filter_keyboard(
    current_filters: Dict = None,
    callback_prefix: str = "finance_filter"
) -> InlineKeyboardMarkup:
    """Create a keyboard for transaction filtering options."""
    if current_filters is None:
        current_filters = {}
    
    # Get current filter values with defaults
    transaction_type = current_filters.get("type")
    category_id = current_filters.get("category_id")
    date_from = current_filters.get("date_from")
    date_to = current_filters.get("date_to")
    
    keyboard = []
    
    # Transaction type filter
    type_text = f"Type: {TransactionType.get_display_name(transaction_type)}" if transaction_type else "Type: Any"
    keyboard.append([
        InlineKeyboardButton(type_text, callback_data=f"{callback_prefix}_type")
    ])
    
    # Category filter
    category_text = "Category: Selected" if category_id else "Category: Any"
    keyboard.append([
        InlineKeyboardButton(category_text, callback_data=f"{callback_prefix}_category")
    ])
    
    # Date range filter
    date_text = "Date: Custom Range" if date_from or date_to else "Date: All Time"
    keyboard.append([
        InlineKeyboardButton(date_text, callback_data=f"{callback_prefix}_date")
    ])
    
    # Amount range filter
    keyboard.append([
        InlineKeyboardButton("💲 Amount Range", callback_data=f"{callback_prefix}_amount")
    ])
    
    # Apply and reset buttons
    keyboard.append([
        InlineKeyboardButton("✅ Apply Filters", callback_data=f"{callback_prefix}_apply"),
        InlineKeyboardButton("🔄 Reset", callback_data=f"{callback_prefix}_reset")
    ])
    
    # Back button
    keyboard.append([
        InlineKeyboardButton("◀️ Back", callback_data="finance_transactions")
    ])
    
    return InlineKeyboardMarkup(keyboard)

def get_report_types_keyboard() -> InlineKeyboardMarkup:
    """Create a keyboard for selecting financial report types."""
    keyboard = [
        [
            InlineKeyboardButton("📊 Monthly Summary", callback_data="finance_report_monthly")
        ],
        [
            InlineKeyboardButton("🍰 Expense Categories", callback_data="finance_report_categories")
        ],
        [
            InlineKeyboardButton("📈 Income vs Expenses", callback_data="finance_report_comparison")
        ],
        [
            InlineKeyboardButton("📉 Spending Trends", callback_data="finance_report_trends")
        ],
        [
            InlineKeyboardButton("💰 Budget Status", callback_data="finance_report_budgets")
        ],
        [
            InlineKeyboardButton("📄 Export Report", callback_data="finance_report_export")
        ],
        [
            InlineKeyboardButton("◀️ Back", callback_data="finance_menu")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_budgets_list_keyboard(
    budgets: List[Budget],
    current_page: int = 0,
    total_pages: int = 1
) -> InlineKeyboardMarkup:
    """Create a keyboard for a list of budgets."""
    keyboard = []
    
    # Add budget buttons
    for budget in budgets:
        # Format amount with currency
        amount_str = f"{budget.amount} {budget.currency}"
        
        # Format dates
        date_range = f"{budget.start_date.strftime('%d %b')} - {budget.end_date.strftime('%d %b')}"
        
        # Create button text
        button_text = f"💼 {budget.name} | {amount_str} | {date_range}"
        
        # Create button
        keyboard.append([
            InlineKeyboardButton(button_text, callback_data=f"finance_view_budget_{budget.id}")
        ])
    
    # Add action buttons
    keyboard.append([
        InlineKeyboardButton("➕ New Budget", callback_data="finance_new_budget")
    ])
    
    # Add pagination controls
    pagination_row = []
    
    if current_page > 0:
        pagination_row.append(
            InlineKeyboardButton("◀️ Previous", callback_data=f"finance_budgets_page_{current_page-1}")
        )
    
    if current_page < total_pages - 1:
        pagination_row.append(
            InlineKeyboardButton("Next ▶️", callback_data=f"finance_budgets_page_{current_page+1}")
        )
    
    if pagination_row:
        keyboard.append(pagination_row)
    
    # Add back button
    keyboard.append([
        InlineKeyboardButton("◀️ Back to Menu", callback_data="finance_menu")
    ])
    
    return InlineKeyboardMarkup(keyboard)

def get_budget_detail_keyboard(budget: Budget) -> InlineKeyboardMarkup:
    """Create a keyboard for budget details."""
    keyboard = [
        [
            InlineKeyboardButton("✏️ Edit", callback_data=f"finance_edit_budget_{budget.id}"),
            InlineKeyboardButton("🗑️ Delete", callback_data=f"finance_delete_budget_{budget.id}")
        ],
        [
            InlineKeyboardButton("📊 Budget Report", callback_data=f"finance_budget_report_{budget.id}")
        ],
        [
            InlineKeyboardButton("◀️ Back to Budgets", callback_data="finance_budgets")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_month_selection_keyboard(
    current_year: int = date.today().year,
    current_month: int = date.today().month,
    callback_prefix: str = "finance_month"
) -> InlineKeyboardMarkup:
    """Create a keyboard for selecting a month."""
    keyboard = []
    
    # Month names
    month_names = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    
    # Add month buttons for current year
    for i in range(0, 12, 3):
        row = []
        for j in range(3):
            month_idx = i + j
            if month_idx < 12:
                month_num = month_idx + 1
                is_current = (month_num == current_month and current_year == date.today().year)
                month_name = month_names[month_idx]
                month_emoji = "📌 " if is_current else ""
                row.append(
                    InlineKeyboardButton(
                        f"{month_emoji}{month_name}", 
                        callback_data=f"{callback_prefix}_{current_year}_{month_num}"
                    )
                )
        keyboard.append(row)
    
    # Add year navigation
    keyboard.append([
        InlineKeyboardButton(f"◀️ {current_year - 1}", callback_data=f"{callback_prefix}_year_{current_year - 1}"),
        InlineKeyboardButton(f"{current_year + 1} ▶️", callback_data=f"{callback_prefix}_year_{current_year + 1}")
    ])
    
    # Back button
    keyboard.append([
        InlineKeyboardButton("◀️ Back", callback_data="finance_reports")
    ])
    
    return InlineKeyboardMarkup(keyboard)