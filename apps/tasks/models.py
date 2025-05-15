from typing import Dict, List, Optional, Union, Any
from datetime import datetime, timedelta
from tortoise.exceptions import DoesNotExist

from database.models import (
    Task, Project, Tag, Attachment, 
    TaskPriority, TaskStatus, RecurrenceType,
    User, ProjectCollaborator, UserRole
)

# Task-related functions
async def get_task_by_id(task_id: int) -> Optional[Task]:
    """Get a task by ID."""
    try:
        return await Task.get(id=task_id)
    except DoesNotExist:
        return None

async def get_user_tasks(
    user_id: int,
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    project_id: Optional[int] = None,
    due_date_from: Optional[datetime] = None,
    due_date_to: Optional[datetime] = None,
    tag_ids: Optional[List[int]] = None,
    search_term: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Task]:
    """Get tasks for a user with various filters."""
    try:
        user = await User.get(telegram_id=user_id)
    except DoesNotExist:
        return []
    
    # Start with base query
    query = Task.filter(user=user)
    
    # Apply filters
    if status:
        query = query.filter(status=status)
    
    if priority:
        query = query.filter(priority=priority)
    
    if project_id:
        query = query.filter(project_id=project_id)
    
    if due_date_from:
        query = query.filter(due_date__gte=due_date_from)
    
    if due_date_to:
        query = query.filter(due_date__lte=due_date_to)
    
    if tag_ids:
        # This requires prefetching tags and filtering in Python
        # We'll fetch all and then filter
        pass
    
    if search_term:
        query = query.filter(title__icontains=search_term)
    
    # Order by priority (high to low) and due date (closest first)
    tasks = await query.order_by("-priority", "due_date").offset(offset).limit(limit).prefetch_related("tags", "project")
    
    # Apply tag filter if needed (after fetching)
    if tag_ids:
        filtered_tasks = []
        for task in tasks:
            task_tag_ids = [tag.id for tag in task.tags]
            if any(tid in task_tag_ids for tid in tag_ids):
                filtered_tasks.append(task)
        return filtered_tasks
    
    return tasks

async def create_task(
    user_id: int,
    title: str,
    description: Optional[str] = None,
    priority: TaskPriority = TaskPriority.MEDIUM,
    status: TaskStatus = TaskStatus.TODO,
    due_date: Optional[datetime] = None,
    reminder_time: Optional[datetime] = None,
    project_id: Optional[int] = None,
    parent_task_id: Optional[int] = None,
    tag_ids: Optional[List[int]] = None,
    is_recurring: bool = False,
    recurrence_type: Optional[RecurrenceType] = None,
    recurrence_data: Optional[Dict] = None
) -> Optional[Task]:
    """Create a new task."""
    try:
        user = await User.get(telegram_id=user_id)
    except DoesNotExist:
        return None
    
    # Prepare task data
    task_data = {
        "user": user,
        "title": title,
        "description": description,
        "priority": priority,
        "status": status,
        "due_date": due_date,
        "reminder_time": reminder_time,
        "is_recurring": is_recurring,
        "recurrence_type": recurrence_type,
        "recurrence_data": recurrence_data
    }
    
    # Add project if provided
    if project_id:
        try:
            project = await Project.get(id=project_id)
            task_data["project"] = project
        except DoesNotExist:
            pass
    
    # Add parent task if provided
    if parent_task_id:
        try:
            parent_task = await Task.get(id=parent_task_id)
            task_data["parent_task"] = parent_task
        except DoesNotExist:
            pass
    
    # Create the task
    task = await Task.create(**task_data)
    
    # Add tags if provided
    if tag_ids:
        for tag_id in tag_ids:
            try:
                tag = await Tag.get(id=tag_id)
                await task.tags.add(tag)
            except DoesNotExist:
                pass
    
    return task

