"""Initialization node for LangGraph workflow."""

import uuid
from datetime import datetime
from typing import Dict, Any

from ...models.state import AgentState
from ...observability.detailed_logger import log_node_execution, DetailedLogger


@log_node_execution
async def initialize_session(state: AgentState) -> AgentState:
    """
    Initialize a new research session with default values.
    
    Args:
        state: Initial agent state (may contain subject and config)
        
    Returns:
        Fully initialized agent state ready for research workflow
    """
    # Generate session ID if not provided
    session_id = state.get("session_id") or str(uuid.uuid4())
    
    logger = DetailedLogger(session_id)
    logger.log("initializing_session", {
        "subject": state.get("subject", "unknown"),
        "session_id": session_id
    })
    
    defaults = dict(
        current_depth=0, start_time=datetime.utcnow(), entities=[], facts=[], connections=[],
        red_flags=[], queries_executed=[], pending_queries=[],
        search_count=0, extraction_count=0, error_count=0, should_continue=True,
        messages=[], search_iterations=[], extracted_metadata={}, timeline=[],
        search_memory=[]
    )
    for k, v in defaults.items():
        state.setdefault(k, v() if callable(v) and k == "start_time" else v)
    
    
    logger.log("session_initialized", {
        "session_id": session_id,
        "max_depth": state["max_depth"],
        "subject": state["subject"]
    })
    
    return state

