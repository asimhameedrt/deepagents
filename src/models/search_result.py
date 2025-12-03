"""Research data models for search and aggregation."""

from datetime import datetime
from typing import List, Optional, Dict, Any
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


#=======================================================
#          Reflection & Analysis Models                 #
#=======================================================
class ReflectionOutput(BaseModel):
    """Simplified reflection output from Claude (fast, reliable)."""
    
    # Analysis Summary (Structured Text)
    analysis_summary: str = Field(
        description="""Comprehensive analysis in structured text format with sections:
        
## Key Findings
- List of new facts discovered

## Entities Discovered
- List of persons, organizations, events, locations

## Relationships
- Format: (subject) --relation--> (object)
- Example: (Sam Bankman-Fried) --founded--> (FTX)

## Risk Assessment
RED FLAGS:
- [SEVERITY] Description of red flag
NEUTRAL:
- Neutral factual findings
POSITIVE:
- Positive indicators

## Gaps
Identified: List of information gaps
Searched: Gaps we attempted to fill
Unfillable: Gaps with no data found

## Source Credibility
- Notes on source quality and reliability
"""
    )
    
    # Decision Making
    should_continue: bool = Field(description="Whether to continue research")
    reasoning: str = Field(description="Reasoning for continue/stop decision")
    
    # Query Strategy (Textual)
    query_strategy: str = Field(
        description="Textual description of priority topics and suggested search angles for next iteration"
    )


#=======================================================
#          Connection Mapping Models                    #
#=======================================================
class GraphNode(BaseModel):
    """Entity node for graph representation."""
    id: str = Field(description="Unique identifier for the entity")
    name: str = Field(description="Entity name")
    type: str = Field(description="Entity type: person, organization, event, location, etc.")
    attributes: Dict[str, Any] = Field(
        default_factory=dict,
        description="Flexible attributes for entity-specific data"
    )

class GraphEdge(BaseModel):
    """Relationship edge for graph representation."""
    source: str = Field(description="Source entity ID")
    target: str = Field(description="Target entity ID")
    relationship: str = Field(description="Relationship type (free-form)")
    confidence: float = Field(description="Confidence in this relationship (0-1)")
    attributes: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional relationship metadata (timeframe, type, etc.)"
    )

class KeyEntity(BaseModel):
    """Key entity with importance assessment."""
    entity: str = Field(description="Entity name")
    importance_score: float = Field(description="Importance to investigation (0-1)")
    reason: str = Field(description="Reasoning for importance")

class ConnectionMappingOutput(BaseModel):
    """Output from connection mapping analysis (OpenAI)."""
    
    # Graph Updates
    new_nodes: List[GraphNode] = Field(
        default_factory=list,
        description="New entities to add to graph"
    )
    new_edges: List[GraphEdge] = Field(
        default_factory=list,
        description="New relationships to add to graph"
    )
    
    # Pattern Detection
    patterns_identified: List[str] = Field(
        default_factory=list,
        description="Patterns found in connections (free-form descriptions)"
    )
    suspicious_patterns: List[str] = Field(
        default_factory=list,
        description="Auto-flagged concerning patterns"
    )
    
    # Entity Importance (LLM-based assessment)
    key_entities: List[KeyEntity] = Field(
        default_factory=list,
        description="Important entities with reasoning"
    )