async def update_task(
    task_id: int,
    user_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    priority: Optional[TaskPriority] = None,
    status: Optional[TaskStatus] = None,
    due_date: Optional[datetime] = None,
    reminder_time: Optional[datetime] = None,
    project_id: Optional[int] = None,
    parent_task_id: Optional[int] = None,
    tag_ids: Optional[List[int]] = None,
    is_recurring: Optional[bool] = None,
    recurrence_type: Optional[RecurrenceType] = None,
    recurrence_data: Optional[Dict] = None,
    completed_at: Optional[datetime] = None
) -> Optional[Task]:
    """Update an existing task."""
    # Get task and verify ownership
    task = await get_task_by_id(task_id)
    if not task or task.user.telegram_id != user_id:
        # Check if user has access through project collaboration
        if task and task.project:
            try:
                user = await User.get(telegram_id=user_id)
                collaboration = await ProjectCollaborator.get(
                    project=task.project, 
                    user=user
                )
                # Check if user has edit permissions
                if not UserRole.can_edit(collaboration.role):
                    return None
            except DoesNotExist:
                return None
        else:
            return None
    
    # Update fields if provided
    if title is not None:
        task.title = title
    
    if description is not None:
        task.description = description
    
    if priority is not None:
        task.priority = priority
    
    if status is not None:
        task.status = status
        # If task is marked as done, set completed_at
        if status == TaskStatus.DONE and task.completed_at is None:
            task.completed_at = datetime.now()
        # If task is no longer done, clear completed_at
        elif status != TaskStatus.DONE and task.completed_at is not None:
            task.completed_at = None
    
    if due_date is not None:
        task.due_date = due_date
    
    if reminder_time is not None:
        task.reminder_time = reminder_time
    
    if project_id is not None:
        try:
            if project_id == 0:  # Special case to remove project
                task.project = None
            else:
                project = await Project.get(id=project_id)
                task.project = project
        except DoesNotExist:
            pass
    
    if parent_task_id is not None:
        try:
            if parent_task_id == 0:  # Special case to remove parent task
                task.parent_task = None
            else:
                parent_task = await Task.get(id=parent_task_id)
                # Avoid circular references
                if parent_task.id != task.id:
                    task.parent_task = parent_task
        except DoesNotExist:
            pass
    
    if is_recurring is not None:
        task.is_recurring = is_recurring
    
    if recurrence_type is not None:
        task.recurrence_type = recurrence_type
    
    if recurrence_data is not None:
        task.recurrence_data = recurrence_data
    
    if completed_at is not None:
        task.completed_at = completed_at
        # If completion time is set, ensure status is DONE
        if completed_at and task.status != TaskStatus.DONE:
            task.status = TaskStatus.DONE
    
    # Save updated task
    await task.save()
    
    # Update tags if provided
    if tag_ids is not None:
        # Clear existing tags
        await task.tags.clear()
        # Add new tags
        for tag_id in tag_ids:
            try:
                tag = await Tag.get(id=tag_id)
                await task.tags.add(tag)
            except DoesNotExist:
                pass
    
    # Refresh to get updated relationships
    await task.fetch_related("tags", "project")
    
    return task

async def delete_task(task_id: int, user_id: int) -> bool:
    """Delete a task."""
    # Get task and verify ownership
    task = await get_task_by_id(task_id)
    if not task or task.user.telegram_id != user_id:
        # Check if user has access through project collaboration
        if task and task.project:
            try:
                user = await User.get(telegram_id=user_id)
                collaboration = await ProjectCollaborator.get(
                    project=task.project, 
                    user=user
                )
                # Check if user has delete permissions
                if not UserRole.can_delete(collaboration.role):
                    return False
            except DoesNotExist:
                return False
        else:
            return False
    
    # Delete task
    await task.delete()
    return True

async def complete_task(task_id: int, user_id: int) -> Optional[Task]:
    """Mark a task as completed."""
    return await update_task(
        task_id=task_id,
        user_id=user_id,
        status=TaskStatus.DONE,
        completed_at=datetime.now()
    )

async def get_overdue_tasks(user_id: int) -> List[Task]:
    """Get overdue tasks for a user."""
    try:
        user = await User.get(telegram_id=user_id)
    except DoesNotExist:
        return []
    
    now = datetime.now()
    return await Task.filter(
        user=user,
        status=TaskStatus.TODO,
        due_date__lt=now
    ).order_by("due_date").prefetch_related("tags", "project")

async def get_upcoming_tasks(user_id: int, days: int = 7) -> List[Task]:
    """Get upcoming tasks due in the next N days."""
    try:
        user = await User.get(telegram_id=user_id)
    except DoesNotExist:
        return []
    
    now = datetime.now()
    end_date = now + timedelta(days=days)
    
    return await Task.filter(
        user=user,
        status=TaskStatus.TODO,
        due_date__gte=now,
        due_date__lte=end_date
    ).order_by("due_date").prefetch_related("tags", "project")

