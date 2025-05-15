# Finance-related message templates
from typing import Dict, List, Optional
from decimal import Decimal
from datetime import date

from apps.shared.enums import TransactionType

# Help message for financial management
FINANCE_HELP_MESSAGE = """
💰 **Financial Management Help**

**Commands and Actions:**
• To add a transaction, tap "Finance" → "New Transaction"
• View your transactions by tapping "Finance" → "Transactions"
• Create budgets to track spending limits
• Generate financial reports and statistics

**Transaction Types:**
• **Income**: Money you receive (salary, gifts, etc.)
• **Expense**: Money you spend (bills, shopping, etc.)
• **Transfer**: Moving money between accounts

**Features:**
• **Categories**: Organize transactions by purpose
• **Budgets**: Set spending limits for different categories
• **Reports**: Visualize your financial activity
• **Recurring**: Set up repeated transactions

**Tips:**
• Categorize all transactions for better insights
• Review your monthly summary regularly
• Set realistic budgets based on your income
• Export reports for financial planning

Need more help with a specific feature? Just ask!
"""

# Function to format a transaction for display
def format_transaction_details(transaction: Dict) -> str:
    """Format a transaction for display in a message."""
    # Get basic transaction info
    amount = transaction.get("amount", Decimal("0.00"))
    currency = transaction.get("currency", "USD")
    transaction_type = transaction.get("type", TransactionType.EXPENSE)
    transaction_date = transaction.get("date", date.today())
    description = transaction.get("description", "")
    
    # Format transaction type with emoji
    type_emoji = TransactionType.get_emoji(transaction_type)
    type_name = TransactionType.get_display_name(transaction_type)
    
    # Get category info
    category = transaction.get("category")
    category_str = f"\n📂 **Category:** {category.get('name')}" if category else ""
    
    # Get project info
    project = transaction.get("project")
    project_str = f"\n📁 **Project:** {project.get('name')}" if project else ""
    
    # Format date
    date_str = transaction_date.strftime("%d %b %Y")
    
    # Check for recurrence
    is_recurring = transaction.get("is_recurring", False)
    recurrence_str = "\n🔄 **Recurring:** Yes" if is_recurring else ""
    
    # Format amount with sign based on transaction type
    if transaction_type == TransactionType.INCOME:
        amount_str = f"+{amount} {currency}"
    elif transaction_type == TransactionType.EXPENSE:
        amount_str = f"-{amount} {currency}"
    else:
        amount_str = f"{amount} {currency}"
    
    # Build the message
    message = (
        f"**{type_emoji} {type_name}: {amount_str}**\n\n"
        f"{description}\n\n"
        f"📅 **Date:** {date_str}"
        f"{category_str}"
        f"{project_str}"
        f"{recurrence_str}\n\n"
        f"🆔 Transaction ID: {transaction.get('id', 'N/A')}"
    )
    
    return message

