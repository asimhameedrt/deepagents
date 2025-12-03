"""Routing logic for LangGraph conditional edges."""

from ...models.state import AgentState
from ...config.settings import settings
from ...utils.research_utils import check_stagnation
from ...observability.detailed_logger import DetailedLogger


def should_continue_research(state: AgentState) -> str:
    """
    Determine next action based on current state and reflection analysis.
    
    This implements the search strategy by deciding whether to:
    - continue_search: Generate more queries and continue searching
    - analyze: Switch to connection mapping (when stagnation detected)
    - finish: Stop research and synthesize report
    
    Decision criteria (checked in order):
    1. Max depth reached → finish
    2. Confidence threshold met → finish
    3. Reflection recommends stop → finish
    4. Stagnation detected (no new entities in N iterations) → analyze
    5. Otherwise → continue_search
    
    Args:
        state: Current agent state
        
    Returns:
        Next node name ("continue_search", "analyze", "finish")
    """
    logger = DetailedLogger(state.get("session_id", "unknown"))
    
    # 1. Check hard limit: max depth
    if state["current_depth"] >= state["max_depth"]:
        logger.log_info("Routing decision: FINISH (max depth reached)", {
            "current_depth": state["current_depth"],
            "max_depth": state["max_depth"]
        })
        state["termination_reason"] = "max_depth_reached"
        return "finish"
    
    # 2. Check confidence threshold
    if state.get("confidence_score", 0.0) >= settings.confidence_threshold:
        logger.log_info("Routing decision: FINISH (confidence threshold met)", {
            "confidence_score": state["confidence_score"],
            "threshold": settings.confidence_threshold
        })
        state["termination_reason"] = "confidence_threshold_met"
        return "finish"
    
    # 3. Check reflection decision
    reflection_memory = state.get("reflection_memory", [])
    if reflection_memory:
        latest_reflection = reflection_memory[-1]
        should_continue = latest_reflection.get("should_continue", True)
        
        if not should_continue:
            logger.log_info("Routing decision: FINISH (reflection recommended stop)", {
                "reasoning": latest_reflection.get("reasoning", "No reasoning provided")
            })
            state["termination_reason"] = "reflection_recommended_stop"
            return "finish"
    
    # 4. Check stagnation (no new entities in last N iterations)
    if check_stagnation(reflection_memory, settings.stagnation_check_iterations):
        logger.log_info("Routing decision: ANALYZE (stagnation detected)", {
            "stagnation_iterations": settings.stagnation_check_iterations
        })
        return "analyze"
    
    # 5. Continue searching
    logger.log_info("Routing decision: CONTINUE_SEARCH", {
        "current_depth": state["current_depth"],
        "confidence_score": state.get("confidence_score", 0.0)
    })
    
    # Increment depth for next iteration
    state["current_depth"] += 1
    
    return "continue_search"


def has_new_queries(state: AgentState) -> str:
    """
    Check if query refinement produced new queries to execute.
    
    This routing function is called after refine_queries node to determine
    whether to execute the refined queries or proceed to synthesis.
    
    Args:
        state: Current agent state
        
    Returns:
        Next node name ("search_more", "synthesize")
    """
    logger = DetailedLogger(state.get("session_id", "unknown"))
    
    pending_queries = state.get("pending_queries", [])
    
    if pending_queries:
        logger.log_info("Routing decision: SEARCH_MORE", {
            "pending_queries_count": len(pending_queries)
        })
        return "search_more"
    else:
        logger.log_info("Routing decision: SYNTHESIZE (no new queries)")
        state["termination_reason"] = "no_additional_queries"
        return "synthesize"


def needs_deeper_research(state: AgentState) -> str:
    """
    Determine if deeper research is needed after initial analysis.
    
    NOTE: This function is currently not used in the main graph flow,
    but kept for potential future use or alternative routing strategies.
    
    Args:
        state: Current agent state
        
    Returns:
        Next node name ("refine", "synthesize")
    """
    logger = DetailedLogger(state.get("session_id", "unknown"))
    
    # Check if there are unexplored entities or gaps
    reflection_memory = state.get("reflection_memory", [])
    if reflection_memory:
        latest_reflection = reflection_memory[-1]
        priority_topics = latest_reflection.get("priority_topics", [])
        
        if priority_topics:
            logger.log_info("Routing decision: REFINE (priority topics identified)", {
                "priority_topics_count": len(priority_topics)
            })
            return "refine"
    
    # No deeper research needed
    logger.log_info("Routing decision: SYNTHESIZE (no deeper research needed)")
    state["termination_reason"] = "research_complete"
    return "synthesize"

