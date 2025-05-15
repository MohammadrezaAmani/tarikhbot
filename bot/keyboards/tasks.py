from typing import Dict, List, Optional
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from apps.shared.enums import TaskPriority, TaskStatus
from database.models import Task

def get_task_list_keyboard(
    tasks: List[Task],
    current_page: int = 0,
    total_pages: int = 1,
    back_callback: str = "main_menu"
) -> InlineKeyboardMarkup:
    """Create a keyboard for a list of tasks."""
    keyboard = []
    
    # Add task buttons
    for task in tasks:
        # Create status indicator emoji
        status_emoji = TaskStatus.get_emoji(task.status)
        priority_emoji = TaskPriority.get_emoji(task.priority)
        
        # Format due date if available
        due_str = ""
        if task.due_date:
            due_str = f" | 📅 {task.due_date.strftime('%d %b')}"
        
        # Create button text
        button_text = f"{status_emoji} {priority_emoji} {task.title[:20]}{due_str}"
        
        # Create button
        keyboard.append([
            InlineKeyboardButton(button_text, callback_data=f"task_view_{task.id}")
        ])
    
    # Add action buttons
    keyboard.append([
        InlineKeyboardButton("➕ New Task", callback_data="task_create"),
        InlineKeyboardButton("🔍 Filter", callback_data="task_filter")
    ])
    
    # Add pagination controls
    pagination_row = []
    
    if current_page > 0:
        pagination_row.append(
            InlineKeyboardButton("◀️ Previous", callback_data=f"task_list_page_{current_page-1}")
        )
    
    if current_page < total_pages - 1:
        pagination_row.append(
            InlineKeyboardButton("Next ▶️", callback_data=f"task_list_page_{current_page+1}")
        )
    
    if pagination_row:
        keyboard.append(pagination_row)
    
    # Add back button
    keyboard.append([
        InlineKeyboardButton("◀️ Back to Menu", callback_data=back_callback)
    ])
    
    return InlineKeyboardMarkup(keyboard)

def get_task_detail_keyboard(task: Task) -> InlineKeyboardMarkup:
    """Create a keyboard for task details."""
    keyboard = []
    
    # Toggle completion button
    if task.status == TaskStatus.DONE:
        status_text = "↩️ Mark as To Do"
        status_callback = f"task_mark_todo_{task.id}"
    else:
        status_text = "✅ Mark as Done"
        status_callback = f"task_mark_done_{task.id}"
    
    keyboard.append([
        InlineKeyboardButton(status_text, callback_data=status_callback)
    ])
    
    # Edit and Delete buttons
    keyboard.append([
        InlineKeyboardButton("✏️ Edit", callback_data=f"task_edit_{task.id}"),
        InlineKeyboardButton("🗑️ Delete", callback_data=f"task_delete_{task.id}")
    ])
    
    # Additional actions
    keyboard.append([
        InlineKeyboardButton("🔔 Set Reminder", callback_data=f"task_reminder_{task.id}"),
        InlineKeyboardButton("📎 Attachments", callback_data=f"task_attachments_{task.id}")
    ])
    
    # Add subtask button
    keyboard.append([
        InlineKeyboardButton("➕ Add Subtask", callback_data=f"task_add_subtask_{task.id}")
    ])
    
    # Back button
    keyboard.append([
        InlineKeyboardButton("◀️ Back to Tasks", callback_data="tasks_menu")
    ])
    
    return InlineKeyboardMarkup(keyboard)

def get_task_filter_keyboard(
    current_filters: Dict = None,
    callback_prefix: str = "task_filter"
) -> InlineKeyboardMarkup:
    """Create a keyboard for task filtering options."""
    if current_filters is None:
        current_filters = {}
    
    # Get current filter values with defaults
    status = current_filters.get("status")
    priority = current_filters.get("priority")
    project_id = current_filters.get("project_id")
    
    keyboard = []
    
    # Status filter
    status_text = f"Status: {TaskStatus.get_display_name(status)}" if status else "Status: Any"
    keyboard.append([
        InlineKeyboardButton(status_text, callback_data=f"{callback_prefix}_status")
    ])
    
    # Priority filter
    priority_text = f"Priority: {TaskPriority.get_display_name(priority)}" if priority else "Priority: Any"
    keyboard.append([
        InlineKeyboardButton(priority_text, callback_data=f"{callback_prefix}_priority")
    ])
    
    # Project filter
    project_text = "Project: Selected" if project_id else "Project: Any"
    keyboard.append([
        InlineKeyboardButton(project_text, callback_data=f"{callback_prefix}_project")
    ])
    
    # Date range filter
    keyboard.append([
        InlineKeyboardButton("📅 Date Range", callback_data=f"{callback_prefix}_date")
    ])
    
    # Apply and reset buttons
    keyboard.append([
        InlineKeyboardButton("✅ Apply Filters", callback_data=f"{callback_prefix}_apply"),
        InlineKeyboardButton("🔄 Reset", callback_data=f"{callback_prefix}_reset")
    ])
    
    # Back button
    keyboard.append([
        InlineKeyboardButton("◀️ Back", callback_data="tasks_menu")
    ])
    
    return InlineKeyboardMarkup(keyboard)