# Function to format a budget for display
def format_budget_details(budget: Dict, status: Dict = None) -> str:
    """Format a budget with its status for display."""
    # Get basic budget info
    name = budget.get("name", "Untitled Budget")
    amount = budget.get("amount", Decimal("0.00"))
    currency = budget.get("currency", "USD")
    start_date = budget.get("start_date", date.today())
    end_date = budget.get("end_date", date.today())
    
    # Format dates
    start_str = start_date.strftime("%d %b %Y")
    end_str = end_date.strftime("%d %b %Y")
    
    # Get category info
    category = budget.get("category")
    category_str = f"\n📂 **Category:** {category.get('name')}" if category else "\n📂 **Category:** All Categories"
    
    # Get project info
    project = budget.get("project")
    project_str = f"\n📁 **Project:** {project.get('name')}" if project else ""
    
    # Build basic message
    message = (
        f"**💼 Budget: {name}**\n\n"
        f"💰 **Amount:** {amount} {currency}\n"
        f"📅 **Period:** {start_str} to {end_str}"
        f"{category_str}"
        f"{project_str}\n"
    )
    
    # Add status information if available
    if status:
        spent = status.get("spent_amount", Decimal("0.00"))
        remaining = status.get("remaining_amount", amount)
        percent_used = status.get("percent_used", 0)
        status_type = status.get("status", "good")
        
        # Choose emoji based on status
        if status_type == "over_budget":
            status_emoji = "🚨"
        elif status_type == "warning":
            status_emoji = "⚠️"
        else:
            status_emoji = "✅"
        
        message += (
            f"\n**Budget Status:**\n"
            f"💸 **Spent:** {spent} {currency}\n"
            f"💰 **Remaining:** {remaining} {currency}\n"
            f"{status_emoji} **Progress:** {percent_used:.1f}% used\n"
        )
        
        # Add some transactions if available
        transactions = status.get("transactions", [])
        if transactions:
            message += "\n**Recent Transactions:**\n"
            for tx in transactions[:3]:  # Show up to 3 transactions
                tx_date = tx.get("date").strftime("%d %b")
                tx_amount = tx.get("amount")
                tx_description = tx.get("description", "No description")
                message += f"• {tx_date}: {tx_description} - {tx_amount} {currency}\n"
    
    return message

# Transaction creation guidance
TRANSACTION_CREATION_GUIDE = """
**Adding a New Transaction**

Please select the type of transaction:
• 💰 **Income**: Money you received
• 💸 **Expense**: Money you spent
• 🔄 **Transfer**: Money moved between accounts

Then provide:
1️⃣ **Amount** (required)
2️⃣ **Category** (optional, but recommended)
3️⃣ **Description** (optional)
4️⃣ **Date** (defaults to today)

You can also tell me if this is a recurring transaction.
"""

# Budget creation guidance
BUDGET_CREATION_GUIDE = """
**Creating a New Budget**

Please provide the following information:
1️⃣ **Budget Name** (required)
2️⃣ **Amount** (required)
3️⃣ **Period** (monthly, custom dates, etc.)
4️⃣ **Category** (optional)
5️⃣ **Project** (optional)

This will help you track and manage your spending effectively.
"""

# No transactions message
NO_TRANSACTIONS_MESSAGE = """
💰 **No Transactions Found**

You don't have any transactions that match your criteria. 

Would you like to:
• Add a new transaction
• Change your filters
• View all transactions
"""

# Financial summary message template
def format_monthly_summary(summary: Dict) -> str:
    """Format monthly financial summary message."""
    income = summary.get("income", Decimal("0.00"))
    expenses = summary.get("expenses", Decimal("0.00"))
    balance = summary.get("balance", Decimal("0.00"))
    currency = summary.get("currency", "USD")
    month = summary.get("month", date.today().month)
    year = summary.get("year", date.today().year)
    
    # Month names
    month_names = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    
    month_name = month_names[month - 1]
    
    # Calculate savings rate if income > 0
    savings_rate = (balance / income * 100) if income > 0 else 0
    
    # Format message
    message = (
        f"📊 **Financial Summary: {month_name} {year}**\n\n"
        f"💰 **Income:** {income} {currency}\n"
        f"💸 **Expenses:** {expenses} {currency}\n"
        f"🏦 **Balance:** {balance} {currency}\n"
        f"💹 **Savings Rate:** {savings_rate:.1f}%\n\n"
    )
    
    # Add expense breakdown by category
    expense_categories = summary.get("expense_by_category", [])
    if expense_categories:
        message += "**Top Expense Categories:**\n"
        for i, category in enumerate(expense_categories[:5]):  # Show top 5 categories
            name = category.get("category_name", "Uncategorized")
            amount = category.get("amount", Decimal("0.00"))
            percentage = category.get("percentage", 0)
            message += f"• {name}: {amount} {currency} ({percentage:.1f}%)\n"
    
    return message