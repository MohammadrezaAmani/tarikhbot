from enum import Enum
from typing import Dict, List, Optional, Union

class TaskPriority(str, Enum):
    """Task priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    
    @classmethod
    def get_emoji(cls, priority: "TaskPriority") -> str:
        """Get emoji representation of priority."""
        emoji_map = {
            cls.LOW: "🟢",
            cls.MEDIUM: "🟡",
            cls.HIGH: "🟠",
            cls.URGENT: "🔴"
        }
        return emoji_map.get(priority, "⚪")
    
    @classmethod
    def get_display_name(cls, priority: "TaskPriority") -> str:
        """Get human-readable name for priority."""
        name_map = {
            cls.LOW: "Low",
            cls.MEDIUM: "Medium",
            cls.HIGH: "High",
            cls.URGENT: "Urgent"
        }
        return name_map.get(priority, "Unknown")


class TaskStatus(str, Enum):
    """Task status states."""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    ARCHIVED = "archived"
    
    @classmethod
    def get_emoji(cls, status: "TaskStatus") -> str:
        """Get emoji representation of status."""
        emoji_map = {
            cls.TODO: "📋",
            cls.IN_PROGRESS: "🔄",
            cls.DONE: "✅",
            cls.ARCHIVED: "🗄️"
        }
        return emoji_map.get(status, "❓")
    
    @classmethod
    def get_display_name(cls, status: "TaskStatus") -> str:
        """Get human-readable name for status."""
        name_map = {
            cls.TODO: "To Do",
            cls.IN_PROGRESS: "In Progress",
            cls.DONE: "Done",
            cls.ARCHIVED: "Archived"
        }
        return name_map.get(status, "Unknown")


class RecurrenceType(str, Enum):
    """Task recurrence types."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    CUSTOM = "custom"  # For custom cron expressions
    
    @classmethod
    def get_emoji(cls, recurrence_type: "RecurrenceType") -> str:
        """Get emoji representation of recurrence type."""
        emoji_map = {
            cls.DAILY: "📆",
            cls.WEEKLY: "📅",
            cls.MONTHLY: "📆",
            cls.YEARLY: "🗓️",
            cls.CUSTOM: "⚙️"
        }
        return emoji_map.get(recurrence_type, "❓")
    
    @classmethod
    def get_display_name(cls, recurrence_type: "RecurrenceType") -> str:
        """Get human-readable name for recurrence type."""
        name_map = {
            cls.DAILY: "Daily",
            cls.WEEKLY: "Weekly",
            cls.MONTHLY: "Monthly",
            cls.YEARLY: "Yearly",
            cls.CUSTOM: "Custom"
        }
        return name_map.get(recurrence_type, "Unknown")
    
    @classmethod
    def get_cron_expression(cls, recurrence_type: "RecurrenceType", **kwargs) -> str:
        """Get cron expression for recurrence type."""
        if recurrence_type == cls.DAILY:
            hour = kwargs.get("hour", 9)
            minute = kwargs.get("minute", 0)
            return f"{minute} {hour} * * *"
        elif recurrence_type == cls.WEEKLY:
            hour = kwargs.get("hour", 9)
            minute = kwargs.get("minute", 0)
            day_of_week = kwargs.get("day_of_week", 1)  # 1 = Monday
            return f"{minute} {hour} * * {day_of_week}"
        elif recurrence_type == cls.MONTHLY:
            hour = kwargs.get("hour", 9)
            minute = kwargs.get("minute", 0)
            day_of_month = kwargs.get("day_of_month", 1)
            return f"{minute} {hour} {day_of_month} * *"
        elif recurrence_type == cls.YEARLY:
            hour = kwargs.get("hour", 9)
            minute = kwargs.get("minute", 0)
            day_of_month = kwargs.get("day_of_month", 1)
            month = kwargs.get("month", 1)
            return f"{minute} {hour} {day_of_month} {month} *"
        elif recurrence_type == cls.CUSTOM:
            return kwargs.get("cron_expression", "0 9 * * *")
        else:
            return "0 9 * * *"  # Default to 9am daily


class TransactionType(str, Enum):
    """Financial transaction types."""
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"
    
    @classmethod
    def get_emoji(cls, transaction_type: "TransactionType") -> str:
        """Get emoji representation of transaction type."""
        emoji_map = {
            cls.INCOME: "💰",
            cls.EXPENSE: "💸",
            cls.TRANSFER: "🔄"
        }
        return emoji_map.get(transaction_type, "❓")
    
    @classmethod
    def get_display_name(cls, transaction_type: "TransactionType") -> str:
        """Get human-readable name for transaction type."""
        name_map = {
            cls.INCOME: "Income",
            cls.EXPENSE: "Expense",
            cls.TRANSFER: "Transfer"
        }
        return name_map.get(transaction_type, "Unknown")


class UserRole(str, Enum):
    """User role types for projects and collaborations."""
    OWNER = "owner"
    ADMIN = "admin"
    COLLABORATOR = "collaborator"
    VIEWER = "viewer"
    
    @classmethod
    def get_emoji(cls, role: "UserRole") -> str:
        """Get emoji representation of user role."""
        emoji_map = {
            cls.OWNER: "👑",
            cls.ADMIN: "🔑",
            cls.COLLABORATOR: "👥",
            cls.VIEWER: "👁️"
        }
        return emoji_map.get(role, "❓")
    
    @classmethod
    def get_display_name(cls, role: "UserRole") -> str:
        """Get human-readable name for user role."""
        name_map = {
            cls.OWNER: "Owner",
            cls.ADMIN: "Admin",
            cls.COLLABORATOR: "Collaborator",
            cls.VIEWER: "Viewer"
        }
        return name_map.get(role, "Unknown")
    
    @classmethod
    def can_edit(cls, role: "UserRole") -> bool:
        """Check if the role has edit permissions."""
        return role in [cls.OWNER, cls.ADMIN, cls.COLLABORATOR]
    
    @classmethod
    def can_delete(cls, role: "UserRole") -> bool:
        """Check if the role has delete permissions."""
        return role in [cls.OWNER, cls.ADMIN]
    
    @classmethod
    def can_manage_users(cls, role: "UserRole") -> bool:
        """Check if the role can manage users."""
        return role in [cls.OWNER, cls.ADMIN]


class Language(str, Enum):
    """Supported languages for the bot."""
    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    RUSSIAN = "ru"
    CHINESE = "zh"
    
    @classmethod
    def get_emoji(cls, language: "Language") -> str:
        """Get emoji representation of language."""
        emoji_map = {
            cls.ENGLISH: "🇬🇧",
            cls.SPANISH: "🇪🇸",
            cls.FRENCH: "🇫🇷",
            cls.GERMAN: "🇩🇪",
            cls.RUSSIAN: "🇷🇺",
            cls.CHINESE: "🇨🇳"
        }
        return emoji_map.get(language, "🌐")
    
    @classmethod
    def get_display_name(cls, language: "Language") -> str:
        """Get human-readable name for language."""
        name_map = {
            cls.ENGLISH: "English",
            cls.SPANISH: "Español",
            cls.FRENCH: "Français",
            cls.GERMAN: "Deutsch",
            cls.RUSSIAN: "Русский",
            cls.CHINESE: "中文"
        }
        return name_map.get(language, "Unknown")