# Project-related functions
async def get_user_projects(user_id: int, include_archived: bool = False) -> List[Project]:
    """Get projects for a user."""
    try:
        user = await User.get(telegram_id=user_id)
    except DoesNotExist:
        return []
    
    # Get projects owned by user
    query = Project.filter(owner=user)
    if not include_archived:
        query = query.filter(is_archived=False)
    
    owned_projects = await query.all()
    
    # Get collaborative projects
    query = user.collaborative_projects.all()
    if not include_archived:
        query = query.filter(is_archived=False)
    
    collaborative_projects = await query
    
    # Combine both lists
    return owned_projects + collaborative_projects

async def create_project(
    user_id: int,
    name: str,
    description: Optional[str] = None,
    color: str = "#4A6FFF",
    icon: Optional[str] = None,
    budget: Optional[float] = None,
    currency: str = "USD"
) -> Optional[Project]:
    """Create a new project."""
    try:
        user = await User.get(telegram_id=user_id)
    except DoesNotExist:
        return None
    
    return await Project.create(
        owner=user,
        name=name,
        description=description,
        color=color,
        icon=icon,
        budget=budget,
        currency=currency
    )

async def update_project(
    project_id: int,
    user_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    color: Optional[str] = None,
    icon: Optional[str] = None,
    budget: Optional[float] = None,
    currency: Optional[str] = None,
    is_archived: Optional[bool] = None
) -> Optional[Project]:
    """Update an existing project."""
    # Get project
    try:
        project = await Project.get(id=project_id)
    except DoesNotExist:
        return None
    
    # Verify ownership or admin access
    try:
        user = await User.get(telegram_id=user_id)
        
        # Check if user is owner
        is_owner = project.owner_id == user.id
        
        # If not owner, check if user is admin
        if not is_owner:
            try:
                collaboration = await ProjectCollaborator.get(
                    project=project,
                    user=user
                )
                if not UserRole.can_edit(collaboration.role):
                    return None
            except DoesNotExist:
                return None
    except DoesNotExist:
        return None
    
    # Update fields if provided
    if name is not None:
        project.name = name
    
    if description is not None:
        project.description = description
    
    if color is not None:
        project.color = color
    
    if icon is not None:
        project.icon = icon
    
    if budget is not None:
        project.budget = budget
    
    if currency is not None:
        project.currency = currency
    
    if is_archived is not None:
        project.is_archived = is_archived
    
    # Save updated project
    await project.save()
    return project

async def delete_project(project_id: int, user_id: int) -> bool:
    """Delete a project."""
    # Get project
    try:
        project = await Project.get(id=project_id)
    except DoesNotExist:
        return False
    
    # Verify ownership
    try:
        user = await User.get(telegram_id=user_id)
        if project.owner_id != user.id:
            return False
    except DoesNotExist:
        return False
    
    # Delete project (this will also delete related tasks)
    await project.delete()
    return True

async def add_project_collaborator(
    project_id: int,
    owner_id: int,
    collaborator_telegram_id: int,
    role: UserRole = UserRole.COLLABORATOR
) -> bool:
    """Add a collaborator to a project."""
    # Get project
    try:
        project = await Project.get(id=project_id)
    except DoesNotExist:
        return False
    
    # Verify ownership or admin access
    try:
        owner = await User.get(telegram_id=owner_id)
        
        # Check if user is owner
        is_owner = project.owner_id == owner.id
        
        # If not owner, check if user is admin
        if not is_owner:
            try:
                collaboration = await ProjectCollaborator.get(
                    project=project,
                    user=owner
                )
                if not UserRole.can_manage_users(collaboration.role):
                    return False
            except DoesNotExist:
                return False
    except DoesNotExist:
        return False
    
    # Get collaborator user
    try:
        collaborator = await User.get(telegram_id=collaborator_telegram_id)
    except DoesNotExist:
        return False
    
    # Add collaborator
    try:
        await ProjectCollaborator.create(
            project=project,
            user=collaborator,
            role=role
        )
        return True
    except Exception:
        # Might be a duplicate, try to update instead
        try:
            collaboration = await ProjectCollaborator.get(
                project=project,
                user=collaborator
            )
            collaboration.role = role
            await collaboration.save()
            return True
        except Exception:
            return False

