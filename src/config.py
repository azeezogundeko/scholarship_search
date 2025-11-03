"""Configuration management for the autonomous agent."""

import json
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field


# Load environment variables
load_dotenv()


class Config(BaseModel):
    """Application configuration loaded from environment variables."""

    # AI Model
    ai_model: str = Field(default="gemini-1.5-pro", description="AI model to use")
    google_genai_api_key: Optional[str] = Field(default=None, description="Google Generative AI API key")
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")

    # Search APIs
    google_api_key: Optional[str] = Field(default=None, description="Google API key")
    google_cse_id: Optional[str] = Field(default=None, description="Google Custom Search Engine ID")
    brave_api_key: Optional[str] = Field(default=None, description="Brave Search API key")

    # Google Sheets
    google_service_account_json: Optional[str] = Field(default=None, description="Google service account JSON")
    google_service_account_path: Optional[str] = Field(default=None, description="Path to service account JSON")
    default_sheet_id: Optional[str] = Field(default=None, description="Default Google Sheet ID")

    # Storage
    sqlite_db_path: Path = Field(default=Path("./data/results.db"), description="SQLite database path")
    faiss_index_path: Path = Field(default=Path("./data/faiss_index"), description="FAISS index path")

    # Crawl4AI
    crawl4ai_browser: str = Field(default="chromium", description="Browser to use for crawling")
    crawl4ai_headless: bool = Field(default=True, description="Run browser in headless mode")

    # Scheduler
    scheduler_timezone: str = Field(default="UTC", description="Timezone for scheduler")

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        return cls(
            ai_model=os.getenv("AI_MODEL", "gemini-1.5-pro"),
            google_genai_api_key=os.getenv("GOOGLE_GENAI_API_KEY"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            google_cse_id=os.getenv("GOOGLE_CSE_ID"),
            brave_api_key=os.getenv("BRAVE_API_KEY"),
            google_service_account_json=os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON"),
            google_service_account_path=os.getenv("GOOGLE_SERVICE_ACCOUNT_PATH"),
            default_sheet_id=os.getenv("DEFAULT_SHEET_ID"),
            sqlite_db_path=Path(os.getenv("SQLITE_DB_PATH", "./data/results.db")),
            faiss_index_path=Path(os.getenv("FAISS_INDEX_PATH", "./data/faiss_index")),
            crawl4ai_browser=os.getenv("CRAWL4AI_BROWSER", "chromium"),
            crawl4ai_headless=os.getenv("CRAWL4AI_HEADLESS", "true").lower() == "true",
            scheduler_timezone=os.getenv("SCHEDULER_TIMEZONE", "UTC"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )

    def get_google_service_account_info(self) -> dict:
        """Get Google service account credentials as a dictionary."""
        if self.google_service_account_json:
            return json.loads(self.google_service_account_json)
        elif self.google_service_account_path:
            with open(self.google_service_account_path) as f:
                return json.load(f)
        else:
            raise ValueError("No Google service account credentials configured")


# Global config instance
config = Config.from_env()
