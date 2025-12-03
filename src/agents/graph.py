"""LangGraph workflow definition."""

from langgraph.graph import StateGraph, END

from ..models.state import AgentState
from .nodes.initialize import initialize_session
from .nodes.web_search import execute_web_search
from .nodes.generate_queries import generate_search_queries
from .nodes.connect import map_connections
from .nodes.analyze import analyze_and_reflect
from .nodes.synthesize import synthesize_report
from .edges.routing import should_continue_research, has_new_queries

def create_research_graph() -> StateGraph:
    """
    Create the LangGraph workflow for deep research.
    
    The workflow implements a streamlined search and analysis strategy:
    1. Initialize session
    2. Generate initial queries (based on subject and context)
    3. Execute searches
    4. Analyze and reflect on results
    5. Decision: continue searching, refine, or finish
    6. If continue: generate more queries and loop back
    7. If refine: map connections and generate refined queries
    8. If more queries: search more
    9. Synthesize final report
    
    Returns:
        Compiled StateGraph
    """
    # Create the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("initialize", initialize_session)
    workflow.add_node("generate_queries", generate_search_queries)
    workflow.add_node("execute_search", execute_web_search)
    workflow.add_node("analyze_and_reflect", analyze_and_reflect)
    workflow.add_node("map_connections", map_connections)
    workflow.add_node("refine_queries", generate_search_queries)  # Same as generate but based on findings
    workflow.add_node("synthesize_report", synthesize_report)
    
    # Define edges
    # Linear flow from start through initial search
    workflow.add_edge("initialize", "generate_queries")
    workflow.add_edge("generate_queries", "execute_search")
    workflow.add_edge("execute_search", "analyze_and_reflect")
    
    # Conditional routing after analysis
    workflow.add_conditional_edges(
        "analyze_and_reflect",
        should_continue_research,
        {
            "continue_search": "generate_queries",  # Loop back for more searches
            "analyze": "map_connections",  # Move to deeper analysis
            "finish": "synthesize_report"  # Skip to report generation
        }
    )
    
    # Connection mapping flow
    workflow.add_edge("map_connections", "refine_queries")
    
    # Decision after refining queries
    workflow.add_conditional_edges(
        "refine_queries",
        has_new_queries,
        {
            "search_more": "execute_search",  # Execute refined searches
            "synthesize": "synthesize_report"  # Done searching, generate report
        }
    )
    
    # Report synthesis ends the workflow
    workflow.add_edge("synthesize_report", END)
    
    # Set entry point
    workflow.set_entry_point("initialize")
    
    return workflow.compile()


# Create the compiled graph
research_graph = create_research_graph()

