import asyncio
from typing import Any, Callable, Dict, List, Optional, Union
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.memory import MemoryJobStore
import logging

from config.settings import SETTINGS

logger = logging.getLogger("scheduler")

class BotScheduler:
    """A singleton scheduler for the bot's scheduled tasks."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BotScheduler, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        jobstores = {
            'default': MemoryJobStore()
        }
        
        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            timezone=SETTINGS["scheduler"]["timezone"],
            job_defaults=SETTINGS["scheduler"]["job_defaults"]
        )
        
        self._initialized = True
        self._active = False
    
    async def start(self):
        """Start the scheduler."""
        if not self._active:
            self.scheduler.start()
            self._active = True
            logger.info("Scheduler started")
    
    async def shutdown(self):
        """Shutdown the scheduler."""
        if self._active:
            self.scheduler.shutdown()
            self._active = False
            logger.info("Scheduler shutdown")
    
    def add_job(self, 
                func: Callable, 
                trigger: Union[str, DateTrigger, IntervalTrigger, CronTrigger], 
                **kwargs) -> str:
        """Add a job to the scheduler."""
        job = self.scheduler.add_job(func, trigger, **kwargs)
        logger.info(f"Added job {job.id} with trigger {trigger}")
        return job.id
    
    def add_reminder(self, 
                    func: Callable, 
                    run_date: str, 
                    user_id: int, 
                    task_id: int, 
                    **kwargs) -> str:
        """Add a task reminder."""
        job_id = f"reminder_{user_id}_{task_id}"
        job = self.scheduler.add_job(
            func, 
            'date', 
            run_date=run_date, 
            id=job_id, 
            replace_existing=True,
            kwargs={'user_id': user_id, 'task_id': task_id, **kwargs}
        )
        logger.info(f"Added reminder {job.id} for user {user_id}, task {task_id} at {run_date}")
        return job.id
    
    def add_recurring_task(self, 
                          func: Callable, 
                          task_id: int, 
                          user_id: int, 
                          cron_expression: str, 
                          **kwargs) -> str:
        """Add a recurring task using cron expression."""
        job_id = f"recurring_{user_id}_{task_id}"
        job = self.scheduler.add_job(
            func, 
            CronTrigger.from_crontab(cron_expression), 
            id=job_id, 
            replace_existing=True,
            kwargs={'user_id': user_id, 'task_id': task_id, **kwargs}
        )
        logger.info(f"Added recurring task {job.id} for user {user_id}, task {task_id} with cron {cron_expression}")
        return job.id
    
    def add_daily_summary(self, 
                         func: Callable, 
                         user_id: int, 
                         time: str, 
                         **kwargs) -> str:
        """Add a daily summary job at specified time."""
        job_id = f"summary_{user_id}"
        hour, minute = map(int, time.split(':'))
        job = self.scheduler.add_job(
            func, 
            'cron', 
            hour=hour, 
            minute=minute, 
            id=job_id, 
            replace_existing=True,
            kwargs={'user_id': user_id, **kwargs}
        )
        logger.info(f"Added daily summary {job.id} for user {user_id} at {time}")
        return job.id
    
    def remove_job(self, job_id: str) -> bool:
        """Remove a job by ID."""
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed job {job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove job {job_id}: {e}")
            return False
    
    def get_user_jobs(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all jobs for a specific user."""
        jobs = []
        for job in self.scheduler.get_jobs():
            # Check if the job is for this user
            if hasattr(job, 'kwargs') and job.kwargs.get('user_id') == user_id:
                jobs.append({
                    'id': job.id,
                    'name': job.name,
                    'next_run_time': job.next_run_time,
                    'trigger': str(job.trigger)
                })
        return jobs

# Singleton instance
scheduler = BotScheduler()