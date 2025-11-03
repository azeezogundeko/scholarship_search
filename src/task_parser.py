"""Task file parser for Markdown files with YAML frontmatter."""

import frontmatter
from pathlib import Path
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime


class TaskMetadata(BaseModel):
    """Metadata for a task from YAML frontmatter."""

    title: str = Field(description="Task title")
    description: Optional[str] = Field(default=None, description="Task description")

    # Scheduling
    recurring: Optional[str] = Field(default=None, description="Recurring schedule (daily, weekly, monthly, etc.)")
    cron: Optional[str] = Field(default=None, description="Cron expression for advanced scheduling")

    # Output destination
    output_type: str = Field(default="sqlite", description="Output type: google_sheets, sqlite, faiss, or multiple")
    sheet_id: Optional[str] = Field(default=None, description="Google Sheets ID")
    sheet_name: Optional[str] = Field(default=None, description="Sheet tab name")
    db_table: Optional[str] = Field(default=None, description="Database table name")

    # Attachments
    attachments: List[str] = Field(default_factory=list, description="List of attachment file paths (e.g., CV)")

    # Search configuration
    max_results: int = Field(default=20, description="Maximum number of results to collect")
    search_depth: int = Field(default=1, description="How many levels deep to crawl links")

    # Custom fields
    custom: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata fields")


class Task(BaseModel):
    """Represents a task to be executed by the autonomous agent."""

    id: str = Field(description="Unique task identifier (filename without extension)")
    file_path: Path = Field(description="Path to the task file")
    metadata: TaskMetadata = Field(description="Task metadata from frontmatter")
    content: str = Field(description="Task description and instructions")
    attachments_data: Dict[str, bytes] = Field(default_factory=dict, description="Loaded attachment data")
    created_at: datetime = Field(default_factory=datetime.now)

    @classmethod
    def from_file(cls, file_path: Path) -> "Task":
        """Parse a task from a Markdown file with YAML frontmatter.

        Args:
            file_path: Path to the task Markdown file

        Returns:
            Parsed Task object
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)

        # Extract metadata
        metadata_dict = dict(post.metadata)
        if 'title' not in metadata_dict:
            metadata_dict['title'] = file_path.stem

        metadata = TaskMetadata(**metadata_dict)

        # Load attachments
        attachments_data = {}
        if metadata.attachments:
            task_dir = file_path.parent
            for attachment_path in metadata.attachments:
                full_path = task_dir / attachment_path
                if full_path.exists():
                    with open(full_path, 'rb') as f:
                        attachments_data[attachment_path] = f.read()

        return cls(
            id=file_path.stem,
            file_path=file_path,
            metadata=metadata,
            content=post.content,
            attachments_data=attachments_data
        )

    def get_attachment_text(self, attachment_name: str) -> Optional[str]:
        """Get attachment content as text (for text files, CVs, etc.)."""
        if attachment_name not in self.attachments_data:
            return None

        try:
            # Try to decode as text
            return self.attachments_data[attachment_name].decode('utf-8')
        except UnicodeDecodeError:
            # For binary files, return None or implement PDF/DOCX parsing
            return None

    def to_dict(self) -> dict:
        """Convert task to dictionary for serialization."""
        return {
            "id": self.id,
            "title": self.metadata.title,
            "description": self.metadata.description,
            "content": self.content,
            "metadata": self.metadata.model_dump(),
            "created_at": self.created_at.isoformat(),
        }


class TaskLoader:
    """Loads and manages tasks from the tasks directory."""

    def __init__(self, tasks_dir: Path = Path("./tasks")):
        """Initialize task loader.

        Args:
            tasks_dir: Directory containing task files
        """
        self.tasks_dir = tasks_dir
        self.tasks_dir.mkdir(parents=True, exist_ok=True)

    def load_task(self, task_id: str) -> Task:
        """Load a specific task by ID.

        Args:
            task_id: Task identifier (filename without extension)

        Returns:
            Loaded Task object
        """
        task_file = self.tasks_dir / f"{task_id}.md"
        if not task_file.exists():
            raise FileNotFoundError(f"Task file not found: {task_file}")

        return Task.from_file(task_file)

    def load_all_tasks(self) -> List[Task]:
        """Load all tasks from the tasks directory.

        Returns:
            List of loaded Task objects
        """
        tasks = []
        for task_file in self.tasks_dir.glob("*.md"):
            try:
                task = Task.from_file(task_file)
                tasks.append(task)
            except Exception as e:
                print(f"Error loading task {task_file}: {e}")

        return tasks

    def get_recurring_tasks(self) -> List[Task]:
        """Get all tasks that have recurring schedules.

        Returns:
            List of recurring Task objects
        """
        all_tasks = self.load_all_tasks()
        return [
            task for task in all_tasks
            if task.metadata.recurring or task.metadata.cron
        ]
