"""Agent state models for LangGraph workflow."""

from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional, TypedDict, Dict, Union
from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field


class SearchIterationData(TypedDict, total=False):
    """Data for a every search iteration."""
    
    goal: str
    queries: List[str]
    model_used: Optional[str]
    new_entities: List[str]
    sources_found: int
    sources: List[Dict[str, str]]  # List of {url, title} dicts
    errors: List[str]


class AgentState(TypedDict):
    """State maintained throughout the agent workflow.
    
    This state is passed between LangGraph nodes and tracks all
    information discovered during the research process.
    """
    
    # Session Info
    session_id: str
    subject: str
    subject_context: Optional[str]
    
    # Research Progress
    current_depth: int
    max_depth: int
    queries_executed: List[str]
    
    # Search Strategy
    pending_queries: List[str]
    
    # Control Flow
    should_continue: bool
    termination_reason: Optional[str]
    
    # Metrics
    start_time: datetime
    search_count: int
    extraction_count: int
    error_count: int
    iteration_count: int  # Track total graph iterations for safety
    
    # Audit Trail - for enhanced reporting
    search_iterations: List[SearchIterationData]
    
    # Search Results Memory - shared workflow memory for decision-making
    search_memory: List[Dict[str, Any]]  # List of search iteration search results
    
    # Messages (for LangGraph)
    messages: List[BaseMessage]

