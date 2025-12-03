"""Query generation node for LangGraph workflow."""

from ...models.state import AgentState
from ...services.search.query_generator import QueryGenerator
from ...observability.detailed_logger import log_node_execution, DetailedLogger

@log_node_execution
async def generate_search_queries(state: AgentState) -> AgentState:
    """
    Generate search queries based on current state.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated agent state with new queries
    """
    logger = DetailedLogger(state.get("session_id", "unknown"))
    query_generator = QueryGenerator(session_id=state.get("session_id"))
    
    current_depth = state.get("current_depth", 0)
    
    try:
        if current_depth == 0:
            # Initial queries
            logger.log("generating_initial_queries", {"subject": state["subject"]})
            queries = await query_generator.generate_initial_queries(
                subject=state["subject"],
                context=state.get("subject_context")
            )
        else:
            # Enhanced refined queries based on discoveries and analysis
            logger.log("refining_queries", {
                "depth": current_depth,
                "entities_count": len(state.get("entities", [])),
                "facts_count": len(state.get("facts", [])),
                "next_steps_count": len(state.get("next_steps", [])),
                "information_gaps_count": len(state.get("information_gaps", [])),
                "red_flags_count": len(state.get("red_flags", [])),
                "connections_count": len(state.get("connections", []))
            })
            queries = await query_generator.refine_queries(
                subject=state["subject"],
                discovered_entities=state.get("entities", []),
                discovered_facts=state.get("facts", []),
                current_depth=current_depth,
                next_steps=state.get("next_steps"),
                information_gaps=state.get("information_gaps"),
                red_flags=state.get("red_flags"),
                connections=state.get("connections"),
                risk_assessment=state.get("risk_assessment")
            )
        
        # Log generated queries
        logger.log_search_queries(queries, f"Depth {current_depth}")
        
        # Add to pending queries
        state["pending_queries"] = queries
        
        # Increment depth
        state["current_depth"] = current_depth + 1
        
        # Increment iteration counter for safety
        state["iteration_count"] = state.get("iteration_count", 0) + 1
        
    except Exception as e:
        logger.log_error("generate_search_queries", e, {"depth": current_depth})
        state["error_count"] = state.get("error_count", 0) + 1
        state["pending_queries"] = []
    
    return state