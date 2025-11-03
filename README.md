# Autonomous Browser Agent

An AI-powered autonomous browser agent built with PydanticAI and Crawl4AI for web research and data collection.

## Features

- **Fully Autonomous**: The agent plans its own steps and makes decisions without human intervention
- **Multi-Tool Integration**:
  - Crawl4AI for advanced web crawling
  - Google Custom Search API and Brave Search API
  - BeautifulSoup for structured data extraction
- **Multiple Storage Backends**:
  - Google Sheets (via service account)
  - SQLite for local persistence
  - FAISS for semantic vector search
- **Task Scheduling**: Recurring tasks (daily, weekly, monthly, or cron-based)
- **Flexible Task Definition**: Define tasks in Markdown files with YAML frontmatter
- **Reasoning & Planning**: PydanticAI-powered agent with full reasoning capabilities

## Installation

### Prerequisites

- Python 3.9+
- pip

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd scholarship_search
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install Playwright browsers:
```bash
python -m playwright install chromium
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

## Configuration

Edit `.env` file with your credentials:

```env
# AI Model (OpenAI, Anthropic, etc.)
AI_MODEL=openai:gpt-4o
OPENAI_API_KEY=your_key_here

# Search APIs
GOOGLE_API_KEY=your_key
GOOGLE_CSE_ID=your_cse_id
BRAVE_API_KEY=your_key

# Google Sheets (service account JSON)
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}
DEFAULT_SHEET_ID=your_sheet_id
```

### Google Sheets Setup

1. Create a Google Cloud project
2. Enable Google Sheets API and Google Drive API
3. Create a service account and download the JSON key
4. Share your Google Sheet with the service account email
5. Add the JSON content to `.env` or save as file and reference path

## Usage

### Run a Single Task

```bash
python main.py run ai_scholarships
```

### List All Tasks

```bash
python main.py list-tasks

# Show only recurring tasks
python main.py list-tasks --recurring
```

### Start Task Scheduler

For recurring tasks:

```bash
python main.py schedule
```

### Query Results

```bash
# Show recent results
python main.py query-results

# Filter by task
python main.py query-results --task-id ai_scholarships --limit 20
```

### Check Configuration

```bash
python main.py config-info
```

## Creating Tasks

Tasks are defined as Markdown files in the `./tasks/` directory with YAML frontmatter.

### Example Task

```markdown
---
title: Find AI Scholarships
description: Search for fully funded AI scholarships
recurring: weekly
output_type: google_sheets
sheet_name: Scholarships
max_results: 30
search_depth: 2
attachments:
  - attachments/cv.txt
---

# Task Description

Search for fully funded PhD scholarships in AI and Machine Learning.

## Requirements
1. Must be fully funded
2. Related to AI/ML
3. Open to international students

## Output Format
Save with these fields:
- Title
- University
- Deadline
- Link
- Funding Details
```

### Task Metadata Fields

- `title`: Task title (required)
- `description`: Brief description
- `recurring`: Schedule (hourly, daily, weekly, monthly)
- `cron`: Cron expression for custom scheduling
- `output_type`: google_sheets, sqlite, faiss, or multiple
- `sheet_id`: Google Sheets ID (optional, uses default from config)
- `sheet_name`: Sheet tab name
- `db_table`: SQLite table name
- `max_results`: Maximum results to collect
- `search_depth`: How many levels deep to crawl
- `attachments`: List of attachment files (e.g., CVs)

## Architecture

### Core Components

1. **Task Parser** (`src/task_parser.py`)
   - Parses Markdown task files with YAML frontmatter
   - Loads attachments (CVs, documents)

2. **Autonomous Agent** (`src/agent.py`)
   - PydanticAI-powered agent with reasoning
   - Self-planning and decision-making
   - Tool-based execution

3. **Tools** (`src/tools/`)
   - `crawl4ai_tool.py`: Web crawling with Crawl4AI
   - `search_tools.py`: Google and Brave search
   - `extraction_tools.py`: BeautifulSoup extraction

4. **Storage** (`src/storage/`)
   - `google_sheets.py`: Google Sheets integration
   - `sqlite_storage.py`: Local SQLite database
   - `faiss_storage.py`: Vector search with FAISS

5. **Scheduler** (`src/scheduler.py`)
   - APScheduler-based task scheduling
   - Cron and interval triggers

### How It Works

1. **Task Loading**: Load task file and parse metadata
2. **Context Building**: Agent receives task description and attachments
3. **Autonomous Planning**: Agent creates its own execution plan
4. **Tool Execution**: Agent uses tools to search, crawl, and extract
5. **Result Storage**: Saves structured data to configured destination
6. **Scheduling**: Recurring tasks run automatically

## Example Use Cases

### 1. Scholarship Search

Find scholarships matching a CV:
- Reads CV to understand profile
- Searches multiple sources
- Crawls scholarship pages
- Extracts deadlines, requirements, funding details
- Ranks by relevance
- Saves to Google Sheets

### 2. Conference Tracking

Monitor AI conference deadlines:
- Searches for CFPs
- Extracts submission deadlines
- Tracks notification dates
- Saves to SQLite for querying
- Runs daily to catch updates

### 3. Research Paper Discovery

Index recent papers:
- Searches arXiv, Papers with Code
- Extracts paper metadata
- Indexes abstracts in FAISS
- Enables semantic search
- Updates weekly

## Tools & APIs Used

- **PydanticAI**: Agent framework with type safety
- **Crawl4AI**: LLM-friendly web crawling
- **Google Custom Search API**: Web search
- **Brave Search API**: Alternative search engine
- **BeautifulSoup**: HTML parsing
- **gspread**: Google Sheets API
- **FAISS**: Vector similarity search
- **APScheduler**: Task scheduling

## Development

### Project Structure

```
scholarship_search/
├── src/
│   ├── agent.py              # Autonomous agent
│   ├── config.py             # Configuration
│   ├── task_parser.py        # Task file parser
│   ├── scheduler.py          # Task scheduler
│   ├── tools/                # Tool implementations
│   │   ├── crawl4ai_tool.py
│   │   ├── search_tools.py
│   │   └── extraction_tools.py
│   └── storage/              # Storage backends
│       ├── google_sheets.py
│       ├── sqlite_storage.py
│       └── faiss_storage.py
├── tasks/                    # Task definitions
│   ├── ai_scholarships.md
│   ├── tech_conferences.md
│   └── attachments/
├── data/                     # Local data storage
│   ├── results.db           # SQLite database
│   └── faiss_index/         # FAISS vectors
├── main.py                   # CLI entry point
├── requirements.txt
└── .env                      # Configuration
```

### Adding New Tools

Tools are registered with the agent using decorators:

```python
@autonomous_agent.tool
async def my_custom_tool(
    ctx: RunContext[AgentDependencies],
    param: str,
) -> dict:
    """Tool description for the LLM."""
    # Implementation
    return {"result": "data"}
```

## Troubleshooting

### Playwright Issues

```bash
# Reinstall Playwright
python -m playwright install --with-deps chromium
```

### Google Sheets Permission Denied

- Ensure the Sheet is shared with the service account email
- Check that Google Sheets API is enabled

### API Rate Limits

- Use Brave Search as fallback (cheaper than Google)
- Adjust `max_results` and `search_depth` in tasks
- Add delays between requests if needed

## License

MIT License

## Contributing

Contributions welcome! Please open an issue or PR.

## Acknowledgments

- Built with [PydanticAI](https://ai.pydantic.dev/)
- Powered by [Crawl4AI](https://github.com/unclecode/crawl4ai)
