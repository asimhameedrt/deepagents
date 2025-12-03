"""Research-specific utility functions for entity merging, graph operations, and confidence calculation."""

from typing import Dict, List, Any, Optional
from ..config.settings import settings
from ..services.llm.claude_service import ClaudeService
from ..services.llm.openai_service import OpenAIService
from pydantic import BaseModel, Field


class EntityMergeInput(BaseModel):
    """Input schema for entity merging."""
    existing_entities: Dict[str, Any] = Field(description="Existing discovered entities")
    new_entities: List[str] = Field(description="New entities to merge")
    
class EntityMergeOutput(BaseModel):
    """Output schema for entity merging."""
    merged_entities: Dict[str, Any] = Field(
        description="Merged entity dictionary with deduplicated entries"
    )
    merge_decisions: List[str] = Field(
        description="List of merge decisions made (e.g., 'Merged: John Smith = J. Smith')"
    )


async def merge_entities_with_llm(
    existing_entities: Dict[str, Any],
    new_entities: List[str],
    session_id: str
) -> Dict[str, Any]:
    """
    Merge new entities with existing ones using LLM for deduplication.
    
    Handles entity disambiguation (e.g., "John Smith" vs "J. Smith") using LLM reasoning.
    
    Args:
        existing_entities: Current entity dictionary
        new_entities: List of newly discovered entity names
        session_id: Session ID for logging
        
    Returns:
        Updated entity dictionary with merged entries
    """
    if not new_entities:
        return existing_entities
    
    # If no existing entities, just convert list to dict
    if not existing_entities:
        return {entity: {"name": entity, "mentions": 1} for entity in new_entities}
    
    # Use Claude for intelligent merging
    claude = ClaudeService(session_id=session_id)
    
    system_prompt = """You are an entity deduplication expert. Your task is to merge new entity names with existing entities, handling variations and duplicates intelligently.

Rules:
1. Identify if a new entity is the same as an existing one (e.g., "John Smith" = "J. Smith", "FTX" = "FTX Exchange")
2. For organizations, consider abbreviations and full names as same entity
3. For persons, match based on first+last name even if middle initial differs
4. If uncertain (confidence < 0.7), treat as separate entity
5. Increment mention count for matched entities
6. Add new entries for distinct entities
7. Return the complete merged dictionary"""
    
    instruction = f"""Existing entities: {existing_entities}
New entities to merge: {new_entities}

Merge these entities intelligently, handling duplicates and variations."""
    
    result = await claude.extract_structured(
        text=instruction,
        schema=EntityMergeOutput,
        system_prompt=system_prompt
    )
    
    return result.get("merged_entities", existing_entities)


class GraphMergeInput(BaseModel):
    """Input schema for graph merging."""
    existing_graph: Dict[str, Any] = Field(description="Existing entity graph")
    new_nodes: List[Dict[str, Any]] = Field(description="New nodes to add")
    new_edges: List[Dict[str, Any]] = Field(description="New edges to add")

class GraphMergeOutput(BaseModel):
    """Output schema for graph merging."""
    merged_graph: Dict[str, Any] = Field(
        description="Merged graph with deduplicated nodes and edges"
    )
    merge_summary: str = Field(description="Summary of merge operations performed")


async def merge_graph_with_llm(
    existing_graph: Dict[str, Any],
    new_nodes: List[Dict[str, Any]],
    new_edges: List[Dict[str, Any]],
    session_id: str
) -> Dict[str, Any]:
    """
    Merge new graph nodes and edges with existing graph using LLM.
    
    Handles node deduplication and edge consolidation using LLM reasoning.
    
    Args:
        existing_graph: Current graph structure {"nodes": [...], "edges": [...]}
        new_nodes: New nodes to add
        new_edges: New edges to add
        session_id: Session ID for logging
        
    Returns:
        Updated graph structure
    """
    # Initialize empty graph if needed
    if not existing_graph:
        existing_graph = {"nodes": [], "edges": []}
    
    if not new_nodes and not new_edges:
        return existing_graph
    
    # Use Claude for intelligent graph merging
    claude = ClaudeService(session_id=session_id)
    
    system_prompt = """You are a graph deduplication expert. Merge new nodes and edges into existing graph structure.

Rules:
1. Deduplicate nodes by 'id' field (case-insensitive)
2. For duplicate nodes, merge attributes (keep most complete information)
3. Deduplicate edges by source+target+relationship combination
4. For duplicate edges, keep higher confidence score
5. Maintain graph structure: {"nodes": [...], "edges": [...]}
6. Ensure all edge source/target IDs exist in nodes list"""
    
    instruction = f"""Existing graph: {existing_graph}
New nodes: {new_nodes}
New edges: {new_edges}

Merge the new nodes and edges into the existing graph."""
    
    result = await claude.extract_structured(
        text=instruction,
        schema=GraphMergeOutput,
        system_prompt=system_prompt
    )
    
    return result.get("merged_graph", existing_graph)