# Tag-related functions
async def get_user_tags(user_id: int) -> List[Tag]:
    """Get tags for a user."""
    try:
        user = await User.get(telegram_id=user_id)
    except DoesNotExist:
        return []
    
    return await Tag.filter(user=user).all()

async def create_tag(
    user_id: int,
    name: str,
    color: str = "#4A6FFF"
) -> Optional[Tag]:
    """Create a new tag."""
    try:
        user = await User.get(telegram_id=user_id)
    except DoesNotExist:
        return None
    
    # Check if tag already exists
    existing_tag = await Tag.filter(user=user, name=name).first()
    if existing_tag:
        return existing_tag
    
    return await Tag.create(
        user=user,
        name=name,
        color=color
    )

async def update_tag(
    tag_id: int,
    user_id: int,
    name: Optional[str] = None,
    color: Optional[str] = None
) -> Optional[Tag]:
    """Update an existing tag."""
    # Get tag
    try:
        tag = await Tag.get(id=tag_id)
    except DoesNotExist:
        return None
    
    # Verify ownership
    try:
        user = await User.get(telegram_id=user_id)
        if tag.user_id != user.id:
            return None
    except DoesNotExist:
        return None
    
    # Update fields if provided
    if name is not None:
        tag.name = name
    
    if color is not None:
        tag.color = color
    
    # Save updated tag
    await tag.save()
    return tag

async def delete_tag(tag_id: int, user_id: int) -> bool:
    """Delete a tag."""
    # Get tag
    try:
        tag = await Tag.get(id=tag_id)
    except DoesNotExist:
        return False
    
    # Verify ownership
    try:
        user = await User.get(telegram_id=user_id)
        if tag.user_id != user.id:
            return False
    except DoesNotExist:
        return False
    
    # Delete tag
    await tag.delete()
    return True

# Attachment-related functions
async def add_attachment(
    task_id: int,
    user_id: int,
    file_path: str,
    file_name: str,
    file_type: str,
    file_size: int,
    telegram_file_id: Optional[str] = None
) -> Optional[Attachment]:
    """Add an attachment to a task."""
    # Get task and verify ownership
    task = await get_task_by_id(task_id)
    if not task or task.user.telegram_id != user_id:
        # Check if user has access through project collaboration
        if task and task.project:
            try:
                user = await User.get(telegram_id=user_id)
                collaboration = await ProjectCollaborator.get(
                    project=task.project, 
                    user=user
                )
                # Check if user has edit permissions
                if not UserRole.can_edit(collaboration.role):
                    return None
            except DoesNotExist:
                return None
        else:
            return None
    
    # Create attachment
    return await Attachment.create(
        task=task,
        file_path=file_path,
        file_name=file_name,
        file_type=file_type,
        file_size=file_size,
        telegram_file_id=telegram_file_id
    )

async def get_task_attachments(task_id: int, user_id: int) -> List[Attachment]:
    """Get attachments for a task."""
    # Get task and verify ownership
    task = await get_task_by_id(task_id)
    if not task or task.user.telegram_id != user_id:
        # Check if user has access through project collaboration
        if task and task.project:
            try:
                user = await User.get(telegram_id=user_id)
                collaboration = await ProjectCollaborator.get(
                    project=task.project, 
                    user=user
                )
                # Even viewers can see attachments
            except DoesNotExist:
                return []
        else:
            return []
    
    return await Attachment.filter(task=task).all()

async def delete_attachment(attachment_id: int, user_id: int) -> bool:
    """Delete an attachment."""
    try:
        attachment = await Attachment.get(id=attachment_id).prefetch_related("task__user")
    except DoesNotExist:
        return False
    
    # Verify ownership
    if attachment.task.user.telegram_id != user_id:
        # Check if user has access through project collaboration
        if attachment.task.project:
            try:
                user = await User.get(telegram_id=user_id)
                collaboration = await ProjectCollaborator.get(
                    project=attachment.task.project, 
                    user=user
                )
                # Check if user has delete permissions
                if not UserRole.can_delete(collaboration.role):
                    return False
            except DoesNotExist:
                return False
        else:
            return False
    
    # Delete attachment
    await attachment.delete()
    return True