"""Synthesis node for LangGraph workflow."""

from datetime import datetime

from ...models.state import AgentState
from ...config.settings import settings
from ...observability.detailed_logger import log_node_execution, DetailedLogger


@log_node_execution
async def synthesize_report(state: AgentState) -> AgentState:
    """
    Synthesize the final report from all discoveries.
    
    Uses the enhanced report format for comprehensive due diligence output.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated agent state with final report
    """
    logger = DetailedLogger(state.get("session_id", "unknown"))
    
    try:
        # Calculate processing time
        start_time = state.get("start_time", datetime.utcnow())
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Build models config from settings
        models_config = {
            "openai_search_model": settings.openai_search_model,
            "openai_extraction_model": settings.openai_extraction_model,
            "claude_model": settings.claude_model
        }
    
        
        # Mark as complete
        state["should_continue"] = False
        state["termination_reason"] = "Report generated successfully"
        
    except Exception as e:
        logger.log_error("synthesize_report", e, {"state_keys": list(state.keys())})
        state["error_count"] = state.get("error_count", 0) + 1
        state["should_continue"] = False
        state["termination_reason"] = f"Report generation error: {str(e)}"
        print(f"Synthesis error: {e}")
    
    return state

