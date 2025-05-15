from typing import Dict, List, Optional, Union, Any
import logging
from datetime import datetime, timedelta
import json

from apps.tasks.models import (
    get_task_by_id, get_user_tasks, create_task, update_task, delete_task,
    complete_task, get_overdue_tasks, get_upcoming_tasks,
    get_user_projects, create_project, update_project, delete_project, add_project_collaborator,
    get_user_tags, create_tag, update_tag, delete_tag,
    add_attachment, get_task_attachments, delete_attachment
)
from database.models import (
    User, Task, Project, Tag, Attachment,
    TaskPriority, TaskStatus, RecurrenceType, UserRole
)

# Setup logger
logger = logging.getLogger("tasks")

class TaskService:
    """Service for managing tasks."""
    
    @staticmethod
    async def get_task(task_id: int, user_id: int) -> Optional[Task]:
        """Get a task by ID, ensuring the user has access."""
        task = await get_task_by_id(task_id)
        if not task:
            return None
            
        # Check if the task belongs to the user
        if task.user.telegram_id == user_id:
            return task
            
        # Check if the user has access through project
        if task.project:
            try:
                user = await User.get(telegram_id=user_id)
                # Check if user is project owner
                if task.project.owner_id == user.id:
                    return task
                    
                # Check if user is a collaborator
                collaborator = await task.project.project_collaborators.filter(user=user).first()
                if collaborator:
                    return task
            except Exception as e:
                logger.error(f"Error checking task access: {e}")
                
        return None
    
    @staticmethod
    async def get_tasks(
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
        """Get tasks for a user with filters."""
        logger.info(f"Getting tasks for user {user_id} with filters: status={status}, project={project_id}")
        return await get_user_tasks(
            user_id=user_id,
            status=status,
            priority=priority,
            project_id=project_id,
            due_date_from=due_date_from,
            due_date_to=due_date_to,
            tag_ids=tag_ids,
            search_term=search_term,
            limit=limit,
            offset=offset
        )
    
    @staticmethod
    async def create_task(
        user_id: int,
        title: str,
        **kwargs
    ) -> Optional[Task]:
        """Create a new task."""
        logger.info(f"Creating task for user {user_id}: {title}")
        return await create_task(user_id=user_id, title=title, **kwargs)
    
    @staticmethod
    async def update_task(
        task_id: int,
        user_id: int,
        **kwargs
    ) -> Optional[Task]:
        """Update an existing task."""
        logger.info(f"Updating task {task_id} for user {user_id}")
        return await update_task(task_id=task_id, user_id=user_id, **kwargs)
    
    @staticmethod
    async def delete_task(task_id: int, user_id: int) -> bool:
        """Delete a task."""
        logger.info(f"Deleting task {task_id} for user {user_id}")
        return await delete_task(task_id=task_id, user_id=user_id)
    
    @staticmethod
    async def complete_task(task_id: int, user_id: int) -> Optional[Task]:
        """Mark a task as completed."""
        logger.info(f"Completing task {task_id} for user {user_id}")
        return await complete_task(task_id=task_id, user_id=user_id)
    
    @staticmethod
    async def get_overdue_tasks(user_id: int) -> List[Task]:
        """Get overdue tasks for user."""
        logger.info(f"Getting overdue tasks for user {user_id}")
        return await get_overdue_tasks(user_id=user_id)
    
    @staticmethod
    async def get_upcoming_tasks(user_id: int, days: int = 7) -> List[Task]:
        """Get upcoming tasks for the next days."""
        logger.info(f"Getting upcoming tasks for user {user_id} for next {days} days")
        return await get_upcoming_tasks(user_id=user_id, days=days)
    
    @staticmethod
    async def get_task_with_subtasks(task_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """Get a task with its subtasks."""
        task = await TaskService.get_task(task_id=task_id, user_id=user_id)
        if not task:
            return None
            
        # Get subtasks
        subtasks = await Task.filter(parent_task_id=task_id).all()
        
        # Format result
        result = {
            "task": task,
            "subtasks": subtasks
        }
        
        return result
    
    @staticmethod
    async def parse_natural_language(user_id: int, text: str) -> Optional[Task]:
        """Parse natural language input to create a task."""
        logger.info(f"Parsing natural language for user {user_id}: {text}")
        
        # This is a basic implementation that could be expanded with NLP
        # For now just do some simple parsing
        
        title = text
        description = None
        due_date = None
        priority = TaskPriority.MEDIUM
        
        # Extract date if text contains "tomorrow", "today", etc.
        lower_text = text.lower()
        
        # Check for priority keywords
        if "urgent" in lower_text or "high priority" in lower_text:
            priority = TaskPriority.URGENT
        elif "important" in lower_text:
            priority = TaskPriority.HIGH
        elif "low priority" in lower_text:
            priority = TaskPriority.LOW
            
        # Check for date keywords
        now = datetime.now()
        if "today" in lower_text:
            due_date = now.replace(hour=23, minute=59, second=59)
        elif "tomorrow" in lower_text:
            due_date = (now + timedelta(days=1)).replace(hour=23, minute=59, second=59)
        elif "next week" in lower_text:
            due_date = (now + timedelta(days=7)).replace(hour=23, minute=59, second=59)
            
        # Extract potential title and description
        if ":" in text:
            parts = text.split(":", 1)
            title = parts[0].strip()
            description = parts[1].strip()
            
        # Create the task
        return await create_task(
            user_id=user_id,
            title=title,
            description=description,
            priority=priority,
            due_date=due_date
        )
    
    @staticmethod
    async def set_google_calendar_id(task_id: int, user_id: int, calendar_event_id: str) -> Optional[Task]:
        """Set Google Calendar event ID for a task."""
        task = await get_task_by_id(task_id)
        if not task or task.user.telegram_id != user_id:
            return None
            
        task.google_calendar_event_id = calendar_event_id
        await task.save()
        return task
    
    @staticmethod
    async def get_tasks_by_google_calendar_id(user_id: int, calendar_event_id: str) -> List[Task]:
        """Get tasks with the given Google Calendar event ID."""
        try:
            user = await User.get(telegram_id=user_id)
            return await Task.filter(user=user, google_calendar_event_id=calendar_event_id).all()
        except Exception as e:
            logger.error(f"Error getting tasks by calendar ID: {e}")
            return []


class ProjectService:
    """Service for managing projects."""
    
    @staticmethod
    async def get_project(project_id: int, user_id: int) -> Optional[Project]:
        """Get a project, ensuring the user has access."""
        try:
            project = await Project.get(id=project_id)
            user = await User.get(telegram_id=user_id)
            
            # Check if user is owner
            if project.owner_id == user.id:
                return project
                
            # Check if user is collaborator
            collaboration = await project.project_collaborators.filter(user=user).first()
            if collaboration:
                return project
                
            return None
        except Exception as e:
            logger.error(f"Error getting project: {e}")
            return None
    
    @staticmethod
    async def get_projects(user_id: int, include_archived: bool = False) -> List[Project]:
        """Get all projects accessible to the user."""
        logger.info(f"Getting projects for user {user_id}")
        return await get_user_projects(user_id=user_id, include_archived=include_archived)
    
    @staticmethod
    async def create_project(user_id: int, name: str, **kwargs) -> Optional[Project]:
        """Create a new project."""
        logger.info(f"Creating project for user {user_id}: {name}")
        return await create_project(user_id=user_id, name=name, **kwargs)
    
    @staticmethod
    async def update_project(project_id: int, user_id: int, **kwargs) -> Optional[Project]:
        """Update an existing project."""
        logger.info(f"Updating project {project_id} for user {user_id}")
        return await update_project(project_id=project_id, user_id=user_id, **kwargs)
    
    @staticmethod
    async def delete_project(project_id: int, user_id: int) -> bool:
        """Delete a project."""
        logger.info(f"Deleting project {project_id} for user {user_id}")
        return await delete_project(project_id=project_id, user_id=user_id)
    
    @staticmethod
    async def add_collaborator(
        project_id: int, 
        owner_id: int, 
        collaborator_id: int, 
        role: UserRole = UserRole.COLLABORATOR
    ) -> bool:
        """Add a collaborator to a project."""
        logger.info(f"Adding collaborator {collaborator_id} to project {project_id}")
        return await add_project_collaborator(
            project_id=project_id,
            owner_id=owner_id, 
            collaborator_telegram_id=collaborator_id,
            role=role
        )
    
    @staticmethod
    async def get_project_with_tasks(project_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """Get a project with its tasks."""
        project = await ProjectService.get_project(project_id=project_id, user_id=user_id)
        if not project:
            return None
            
        # Get tasks for this project
        try:
            user = await User.get(telegram_id=user_id)
            tasks = await Task.filter(project=project, user=user).all()
            
            # Format result
            result = {
                "project": project,
                "tasks": tasks
            }
            
            return result
        except Exception as e:
            logger.error(f"Error getting project tasks: {e}")
            return {"project": project, "tasks": []}


class TagService:
    """Service for managing tags."""
    
    @staticmethod
    async def get_tags(user_id: int) -> List[Tag]:
        """Get all tags for the user."""
        logger.info(f"Getting tags for user {user_id}")
        return await get_user_tags(user_id=user_id)
    
    @staticmethod
    async def create_tag(user_id: int, name: str, color: str = "#4A6FFF") -> Optional[Tag]:
        """Create a new tag."""
        logger.info(f"Creating tag for user {user_id}: {name}")
        return await create_tag(user_id=user_id, name=name, color=color)
    
    @staticmethod
    async def update_tag(tag_id: int, user_id: int, **kwargs) -> Optional[Tag]:
        """Update an existing tag."""
        logger.info(f"Updating tag {tag_id} for user {user_id}")
        return await update_tag(tag_id=tag_id, user_id=user_id, **kwargs)
    
    @staticmethod
    async def delete_tag(tag_id: int, user_id: int) -> bool:
        """Delete a tag."""
        logger.info(f"Deleting tag {tag_id} for user {user_id}")
        return await delete_tag(tag_id=tag_id, user_id=user_id)
    
    @staticmethod
    async def get_tasks_by_tag(tag_id: int, user_id: int) -> List[Task]:
        """Get all tasks with a specific tag."""
        logger.info(f"Getting tasks with tag {tag_id} for user {user_id}")
        try:
            user = await User.get(telegram_id=user_id)
            tag = await Tag.get(id=tag_id, user=user)
            return await tag.tasks.all()
        except Exception as e:
            logger.error(f"Error getting tasks by tag: {e}")
            return []


class AttachmentService:
    """Service for managing task attachments."""
    
    @staticmethod
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
        logger.info(f"Adding attachment to task {task_id}: {file_name}")
        return await add_attachment(
            task_id=task_id,
            user_id=user_id,
            file_path=file_path,
            file_name=file_name,
            file_type=file_type,
            file_size=file_size,
            telegram_file_id=telegram_file_id
        )
    
    @staticmethod
    async def get_attachments(task_id: int, user_id: int) -> List[Attachment]:
        """Get all attachments for a task."""
        logger.info(f"Getting attachments for task {task_id}")
        return await get_task_attachments(task_id=task_id, user_id=user_id)
    
    @staticmethod
    async def delete_attachment(attachment_id: int, user_id: int) -> bool:
        """Delete an attachment."""
        logger.info(f"Deleting attachment {attachment_id}")
        return await delete_attachment(attachment_id=attachment_id, user_id=user_id)