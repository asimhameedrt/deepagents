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
class RedFlagItem(BaseModel):
    """Individual red flag finding with severity and confidence."""
    finding: str = Field(description="Description of the red flag")
    severity: str = Field(description="Severity level: critical, high, medium, low")
    confidence: float = Field(description="Confidence score (0-1)")
    sources: List[str] = Field(default_factory=list, description="Source names supporting this finding")

class SourceCredibility(BaseModel):
    """Source credibility assessment."""
    source: str = Field(description="Source name or title")
    url: str = Field(description="Source URL")
    credibility: float = Field(description="Credibility weight (0-1)")

class ReflectionOutput(BaseModel):
    """Output from reflection and analysis node (Claude)."""
    
    # Key Findings Summary
    new_findings: List[str] = Field(
        default_factory=list,
        description="New facts discovered this iteration"
    )
    new_entities: List[str] = Field(
        default_factory=list,
        description="Newly discovered entities (persons, organizations, events)"
    )
    new_relationships: List[str] = Field(
        default_factory=list,
        description="Discovered connections in free-form text"
    )
    
    # Gap Analysis
    identified_gaps: List[str] = Field(
        default_factory=list,
        description="Information gaps identified"
    )
    gaps_searched: List[str] = Field(
        default_factory=list,
        description="Gaps we attempted to fill this iteration"
    )
    gaps_unfillable: List[str] = Field(
        default_factory=list,
        description="Gaps with no data found (give up on these)"
    )
    
    # Risk Assessment
    red_flags: List[RedFlagItem] = Field(
        default_factory=list,
        description="Red flag findings with severity and confidence"
    )
    neutral_facts: List[str] = Field(
        default_factory=list,
        description="Neutral factual findings"
    )
    positive_indicators: List[str] = Field(
        default_factory=list,
        description="Positive indicators or achievements"
    )
    
    # Decision Making
    should_continue: bool = Field(description="Whether to continue research")
    reasoning: str = Field(description="Reasoning for continue/stop decision")
    confidence_score: float = Field(description="Overall confidence in findings (0-1)")
    
    # Query Strategy
    priority_topics: List[str] = Field(
        default_factory=list,
        description="Ranked list of topics for next queries (red flags prioritized)"
    )
    suggested_angles: List[str] = Field(
        default_factory=list,
        description="Specific search angles or directions"
    )
    
    # Source Assessment
    source_credibility: List[SourceCredibility] = Field(
        default_factory=list,
        description="LLM-assessed credibility of sources used"
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
