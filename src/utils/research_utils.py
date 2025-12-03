"""Research-specific utility functions for entity merging, graph operations, and confidence calculation."""

from typing import Dict, List, Any, Optional
from ..config.settings import settings
from ..services.llm.openai_service import OpenAIService
from pydantic import BaseModel, Field
from agents import Agent, ModelSettings, Runner, RunConfig, AgentOutputSchema


class EntityMergeOutput(BaseModel):
    """Output schema for entity merging."""
    merged_entities: Dict[str, Any] = Field(
        description="Merged entity dictionary with deduplicated entries. Keys are entity names, values contain metadata."
    )
    entities_extracted: List[str] = Field(
        description="List of entity names extracted from the analysis summary"
    )


async def merge_entities_with_llm(
    existing_entities: Dict[str, Any],
    analysis_summary: str,
    session_id: str
) -> Dict[str, Any]:
    """
    Extract entities from analysis text and merge with existing using OpenAI.
    
    Two-step process:
    1. Extract entities from analysis_summary text
    2. Merge with existing entities, handling deduplication
    
    Args:
        existing_entities: Current entity dictionary
        analysis_summary: Text from Claude's reflection containing entities
        session_id: Session ID for logging
        
    Returns:
        Updated entity dictionary with merged entries
    """
    if not analysis_summary:
        return existing_entities
    
    # Use OpenAI for extraction + merging (fast, structured output)
    openai_service = OpenAIService(session_id=session_id)
    
    instructions = """You are an entity extraction and deduplication expert.

Your task:
1. Extract all entities from the analysis summary (persons, organizations, events, locations)
2. Merge them with existing entities, handling duplicates intelligently

Entity matching rules:
- "John Smith" = "J. Smith" (name variations)
- "FTX" = "FTX Exchange" (abbreviations)
- "Sam Bankman-Fried" = "SBF" (nicknames)
- If uncertain (confidence < 0.7), treat as separate entity

For merged entities:
- Keep most complete name
- Increment mention count
- Preserve all metadata

Return:
- merged_entities: Complete entity dictionary (existing + new, deduplicated)
- entities_extracted: List of entity names found in analysis summary"""
    
    prompt = f"""# Entity Extraction and Merging

## Existing Entities
{existing_entities if existing_entities else "None"}

## Analysis Summary (extract entities from this text)
{analysis_summary}

Extract all entities from the analysis summary and merge with existing entities."""
    
    agent = Agent(
        name="EntityMerger",
        model=settings.openai_search_model,
        instructions=instructions,
        output_type=AgentOutputSchema(EntityMergeOutput, strict_json_schema=False),
        model_settings=ModelSettings(verbosity="medium"),
    )
    
    result = await Runner.run(agent, prompt, run_config=RunConfig(tracing_disabled=True))
    output: EntityMergeOutput = result.final_output
    
    return output.merged_entities if output.merged_entities else existing_entities


class GraphMergeOutput(BaseModel):
    """Output schema for graph merging."""
    merged_graph: Dict[str, Any] = Field(
        description="Merged graph with deduplicated nodes and edges. Structure: {'nodes': [...], 'edges': [...]}"
    )
    nodes_added: int = Field(description="Number of new nodes added")
    edges_added: int = Field(description="Number of new edges added")
    nodes_merged: int = Field(description="Number of nodes merged with existing")


async def merge_graph_with_llm(
    existing_graph: Dict[str, Any],
    new_nodes: List[Dict[str, Any]],
    new_edges: List[Dict[str, Any]],
    session_id: str
) -> Dict[str, Any]:
    """
    Merge new graph nodes and edges with existing graph using OpenAI.
    
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
    
    # Use OpenAI for intelligent graph merging (fast, structured output)
    openai_service = OpenAIService(session_id=session_id)
    
    instructions = """You are a graph deduplication expert. Merge new nodes and edges into existing graph.

Node deduplication rules:
1. Match by 'id' field (case-insensitive, normalized)
2. "sam_bankman_fried" = "sbf" = "Sam-Bankman-Fried" (same entity)
3. For duplicates: merge attributes, keep most complete info
4. Increment relationship count for matched nodes

Edge deduplication rules:
1. Match by source + target + relationship (all three must match)
2. For duplicates: keep edge with higher confidence
3. Ensure all edge source/target IDs exist in nodes list

Output structure:
{"nodes": [...], "edges": [...]}"""
    
    prompt = f"""# Graph Merging Task

## Existing Graph
Nodes: {len(existing_graph.get('nodes', []))}
Edges: {len(existing_graph.get('edges', []))}
{existing_graph}

## New Nodes to Add
{new_nodes}

## New Edges to Add
{new_edges}

Merge new nodes and edges into existing graph, handling duplicates intelligently."""
    
    agent = Agent(
        name="GraphMerger",
        model=settings.openai_search_model,
        instructions=instructions,
        output_type=AgentOutputSchema(GraphMergeOutput, strict_json_schema=False),
        model_settings=ModelSettings(verbosity="medium"),
    )
    
    result = await Runner.run(agent, prompt, run_config=RunConfig(tracing_disabled=True))
    output: GraphMergeOutput = result.final_output
    
    return output.merged_graph if output.merged_graph else existing_graph


# NOTE: Confidence calculation moved to connection mapping node
# No longer calculated in reflection (Claude keeps schema simple)


def check_stagnation(
    reflection_memory: List[Dict[str, Any]],
    n_iterations: Optional[int] = None
) -> bool:
    """
    Check if research has stagnated (no significant progress in last N iterations).
    
    Since entities are extracted by OpenAI during merge (not in reflection),
    we check if the analysis_summary indicates new discoveries.
    
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
    
    # Check last N reflections for significant findings
    # If analysis_summary mentions "no new entities" or "no significant findings"
    # or is very short, consider it stagnation
    recent_reflections = reflection_memory[-n_iterations:]
    
    stagnant_count = 0
    for reflection in recent_reflections:
        analysis = reflection.get("analysis_summary", "").lower()
        
        # Check for stagnation indicators
        if any(indicator in analysis for indicator in [
            "no new entities",
            "no significant findings", 
            "limited new information",
            "entities discovered: none",
            "entities discovered:\nnone"
        ]) or len(analysis) < 200:  # Very short analysis suggests little found
            stagnant_count += 1
    
    # If all recent iterations show stagnation, return True
    return stagnant_count >= n_iterations