def get_task_status_keyboard(callback_prefix: str) -> InlineKeyboardMarkup:
    """Create a keyboard for selecting task status."""
    keyboard = []
    
    for status in TaskStatus:
        emoji = TaskStatus.get_emoji(status)
        name = TaskStatus.get_display_name(status)
        keyboard.append([
            InlineKeyboardButton(f"{emoji} {name}", callback_data=f"{callback_prefix}_{status.value}")
        ])
    
    # Add "Any" option for filters
    keyboard.append([
        InlineKeyboardButton("🔍 Any Status", callback_data=f"{callback_prefix}_any")
    ])
    
    # Back button
    keyboard.append([
        InlineKeyboardButton("◀️ Back", callback_data="task_filter")
    ])
    
    return InlineKeyboardMarkup(keyboard)

def get_task_priority_keyboard(callback_prefix: str) -> InlineKeyboardMarkup:
    """Create a keyboard for selecting task priority."""
    keyboard = []
    
    for priority in TaskPriority:
        emoji = TaskPriority.get_emoji(priority)
        name = TaskPriority.get_display_name(priority)
        keyboard.append([
            InlineKeyboardButton(f"{emoji} {name}", callback_data=f"{callback_prefix}_{priority.value}")
        ])
    
    # Add "Any" option for filters
    keyboard.append([
        InlineKeyboardButton("🔍 Any Priority", callback_data=f"{callback_prefix}_any")
    ])
    
    # Back button
    keyboard.append([
        InlineKeyboardButton("◀️ Back", callback_data="task_filter")
    ])
    
    return InlineKeyboardMarkup(keyboard)

def get_project_selection_keyboard(
    projects: List,
    callback_prefix: str,
    current_page: int = 0,
    items_per_page: int = 5
) -> InlineKeyboardMarkup:
    """Create a keyboard for selecting a project."""
    keyboard = []
    
    # Calculate pagination
    total_pages = (len(projects) + items_per_page - 1) // items_per_page
    start_idx = current_page * items_per_page
    end_idx = min(start_idx + items_per_page, len(projects))
    current_projects = projects[start_idx:end_idx]
    
    # Add project buttons
    for project in current_projects:
        keyboard.append([
            InlineKeyboardButton(
                f"{project.icon or '📁'} {project.name}", 
                callback_data=f"{callback_prefix}_{project.id}"
            )
        ])
    
    # Add "No Project" option
    keyboard.append([
        InlineKeyboardButton("📋 No Project", callback_data=f"{callback_prefix}_none")
    ])
    
    # Add "Any Project" option for filters
    keyboard.append([
        InlineKeyboardButton("🔍 Any Project", callback_data=f"{callback_prefix}_any")
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
        InlineKeyboardButton("◀️ Back", callback_data="task_filter")
    ])
    
    return InlineKeyboardMarkup(keyboard)

def get_task_reminder_keyboard(task_id: int) -> InlineKeyboardMarkup:
    """Create a keyboard for setting task reminders."""
    keyboard = [
        [
            InlineKeyboardButton("⏰ 30 Minutes Before", callback_data=f"task_reminder_30min_{task_id}")
        ],
        [
            InlineKeyboardButton("⏰ 1 Hour Before", callback_data=f"task_reminder_1hour_{task_id}")
        ],
        [
            InlineKeyboardButton("⏰ 3 Hours Before", callback_data=f"task_reminder_3hours_{task_id}")
        ],
        [
            InlineKeyboardButton("⏰ 1 Day Before", callback_data=f"task_reminder_1day_{task_id}")
        ],
        [
            InlineKeyboardButton("🕐 Custom Time", callback_data=f"task_reminder_custom_{task_id}")
        ],
        [
            InlineKeyboardButton("❌ Remove Reminder", callback_data=f"task_reminder_remove_{task_id}")
        ],
        [
            InlineKeyboardButton("◀️ Back", callback_data=f"task_view_{task_id}")
        ]
    ]
    
    return InlineKeyboardMarkup(keyboard)

def get_task_edit_keyboard(task_id: int) -> InlineKeyboardMarkup:
    """Create a keyboard for editing task properties."""
    keyboard = [
        [
            InlineKeyboardButton("✏️ Edit Title", callback_data=f"task_edit_title_{task_id}")
        ],
        [
            InlineKeyboardButton("📝 Edit Description", callback_data=f"task_edit_desc_{task_id}")
        ],
        [
            InlineKeyboardButton("📅 Change Due Date", callback_data=f"task_edit_date_{task_id}")
        ],
        [
            InlineKeyboardButton("🚩 Change Priority", callback_data=f"task_edit_priority_{task_id}")
        ],
        [
            InlineKeyboardButton("📁 Change Project", callback_data=f"task_edit_project_{task_id}")
        ],
        [
            InlineKeyboardButton("🏷️ Edit Tags", callback_data=f"task_edit_tags_{task_id}")
        ],
        [
            InlineKeyboardButton("◀️ Back", callback_data=f"task_view_{task_id}")
        ]
    ]
    
    return InlineKeyboardMarkup(keyboard)