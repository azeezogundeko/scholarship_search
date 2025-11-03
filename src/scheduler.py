"""Task scheduler for recurring tasks."""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from .task_parser import Task, TaskLoader
from .agent import AutonomousAgent
from .config import config


class TaskScheduler:
    """Scheduler for recurring tasks."""

    def __init__(self, tasks_dir: str = "./tasks"):
        """Initialize task scheduler.

        Args:
            tasks_dir: Directory containing task files
        """
        self.scheduler = AsyncIOScheduler(timezone=config.scheduler_timezone)
        self.task_loader = TaskLoader(tasks_dir)
        self.agent = AutonomousAgent()
        self.scheduled_jobs: Dict[str, str] = {}  # task_id -> job_id

    async def _execute_task(self, task_id: str):
        """Execute a task by ID.

        Args:
            task_id: Task identifier
        """
        print(f"\n[{datetime.now()}] Executing scheduled task: {task_id}")

        try:
            task = self.task_loader.load_task(task_id)
            result = await self.agent.execute_task(task)

            print(f"Task {task_id} completed:")
            print(f"  Success: {result.success}")
            print(f"  Summary: {result.summary}")
            if result.errors:
                print(f"  Errors: {result.errors}")

        except Exception as e:
            print(f"Error executing task {task_id}: {e}")

    def _parse_recurring_schedule(self, recurring: str) -> Optional[IntervalTrigger]:
        """Parse recurring schedule string to IntervalTrigger.

        Args:
            recurring: Schedule string (e.g., 'daily', 'weekly', 'hourly')

        Returns:
            IntervalTrigger or None if invalid
        """
        schedule_map = {
            'hourly': timedelta(hours=1),
            'daily': timedelta(days=1),
            'weekly': timedelta(weeks=1),
            'monthly': timedelta(days=30),
        }

        interval = schedule_map.get(recurring.lower())
        if interval:
            return IntervalTrigger(
                seconds=interval.total_seconds(),
                start_date=datetime.now(),
            )

        return None

    def schedule_task(self, task: Task) -> bool:
        """Schedule a task for recurring execution.

        Args:
            task: Task to schedule

        Returns:
            True if scheduled successfully, False otherwise
        """
        if not task.metadata.recurring and not task.metadata.cron:
            return False

        # Determine trigger
        trigger = None

        if task.metadata.cron:
            # Use cron expression
            trigger = CronTrigger.from_crontab(task.metadata.cron)
        elif task.metadata.recurring:
            # Use recurring schedule
            trigger = self._parse_recurring_schedule(task.metadata.recurring)

        if not trigger:
            print(f"Invalid schedule for task {task.id}")
            return False

        # Schedule the job
        job = self.scheduler.add_job(
            self._execute_task,
            trigger=trigger,
            args=[task.id],
            id=f"task_{task.id}",
            name=task.metadata.title,
            replace_existing=True,
        )

        self.scheduled_jobs[task.id] = job.id
        print(f"Scheduled task: {task.id} ({task.metadata.title})")

        return True

    def load_and_schedule_all(self):
        """Load all recurring tasks and schedule them."""
        recurring_tasks = self.task_loader.get_recurring_tasks()

        scheduled_count = 0
        for task in recurring_tasks:
            if self.schedule_task(task):
                scheduled_count += 1

        print(f"\nScheduled {scheduled_count} recurring tasks")

    def start(self):
        """Start the scheduler."""
        if not self.scheduler.running:
            self.scheduler.start()
            print("Scheduler started")

    def stop(self):
        """Stop the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            print("Scheduler stopped")

    def list_jobs(self):
        """List all scheduled jobs."""
        jobs = self.scheduler.get_jobs()
        if not jobs:
            print("No scheduled jobs")
            return

        print("\nScheduled Jobs:")
        print("-" * 80)
        for job in jobs:
            print(f"  {job.name} (ID: {job.id})")
            print(f"    Next run: {job.next_run_time}")
            print(f"    Trigger: {job.trigger}")
            print()

    async def run_forever(self):
        """Run the scheduler indefinitely."""
        self.start()
        try:
            # Keep the scheduler running
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down scheduler...")
            self.stop()
