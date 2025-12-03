"""Research data models for search and aggregation."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


#=======================================================
#               Web Search Models                       #
#=======================================================
class WebSearchSource(BaseModel):
    """Source found during web search (for LLM structured output)."""
    url: str = Field(description="URL of the source")
    title: str = Field(description="Title or publisher name")

class WebSearchOutput(BaseModel):
    """Structured output schema for web search LLM responses."""
    query: str = Field(description="The search query executed")
    search_result: str = Field(
        description="All the search results by keeping the key information verbatim as it is"
    )
    sources: List[WebSearchSource] = Field(description="All sources used with URLs and titles")

class SearchQueriesList(BaseModel):
    """Structured output schema for search query generation."""
    queries: List[str] = Field(description="Targeted search queries prioritized by value")
