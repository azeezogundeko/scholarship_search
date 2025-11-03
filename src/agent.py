"""Autonomous browser agent with PydanticAI."""

import asyncio
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from .config import config
from .task_parser import Task
from .tools.crawl4ai_tool import Crawl4AITool, CrawlResult
from .tools.search_tools import UnifiedSearchTool, SearchResult
from .tools.extraction_tools import BeautifulSoupTool
from .storage.google_sheets import GoogleSheetsStorage
from .storage.sqlite_storage import SQLiteStorage
from .storage.faiss_storage import FAISSStorage


@dataclass
class AgentDependencies:
    """Dependencies injected into the agent for tool execution."""

    task: Task
    crawl_tool: Crawl4AITool
    search_tool: UnifiedSearchTool
    extraction_tool: BeautifulSoupTool
    sheets_storage: Optional[GoogleSheetsStorage]
    sqlite_storage: SQLiteStorage
    faiss_storage: FAISSStorage


class ActionPlan(BaseModel):
    """A plan for executing a task."""

    steps: List[str] = Field(description="List of steps to execute")
    rationale: str = Field(description="Why this plan makes sense")


class TaskResult(BaseModel):
    """Result from executing a task."""

    success: bool = Field(description="Whether the task completed successfully")
    summary: str = Field(description="Summary of what was accomplished")
    results_count: int = Field(description="Number of results found/saved")
    storage_locations: List[str] = Field(description="Where results were saved")
    errors: List[str] = Field(default_factory=list, description="Any errors encountered")


# System prompt for the autonomous agent
SYSTEM_PROMPT = """You are an autonomous web research agent with full reasoning and decision-making capabilities.

Your role is to:
1. Understand the task requirements and any attached data (like CVs, resumes, etc.)
2. Create your own execution plan - decide what to search, which pages to visit, how to extract data
3. Use available tools to search the web, crawl pages, and extract structured information
4. Follow links and navigate to next pages when needed to gather complete data
5. Rank and filter results based on relevance to the task
6. Save structured results to the configured destination (Google Sheets, SQLite, or FAISS)

You have access to these tools:
- web_search: Search using Google or Brave Search APIs
- crawl_webpage: Crawl and extract content from a URL using Crawl4AI
- extract_data: Extract structured data using CSS selectors
- save_to_sheets: Save results to Google Sheets
- save_to_sqlite: Save results to SQLite database
- save_to_faiss: Save results to FAISS vector store for semantic search

Important guidelines:
- Be autonomous: Don't ask for clarification, make intelligent decisions
- Be thorough: Follow links, check multiple pages if needed
- Be smart: Filter irrelevant results, focus on quality over quantity
- Be structured: Always save results in a clear, organized format
- Provide clear reasoning: Explain your decisions in the final summary

When given a task, first analyze what needs to be done, then execute autonomously."""


# Create the agent
autonomous_agent = Agent(
    config.ai_model,
    deps_type=AgentDependencies,
    instructions=SYSTEM_PROMPT,
    retries=2,
)


@autonomous_agent.tool
async def web_search(
    ctx: RunContext[AgentDependencies],
    query: str,
    num_results: int = 10,
) -> List[Dict[str, str]]:
    """Search the web using available search APIs.

    Args:
        query: Search query
        num_results: Number of results to return

    Returns:
        List of search results with title, url, and snippet
    """
    results = ctx.deps.search_tool.search(query, num_results)
    return [
        {
            "title": r.title,
            "url": r.url,
            "snippet": r.snippet,
            "source": r.source,
        }
        for r in results
    ]


@autonomous_agent.tool
async def crawl_webpage(
    ctx: RunContext[AgentDependencies],
    url: str,
) -> Dict[str, Any]:
    """Crawl a webpage and extract its content as Markdown.

    Args:
        url: URL to crawl

    Returns:
        Dictionary with url, title, markdown content, and links
    """
    result = await ctx.deps.crawl_tool.crawl_url(url)
    return {
        "url": result.url,
        "title": result.title,
        "content": result.markdown[:5000],  # Limit content size
        "links": result.links[:20],  # Limit number of links
        "success": result.success,
        "error": result.error,
    }


@autonomous_agent.tool
async def crawl_multiple_pages(
    ctx: RunContext[AgentDependencies],
    urls: List[str],
) -> List[Dict[str, Any]]:
    """Crawl multiple webpages concurrently.

    Args:
        urls: List of URLs to crawl

    Returns:
        List of crawl results
    """
    results = await ctx.deps.crawl_tool.crawl_multiple(urls[:10])  # Limit to 10 URLs
    return [
        {
            "url": r.url,
            "title": r.title,
            "content": r.markdown[:3000],  # Smaller limit for multiple pages
            "success": r.success,
        }
        for r in results
    ]


