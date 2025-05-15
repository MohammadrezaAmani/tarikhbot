from typing import Dict, List

# Main welcome message shown when user starts the bot
WELCOME_MESSAGE = """
👋 Welcome to Task Manager Bot!

I'm your personal assistant for managing tasks, finances, and scheduling. Here's what I can do:

📋 **Tasks** - Create and manage tasks with priorities, due dates, and reminders
💰 **Finance** - Track income and expenses, manage budgets, and view financial reports
📊 **Statistics** - View insights about your productivity and spending habits
📅 **Google Calendar** - Sync tasks with your Google Calendar
📧 **Gmail** - Send reports and reminders via Gmail

Use the menu below to get started!
"""

# Help message shown when /help command is used
HELP_MESSAGE = """
🔍 **How To Use This Bot**

**Basic Commands:**
/start - Return to the main menu
/help - Show this help message
/settings - Manage your settings
/cancel - Cancel current operation

**Task Management:**
• To create a task, select "Tasks" → "Add Task"
• You can add due dates, priorities, and reminders
• Tasks can be organized into projects and tags
• For quick task creation, try natural language: "remind me to buy milk tomorrow"

**Finance Tracking:**
• To add transactions, select "Finance" → "Add Transaction"
• Create budgets to track your spending limits
• View reports by day, month, or category

**Google Integration:**
• Connect your Google account in Settings
• Sync tasks with Google Calendar
• Use Gmail for sending reports

**Tips:**
• Use the menu buttons for most functions
• Inline buttons make navigation easy
• Swipe through lists to see more items
• Set your timezone for accurate reminders

Need more help? Feel free to ask specific questions!
"""

# Error messages
ERROR_MESSAGES = {
    "general": "⚠️ An error occurred. Please try again later.",
    "not_found": "⚠️ Item not found. It may have been deleted.",
    "permission": "⚠️ You don't have permission to perform this action.",
    "input": "⚠️ Invalid input. Please try again.",
    "timeout": "⚠️ Operation timed out. Please try again.",
    "google_auth": "⚠️ Google authentication failed. Please reconnect your account in Settings.",
}

# Success messages
SUCCESS_MESSAGES = {
    "task_created": "✅ Task created successfully!",
    "task_updated": "✅ Task updated successfully!",
    "task_deleted": "✅ Task deleted successfully!",
    "transaction_created": "✅ Transaction recorded successfully!",
    "transaction_updated": "✅ Transaction updated successfully!",
    "transaction_deleted": "✅ Transaction deleted successfully!",
    "budget_created": "✅ Budget created successfully!",
    "settings_updated": "✅ Settings updated successfully!",
    "google_connected": "✅ Google account connected successfully!",
}

# Confirmation messages
CONFIRMATION_MESSAGES = {
    "delete_task": "⚠️ Are you sure you want to delete this task? This cannot be undone.",
    "delete_project": "⚠️ Are you sure you want to delete this project? All tasks in this project will also be deleted. This cannot be undone.",
    "delete_transaction": "⚠️ Are you sure you want to delete this transaction? This cannot be undone.",
    "delete_budget": "⚠️ Are you sure you want to delete this budget? This cannot be undone.",
    "disconnect_google": "⚠️ Are you sure you want to disconnect your Google account? This will disable all Google integrations.",
}