def calculate_confidence_score(
    reflection_output: Dict[str, Any],
    search_memory: List[Dict[str, Any]],
    current_depth: int
) -> float:
    """
    Calculate overall research confidence score using weighted components.
    
    Formula (configurable via settings):
    confidence_score = (
        finding_confidence * weight_findings +
        source_credibility * weight_sources +
        gap_coverage * weight_gaps +
        cross_validation * weight_validation
    )
    
    Components:
    1. Finding Confidence: Average confidence of red flags and key findings
    2. Source Credibility: Average credibility weight across sources
    3. Gap Coverage: Percentage of identified gaps successfully researched
    4. Cross-validation: Percentage of facts corroborated by multiple sources
    
    Args:
        reflection_output: Latest reflection output dictionary
        search_memory: All search memory entries
        current_depth: Current search depth
        
    Returns:
        Confidence score between 0 and 1
    """
    # Component 1: Finding Confidence (from red_flags confidence scores)
    red_flags = reflection_output.get("red_flags", [])
    if red_flags:
        finding_confidence = sum(rf.get("confidence", 0.5) for rf in red_flags) / len(red_flags)
    else:
        finding_confidence = 0.5  # Neutral if no red flags yet
    
    # Component 2: Source Credibility (from source_credibility assessments)
    source_creds = reflection_output.get("source_credibility", [])
    if source_creds:
        source_credibility = sum(sc.get("credibility", 0.5) for sc in source_creds) / len(source_creds)
    else:
        source_credibility = 0.5  # Neutral if no credibility data
    
    # Component 3: Gap Coverage (gaps filled / gaps identified)
    identified_gaps = reflection_output.get("identified_gaps", [])
    gaps_searched = reflection_output.get("gaps_searched", [])
    gaps_unfillable = reflection_output.get("gaps_unfillable", [])
    
    if identified_gaps:
        gaps_addressed = len(gaps_searched) + len(gaps_unfillable)
        gap_coverage = min(gaps_addressed / len(identified_gaps), 1.0)
    else:
        gap_coverage = 0.8  # High coverage if no gaps identified (complete picture)
    
    # Component 4: Cross-validation (simplified - based on source count per iteration)
    # Higher cross-validation if multiple sources found per search
    total_sources = sum(
        mem.get("sources_found", 0) for mem in search_memory
    )
    total_queries = sum(
        len(mem.get("queries", [])) for mem in search_memory
    )
    if total_queries > 0:
        avg_sources_per_query = total_sources / total_queries
        cross_validation = min(avg_sources_per_query / 5.0, 1.0)  # Normalize to 0-1 (5 sources = full validation)
    else:
        cross_validation = 0.0
    
    # Calculate weighted average
    confidence_score = (
        finding_confidence * settings.confidence_weight_findings +
        source_credibility * settings.confidence_weight_sources +
        gap_coverage * settings.confidence_weight_gaps +
        cross_validation * settings.confidence_weight_validation
    )
    
    return min(max(confidence_score, 0.0), 1.0)  # Clamp to [0, 1]


def check_stagnation(
    reflection_memory: List[Dict[str, Any]],
    n_iterations: Optional[int] = None
) -> bool:
    """
    Check if research has stagnated (no new entities in last N iterations).
    
    Args:
        reflection_memory: List of reflection outputs
        n_iterations: Number of iterations to check (defaults to settings value)
        
    Returns:
        True if stagnated, False otherwise
    """
    if n_iterations is None:
        n_iterations = settings.stagnation_check_iterations
    
    # Need at least N reflections to check
    if len(reflection_memory) < n_iterations:
        return False
    
    # Check last N reflections for new entities
    recent_reflections = reflection_memory[-n_iterations:]
    
    for reflection in recent_reflections:
        new_entities = reflection.get("new_entities", [])
        if new_entities:  # Found new entities, not stagnated
            return False
    
    # No new entities in last N iterations
    return True

