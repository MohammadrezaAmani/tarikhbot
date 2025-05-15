from typing import Dict, List, Optional
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Create the main menu keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("📋 Tasks", callback_data="tasks_menu"),
            InlineKeyboardButton("💰 Finance", callback_data="finance_menu")
        ],
        [
            InlineKeyboardButton("📊 Statistics", callback_data="stats_menu"),
            InlineKeyboardButton("⚙️ Settings", callback_data="settings_menu")
        ],
        [
            InlineKeyboardButton("📅 Google Calendar", callback_data="google_cal_menu"),
            InlineKeyboardButton("📧 Gmail", callback_data="google_gmail_menu")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_settings_keyboard(user_profile: Dict) -> InlineKeyboardMarkup:
    """Create the settings menu keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("🌐 Change Language", callback_data="settings_language"),
            InlineKeyboardButton("🕒 Change Timezone", callback_data="settings_timezone")
        ]
    ]
    
    # Add Google integration button based on connection status
    if user_profile.get("google_connected"):
        keyboard.append([
            InlineKeyboardButton("🔄 Google Sync Settings", callback_data="settings_google_sync"),
            InlineKeyboardButton("🔌 Disconnect Google", callback_data="settings_google_disconnect")
        ])
    else:
        keyboard.append([
            InlineKeyboardButton("🔗 Connect Google Account", callback_data="settings_google_connect")
        ])
    
    # Add more settings options
    keyboard.append([
        InlineKeyboardButton("🔔 Notification Settings", callback_data="settings_notifications")
    ])
    
    # Add back button
    keyboard.append([
        InlineKeyboardButton("◀️ Back to Main Menu", callback_data="main_menu")
    ])
    
    return InlineKeyboardMarkup(keyboard)

def get_language_keyboard() -> InlineKeyboardMarkup:
    """Create a keyboard for language selection."""
    keyboard = [
        [
            InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
            InlineKeyboardButton("🇪🇸 Español", callback_data="lang_es")
        ],
        [
            InlineKeyboardButton("🇫🇷 Français", callback_data="lang_fr"),
            InlineKeyboardButton("🇩🇪 Deutsch", callback_data="lang_de")
        ],
        [
            InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
            InlineKeyboardButton("🇨🇳 中文", callback_data="lang_zh")
        ],
        [
            InlineKeyboardButton("◀️ Back", callback_data="settings_menu")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_timezone_regions_keyboard() -> InlineKeyboardMarkup:
    """Create a keyboard for timezone region selection."""
    keyboard = [
        [
            InlineKeyboardButton("Africa", callback_data="tz_region_Africa"),
            InlineKeyboardButton("America", callback_data="tz_region_America")
        ],
        [
            InlineKeyboardButton("Asia", callback_data="tz_region_Asia"),
            InlineKeyboardButton("Europe", callback_data="tz_region_Europe")
        ],
        [
            InlineKeyboardButton("Australia", callback_data="tz_region_Australia"),
            InlineKeyboardButton("Pacific", callback_data="tz_region_Pacific")
        ],
        [
            InlineKeyboardButton("◀️ Back", callback_data="settings_menu")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_timezone_cities_keyboard(region: str, page: int = 0) -> InlineKeyboardMarkup:
    """Create a paginated keyboard for timezone city selection."""
    # This is a simplified example - in a real implementation you'd pull these from a library
    cities_by_region = {
        "Africa": ["Cairo", "Johannesburg", "Lagos", "Nairobi"],
        "America": ["New_York", "Los_Angeles", "Chicago", "Toronto", "Mexico_City", "Sao_Paulo"],
        "Asia": ["Tokyo", "Shanghai", "Seoul", "Singapore", "Dubai", "Kolkata", "Mumbai"],
        "Europe": ["London", "Paris", "Berlin", "Rome", "Madrid", "Moscow"],
        "Australia": ["Sydney", "Melbourne", "Perth", "Brisbane"],
        "Pacific": ["Auckland", "Honolulu", "Fiji"]
    }
    
    # Get cities for the selected region with pagination
    cities = cities_by_region.get(region, [])
    items_per_page = 6
    total_pages = (len(cities) + items_per_page - 1) // items_per_page
    
    start_idx = page * items_per_page
    end_idx = min(start_idx + items_per_page, len(cities))
    current_cities = cities[start_idx:end_idx]
    
    # Create keyboard with cities
    keyboard = []
    for i in range(0, len(current_cities), 2):
        row = []
        for j in range(2):
            if i + j < len(current_cities):
                city = current_cities[i + j]
                row.append(
                    InlineKeyboardButton(
                        city.replace("_", " "), 
                        callback_data=f"tz_{region}/{city}"
                    )
                )
        keyboard.append(row)
    
    # Add pagination controls if needed
    pagination_row = []
    if page > 0:
        pagination_row.append(
            InlineKeyboardButton("◀️ Previous", callback_data=f"tz_region_{region}_page_{page-1}")
        )
    
    if page < total_pages - 1:
        pagination_row.append(
            InlineKeyboardButton("Next ▶️", callback_data=f"tz_region_{region}_page_{page+1}")
        )
    
    if pagination_row:
        keyboard.append(pagination_row)
    
    # Add back button
    keyboard.append([
        InlineKeyboardButton("◀️ Back to Regions", callback_data="settings_timezone")
    ])
    
    return InlineKeyboardMarkup(keyboard)

def get_google_sync_keyboard(google_auth: Dict) -> InlineKeyboardMarkup:
    """Create a keyboard for Google sync settings."""
    calendar_sync = google_auth.get("calendar_sync_enabled", False)
    gmail_sync = google_auth.get("gmail_sync_enabled", False)
    
    keyboard = [
        [
            InlineKeyboardButton(
                f"📅 Calendar Sync: {'ON ✅' if calendar_sync else 'OFF ❌'}", 
                callback_data="toggle_calendar_sync"
            )
        ],
        [
            InlineKeyboardButton(
                f"📧 Gmail Sync: {'ON ✅' if gmail_sync else 'OFF ❌'}", 
                callback_data="toggle_gmail_sync"
            )
        ],
        [
            InlineKeyboardButton("🔄 Sync Now", callback_data="sync_google_now")
        ],
        [
            InlineKeyboardButton("◀️ Back", callback_data="settings_menu")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_confirmation_keyboard(action: str, item_id: Optional[str] = None) -> InlineKeyboardMarkup:
    """Create a confirmation keyboard for destructive actions."""
    callback_prefix = f"{action}_{item_id}_" if item_id else f"{action}_"
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes", callback_data=f"{callback_prefix}confirm"),
            InlineKeyboardButton("❌ No", callback_data=f"{callback_prefix}cancel")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_pagination_keyboard(
    current_page: int, 
    total_pages: int, 
    callback_prefix: str,
    show_back: bool = True,
    back_callback: str = "main_menu"
) -> InlineKeyboardMarkup:
    """Create a pagination keyboard."""
    keyboard = []
    
    # Add pagination controls
    pagination_row = []
    
    # First page button
    if current_page > 0:
        pagination_row.append(
            InlineKeyboardButton("⏮️", callback_data=f"{callback_prefix}_page_0")
        )
    
    # Previous page button
    if current_page > 0:
        pagination_row.append(
            InlineKeyboardButton("◀️", callback_data=f"{callback_prefix}_page_{current_page-1}")
        )
    
    # Page indicator
    pagination_row.append(
        InlineKeyboardButton(f"{current_page+1}/{total_pages}", callback_data="noop")
    )
    
    # Next page button
    if current_page < total_pages - 1:
        pagination_row.append(
            InlineKeyboardButton("▶️", callback_data=f"{callback_prefix}_page_{current_page+1}")
        )
    
    # Last page button
    if current_page < total_pages - 1:
        pagination_row.append(
            InlineKeyboardButton("⏭️", callback_data=f"{callback_prefix}_page_{total_pages-1}")
        )
    
    if pagination_row:
        keyboard.append(pagination_row)
    
    # Add back button
    if show_back:
        keyboard.append([
            InlineKeyboardButton("◀️ Back", callback_data=back_callback)
        ])
    
    return InlineKeyboardMarkup(keyboard)

def get_notification_settings_keyboard(user_profile: Dict) -> InlineKeyboardMarkup:
    """Create a keyboard for notification settings."""
    # Extract notification settings from user profile preferences
    preferences = user_profile.get("preferences", {})
    notif_settings = preferences.get("notifications", {})
    
    task_reminders = notif_settings.get("task_reminders", True)
    daily_summary = notif_settings.get("daily_summary", False)
    overdue_alerts = notif_settings.get("overdue_alerts", True)
    budget_alerts = notif_settings.get("budget_alerts", True)
    
    keyboard = [
        [
            InlineKeyboardButton(
                f"🔔 Task Reminders: {'ON ✅' if task_reminders else 'OFF ❌'}", 
                callback_data="toggle_notif_task_reminders"
            )
        ],
        [
            InlineKeyboardButton(
                f"📊 Daily Summary: {'ON ✅' if daily_summary else 'OFF ❌'}", 
                callback_data="toggle_notif_daily_summary"
            )
        ],
        [
            InlineKeyboardButton(
                f"⏰ Overdue Alerts: {'ON ✅' if overdue_alerts else 'OFF ❌'}", 
                callback_data="toggle_notif_overdue_alerts"
            )
        ],
        [
            InlineKeyboardButton(
                f"💰 Budget Alerts: {'ON ✅' if budget_alerts else 'OFF ❌'}", 
                callback_data="toggle_notif_budget_alerts"
            )
        ],
        [
            InlineKeyboardButton("◀️ Back", callback_data="settings_menu")
        ]
    ]
    
    return InlineKeyboardMarkup(keyboard)

def yes_no_keyboard(callback_prefix: str) -> InlineKeyboardMarkup:
    """Simple Yes/No keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes", callback_data=f"{callback_prefix}_yes"),
            InlineKeyboardButton("❌ No", callback_data=f"{callback_prefix}_no")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Create a simple keyboard with just a cancel button."""
    keyboard = [[KeyboardButton("❌ Cancel")]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)