@autonomous_agent.tool
def save_to_sheets(
    ctx: RunContext[AgentDependencies],
    data: List[Dict[str, Any]],
    sheet_name: Optional[str] = None,
) -> str:
    """Save results to Google Sheets.

    Args:
        data: List of dictionaries to save
        sheet_name: Optional sheet name (uses task metadata if not provided)

    Returns:
        Confirmation message
    """
    if not ctx.deps.sheets_storage:
        return "Google Sheets storage not configured"

    task = ctx.deps.task
    sheet_id = task.metadata.sheet_id or config.default_sheet_id
    sheet_name = sheet_name or task.metadata.sheet_name or task.id

    if not sheet_id:
        return "No Google Sheets ID configured"

    ctx.deps.sheets_storage.append_dicts(
        spreadsheet_id=sheet_id,
        sheet_name=sheet_name,
        data=data,
        add_timestamp=True,
    )

    return f"Saved {len(data)} results to Google Sheets (sheet: {sheet_name})"


@autonomous_agent.tool
def save_to_sqlite(
    ctx: RunContext[AgentDependencies],
    data: List[Dict[str, Any]],
    table_name: Optional[str] = None,
) -> str:
    """Save results to SQLite database.

    Args:
        data: List of dictionaries to save
        table_name: Optional table name (uses task metadata if not provided)

    Returns:
        Confirmation message
    """
    task = ctx.deps.task
    table_name = table_name or task.metadata.db_table or task.id

    ctx.deps.sqlite_storage.append_results(
        task_id=task.id,
        table_name=table_name,
        data=data,
    )

    return f"Saved {len(data)} results to SQLite (table: {table_name})"


@autonomous_agent.tool
def save_to_faiss(
    ctx: RunContext[AgentDependencies],
    texts: List[str],
    metadata: List[Dict[str, Any]],
) -> str:
    """Save texts to FAISS vector store for semantic search.

    Args:
        texts: List of text strings to index
        metadata: Metadata for each text

    Returns:
        Confirmation message
    """
    task = ctx.deps.task

    # Add task_id to metadata
    for meta in metadata:
        meta['task_id'] = task.id

    ids = ctx.deps.faiss_storage.add_texts(texts, metadata)

    return f"Saved {len(texts)} items to FAISS vector store"


@autonomous_agent.tool
def get_task_info(ctx: RunContext[AgentDependencies]) -> Dict[str, Any]:
    """Get information about the current task.

    Returns:
        Dictionary with task details, requirements, and attached data
    """
    task = ctx.deps.task

    # Get attachment text if available
    attachments_info = {}
    for attachment_name in task.metadata.attachments:
        text = task.get_attachment_text(attachment_name)
        if text:
            attachments_info[attachment_name] = text[:2000]  # Limit size

    return {
        "task_id": task.id,
        "title": task.metadata.title,
        "description": task.metadata.description,
        "content": task.content,
        "output_type": task.metadata.output_type,
        "max_results": task.metadata.max_results,
        "search_depth": task.metadata.search_depth,
        "attachments": attachments_info,
    }


class AutonomousAgent:
    """Autonomous agent executor."""

    def __init__(self):
        """Initialize the autonomous agent."""
        self.crawl_tool = Crawl4AITool(
            headless=config.crawl4ai_headless,
            browser=config.crawl4ai_browser,
        )

        self.search_tool = UnifiedSearchTool(
            google_api_key=config.google_api_key,
            google_cse_id=config.google_cse_id,
            brave_api_key=config.brave_api_key,
        )

        self.extraction_tool = BeautifulSoupTool()

        # Initialize storage backends
        self.sqlite_storage = SQLiteStorage(config.sqlite_db_path)
        self.faiss_storage = FAISSStorage(config.faiss_index_path)

        # Initialize Google Sheets if configured
        self.sheets_storage = None
        try:
            service_account_info = config.get_google_service_account_info()
            self.sheets_storage = GoogleSheetsStorage(service_account_info)
        except (ValueError, FileNotFoundError):
            print("Google Sheets not configured, skipping...")

    async def execute_task(self, task: Task) -> TaskResult:
        """Execute a task autonomously.

        Args:
            task: Task to execute

        Returns:
            TaskResult with execution summary
        """
        # Save task to SQLite
        self.sqlite_storage.save_task(
            task_id=task.id,
            title=task.metadata.title,
            content=task.content,
            description=task.metadata.description,
            metadata=task.metadata.model_dump(),
        )

        # Create dependencies
        deps = AgentDependencies(
            task=task,
            crawl_tool=self.crawl_tool,
            search_tool=self.search_tool,
            extraction_tool=self.extraction_tool,
            sheets_storage=self.sheets_storage,
            sqlite_storage=self.sqlite_storage,
            faiss_storage=self.faiss_storage,
        )

        # Run the agent
        prompt = f"""Execute the following task autonomously:

Task: {task.metadata.title}

{task.content}

First, use get_task_info() to understand the full task details and any attached data.
Then, create your own plan and execute it using the available tools.
Be thorough and autonomous - search, crawl, extract, and save results without asking for confirmation.

At the end, provide a summary of what you accomplished."""

        try:
            result = await autonomous_agent.run(prompt, deps=deps)

            return TaskResult(
                success=True,
                summary=result.output,
                results_count=0,  # Agent will report in summary
                storage_locations=[task.metadata.output_type],
            )

        except Exception as e:
            return TaskResult(
                success=False,
                summary=f"Task execution failed: {str(e)}",
                results_count=0,
                storage_locations=[],
                errors=[str(e)],
            )
