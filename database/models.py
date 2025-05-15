from tortoise import fields
from tortoise.models import Model
from enum import Enum
from typing import List, Dict, Union
import json
import datetime


# ----- Shared Enums -----
class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    ARCHIVED = "archived"


class RecurrenceType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    CUSTOM = "custom"  # For custom cron expressions


class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"


class UserRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    COLLABORATOR = "collaborator"
    VIEWER = "viewer"


# ----- Base Models -----
class BaseModel(Model):
    id = fields.IntField(pk=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        abstract = True


class JSONField(fields.TextField):
    """Custom JSON field that stores data as JSON string."""

    def to_db_value(self, value: Union[Dict, List], instance) -> str:
        if value is None:
            return None
        return json.dumps(value)

    def to_python_value(self, value: str) -> Union[Dict, List, None]:
        if value is None:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return None


# ----- User Models -----
class User(BaseModel):
    """Telegram user model."""

    telegram_id = fields.BigIntField(unique=True, index=True)
    username = fields.CharField(max_length=255, null=True)
    first_name = fields.CharField(max_length=255)
    last_name = fields.CharField(max_length=255, null=True)
    language_code = fields.CharField(max_length=10, default="en")
    timezone = fields.CharField(max_length=50, default="UTC")
    is_active = fields.BooleanField(default=True)
    is_premium = fields.BooleanField(default=False)
    preferences = JSONField(default=dict)

    # Relationships
    tasks: fields.ReverseRelation["Task"]
    projects: fields.ReverseRelation["Project"]
    transactions: fields.ReverseRelation["Transaction"]
    google_auth: fields.ReverseRelation["GoogleAuth"]

    class Meta:
        table = "users"

    def __str__(self):
        return f"User(id={self.id}, telegram_id={self.telegram_id}, name={self.first_name})"


class GoogleAuth(BaseModel):
    """Google OAuth2 credentials for a user."""

    user = fields.ForeignKeyField("models.User", related_name="google_auth")
    access_token = fields.CharField(max_length=2048)
    refresh_token = fields.CharField(max_length=512, null=True)
    token_expiry = fields.DatetimeField()
    email = fields.CharField(max_length=255, null=True)
    calendar_sync_enabled = fields.BooleanField(default=False)
    gmail_sync_enabled = fields.BooleanField(default=False)

    class Meta:
        table = "google_auth"

    def __str__(self):
        return f"GoogleAuth(user_id={self.user_id}, email={self.email})"

    def is_expired(self) -> bool:
        """Check if the token is expired."""
        return datetime.datetime.now() > self.token_expiry


# ----- Task Models -----
class Project(BaseModel):
    """Project model to group tasks."""

    name = fields.CharField(max_length=255)
    description = fields.TextField(null=True)
    color = fields.CharField(max_length=7, default="#4A6FFF")  # Hex color code
    icon = fields.CharField(max_length=50, null=True)  # Emoji or icon name
    owner = fields.ForeignKeyField("models.User", related_name="projects")
    is_archived = fields.BooleanField(default=False)

    # Budget fields
    budget = fields.DecimalField(max_digits=12, decimal_places=2, null=True)
    currency = fields.CharField(max_length=3, default="USD")

    # Relationships
    tasks: fields.ReverseRelation["Task"]
    collaborators: fields.ManyToManyRelation["User"] = fields.ManyToManyField(
        "models.User",
        related_name="collaborative_projects",
        through="project_collaborators",
    )

    class Meta:
        table = "projects"

    def __str__(self):
        return f"Project(id={self.id}, name={self.name})"


class ProjectCollaborator(Model):
    """Many-to-many through table for project collaborators with role."""

    project = fields.ForeignKeyField(
        "models.Project", related_name="project_collaborators"
    )
    user = fields.ForeignKeyField("models.User", related_name="project_collaborations")
    role = fields.CharEnumField(UserRole, default=UserRole.COLLABORATOR)

    class Meta:
        table = "project_collaborators"
        unique_together = (("project_id", "user_id"),)


class Tag(BaseModel):
    """Tags for tasks."""

    name = fields.CharField(max_length=50)
    color = fields.CharField(max_length=7, default="#4A6FFF")  # Hex color code
    user = fields.ForeignKeyField("models.User", related_name="tags")

    class Meta:
        table = "tags"
        unique_together = (("name", "user_id"),)

    def __str__(self):
        return f"Tag(id={self.id}, name={self.name})"


class Task(BaseModel):
    """Task model."""

    title = fields.CharField(max_length=255)
    description = fields.TextField(null=True)
    status = fields.CharEnumField(TaskStatus, default=TaskStatus.TODO)
    priority = fields.CharEnumField(TaskPriority, default=TaskPriority.MEDIUM)
    due_date = fields.DatetimeField(null=True)
    reminder_time = fields.DatetimeField(null=True)
    completed_at = fields.DatetimeField(null=True)

    # Relationships
    user = fields.ForeignKeyField("models.User", related_name="tasks")
    project = fields.ForeignKeyField("models.Project", related_name="tasks", null=True)
    parent_task = fields.ForeignKeyField(
        "models.Task", related_name="subtasks", null=True
    )
    tags = fields.ManyToManyField(
        "models.Tag", related_name="tasks", through="task_tags"
    )

    # Recurrence fields
    is_recurring = fields.BooleanField(default=False)
    recurrence_type = fields.CharEnumField(RecurrenceType, null=True)
    recurrence_data = JSONField(null=True)  # Store specific recurrence details

    # Google Calendar integration
    google_calendar_event_id = fields.CharField(max_length=1024, null=True)

    # Additional metadata
    metadata = JSONField(default=dict)  # For extensibility

    class Meta:
        table = "tasks"

    def __str__(self):
        return f"Task(id={self.id}, title={self.title})"

    def is_overdue(self) -> bool:
        """Check if the task is overdue."""
        if not self.due_date:
            return False
        return (
            datetime.datetime.now() > self.due_date and self.status != TaskStatus.DONE
        )


class TaskTag(Model):
    """Many-to-many through table for task tags."""

    task = fields.ForeignKeyField("models.Task", related_name="task_tags")
    tag = fields.ForeignKeyField("models.Tag", related_name="tag_tasks")

    class Meta:
        table = "task_tags"
        unique_together = (("task_id", "tag_id"),)


class Attachment(BaseModel):
    """File attachments for tasks."""

    task = fields.ForeignKeyField("models.Task", related_name="attachments")
    file_path = fields.CharField(max_length=1024)
    file_name = fields.CharField(max_length=255)
    file_type = fields.CharField(max_length=100)  # MIME type
    file_size = fields.IntField()  # In bytes
    telegram_file_id = fields.CharField(max_length=1024, null=True)

    class Meta:
        table = "attachments"

    def __str__(self):
        return f"Attachment(id={self.id}, file_name={self.file_name})"


# ----- Finance Models -----
class Category(BaseModel):
    """Transaction categories."""

    name = fields.CharField(max_length=100)
    icon = fields.CharField(max_length=50, null=True)  # Emoji or icon name
    color = fields.CharField(max_length=7, default="#4A6FFF")  # Hex color code
    user = fields.ForeignKeyField("models.User", related_name="categories")
    transaction_type = fields.CharEnumField(
        TransactionType, null=True
    )  # Can be null for both income/expense

    class Meta:
        table = "categories"
        unique_together = (("name", "user_id", "transaction_type"),)

    def __str__(self):
        return f"Category(id={self.id}, name={self.name})"


class Transaction(BaseModel):
    """Financial transactions."""

    amount = fields.DecimalField(max_digits=12, decimal_places=2)
    currency = fields.CharField(max_length=3, default="USD")
    type = fields.CharEnumField(TransactionType)
    date = fields.DateField()
    description = fields.TextField(null=True)

    # Relationships
    user = fields.ForeignKeyField("models.User", related_name="transactions")
    category = fields.ForeignKeyField(
        "models.Category", related_name="transactions", null=True
    )
    project = fields.ForeignKeyField(
        "models.Project", related_name="transactions", null=True
    )

    # Additional fields
    is_recurring = fields.BooleanField(default=False)
    recurrence_data = JSONField(null=True)
    metadata = JSONField(default=dict)  # For extensibility

    class Meta:
        table = "transactions"

    def __str__(self):
        return f"Transaction(id={self.id}, amount={self.amount}, type={self.type})"


class Budget(BaseModel):
    """Budget model for financial planning."""

    name = fields.CharField(max_length=255)
    amount = fields.DecimalField(max_digits=12, decimal_places=2)
    currency = fields.CharField(max_length=3, default="USD")
    start_date = fields.DateField()
    end_date = fields.DateField()

    # Relationships
    user = fields.ForeignKeyField("models.User", related_name="budgets")
    category = fields.ForeignKeyField(
        "models.Category", related_name="budgets", null=True
    )
    project = fields.ForeignKeyField(
        "models.Project", related_name="budgets", null=True
    )

    class Meta:
        table = "budgets"

    def __str__(self):
        return f"Budget(id={self.id}, name={self.name}, amount={self.amount})"


# Import all models for Tortoise ORM registration
__all__ = [
    "User",
    "GoogleAuth",
    "Project",
    "ProjectCollaborator",
    "Tag",
    "Task",
    "TaskTag",
    "Attachment",
    "Category",
    "Transaction",
    "Budget",
]
