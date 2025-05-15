# Task-related message templates
from typing import Dict, List, Optional

from apps.shared.enums import TaskPriority, TaskStatus, RecurrenceType

# Help message for task management
TASK_HELP_MESSAGE = """
📋 **Task Management Help**

**Commands and Actions:**
• To create a task, tap "Tasks" → "Add Task"
• To view all tasks, tap "Tasks" → "View Tasks"
• Mark tasks as complete by viewing a task and tapping "Mark as Done"
• Set reminders for important tasks to get notifications
• Organize tasks into projects for better management

**Task Properties:**
• **Priority**: Set task importance (Low, Medium, High, Urgent)
• **Due Date**: When the task needs to be completed
• **Reminders**: Get notified before the task is due
• **Projects**: Group related tasks together
• **Tags**: Categorize tasks for easy filtering
• **Attachments**: Add files, photos, or voice notes

**Tips:**
• Use natural language for quick task creation (e.g., "Buy milk tomorrow")
• Set recurring tasks for regular activities
• View your task statistics to track productivity
• Sync with Google Calendar for cross-platform access

Need more help with a specific feature? Just ask!
"""

# Function to format a task for display
def format_task_details(task: Dict, include_subtasks: bool = False) -> str:
    """Format a task for display in a message."""
    # Get basic task info
    title = task.get("title", "Untitled Task")
    description = task.get("description", "")
    status = task.get("status", TaskStatus.TODO)
    priority = task.get("priority", TaskPriority.MEDIUM)
    
    # Format status and priority with emojis
    status_emoji = TaskStatus.get_emoji(status)
    priority_emoji = TaskPriority.get_emoji(priority)
    
    # Format dates
    due_date = task.get("due_date")
    due_date_str = due_date.strftime("%d %b %Y, %H:%M") if due_date else "No due date"
    
    reminder_time = task.get("reminder_time")
    reminder_str = reminder_time.strftime("%d %b %Y, %H:%M") if reminder_time else "No reminder"
    
    created_at = task.get("created_at")
    created_str = created_at.strftime("%d %b %Y") if created_at else "Unknown"
    
    # Check for recurrence
    is_recurring = task.get("is_recurring", False)
    recurrence_type = task.get("recurrence_type")
    recurrence_str = ""
    if is_recurring and recurrence_type:
        recurrence_str = f"\n🔄 **Recurring:** {RecurrenceType.get_display_name(recurrence_type)}"
    
    # Get project and tags
    project = task.get("project")
    project_str = f"\n📁 **Project:** {project.get('name')}" if project else ""
    
    tags = task.get("tags", [])
    tags_str = ""
    if tags:
        tag_names = [tag.get("name", "") for tag in tags]
        tags_str = f"\n🏷️ **Tags:** {', '.join(tag_names)}"
    
    # Format completed status
    completed_at = task.get("completed_at")
    completed_str = ""
    if status == TaskStatus.DONE and completed_at:
        completed_str = f"\n✅ **Completed:** {completed_at.strftime('%d %b %Y, %H:%M')}"
    
    # Build the message
    message = (
        f"**{status_emoji} {title}**\n\n"
        f"{description}\n\n"
        f"📊 **Status:** {status_emoji} {TaskStatus.get_display_name(status)}\n"
        f"🚩 **Priority:** {priority_emoji} {TaskPriority.get_display_name(priority)}\n"
        f"📅 **Due Date:** {due_date_str}\n"
        f"⏰ **Reminder:** {reminder_str}"
        f"{recurrence_str}"
        f"{project_str}"
        f"{tags_str}"
        f"{completed_str}\n\n"
        f"📝 **Created:** {created_str}"
    )
    
    # Add subtasks if requested and available
    subtasks = task.get("subtasks", [])
    if include_subtasks and subtasks:
        message += "\n\n📋 **Subtasks:**"
        for subtask in subtasks:
            subtask_status = TaskStatus.get_emoji(subtask.get("status", TaskStatus.TODO))
            subtask_title = subtask.get("title", "Untitled")
            message += f"\n{subtask_status} {subtask_title}"
    
    return message

# Task creation guidance
TASK_CREATION_GUIDE = """
**Creating a New Task**

Please provide the following information:

1️⃣ **Task Title** (required)
2️⃣ **Description** (optional)
3️⃣ **Due Date** (optional, format: DD/MM/YYYY or "today"/"tomorrow")
4️⃣ **Priority** (optional: low, medium, high, urgent)

Example: "Buy groceries for dinner tomorrow, high priority"

You can also use natural language, and I'll try to understand your intent!
"""

# Task filter instructions
TASK_FILTER_INSTRUCTIONS = """
**Filter Your Tasks**

You can filter your tasks by:
• Status (To Do, In Progress, Done)
• Priority (Low, Medium, High, Urgent)
• Project
• Due Date Range
• Tags

Use the buttons below to set your filters, then tap "Apply Filters" to see the results.
"""

# No tasks message
NO_TASKS_MESSAGE = """
📋 **No Tasks Found**

You don't have any tasks that match your criteria. 

Would you like to:
• Create a new task
• Change your filters
• View all tasks
"""

# Task reminder message template
def format_task_reminder(task: Dict) -> str:
    """Format a task reminder message."""
    title = task.get("title", "Untitled Task")
    due_date = task.get("due_date")
    due_date_str = due_date.strftime("%d %b %Y, %H:%M") if due_date else "No due date"
    
    return (
        f"⏰ **Reminder: Task Due Soon**\n\n"
        f"Your task **{title}** is due at {due_date_str}.\n\n"
        f"Use the buttons below to manage this task."
    )

# Task statistics message template
def format_task_stats(stats: Dict) -> str:
    """Format task statistics message."""
    total_tasks = stats.get("total", 0)
    completed = stats.get("completed", 0)
    pending = stats.get("pending", 0)
    overdue = stats.get("overdue", 0)
    
    completion_rate = (completed / total_tasks * 100) if total_tasks > 0 else 0
    
    return (
        f"📊 **Your Task Statistics**\n\n"
        f"**Total Tasks:** {total_tasks}\n"
        f"**Completed:** {completed} ({completion_rate:.1f}%)\n"
        f"**Pending:** {pending}\n"
        f"**Overdue:** {overdue}\n\n"
        f"Keep up the good work! 💪"
    )