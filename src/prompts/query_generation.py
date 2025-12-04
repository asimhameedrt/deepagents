"""
Prompts for search query generation using Claude.

This module provides system prompts and prompt builders for generating
both initial and refined search queries based on reflection analysis.

Used by:
- `services/search/query_generator.py` → `QueryGenerator`
"""

from typing import List, Optional, Dict, Any


# ============================================================================
# Initial Query Generation System Prompt
# ============================================================================

INITIAL_QUERY_SYSTEM_PROMPT = """You are an expert research strategist for Enhanced Due Diligence investigations.

<task_overview>
Your task is to generate initial search queries that provide broad coverage of a subject.
</task_overview>

<focus_areas>
For initial queries (Depth 0), focus on:
1. Biographical basics (background, education, early career)
2. Professional history (employment, roles, companies)
3. Financial information (net worth, investments, major transactions)
4. Legal/regulatory issues (lawsuits, investigations, compliance)
5. Behavioral patterns (associations, decision-making, public statements)
</focus_areas>

<query_quality_guidelines>
Generate specific, targeted queries that will retrieve high-quality information.
</query_quality_guidelines>"""


# ============================================================================
# Refined Query Generation System Prompt
# ============================================================================

REFINED_QUERY_SYSTEM_PROMPT = """You are an expert research strategist for Enhanced Due Diligence investigations.

<task_overview>
Your task is to generate refined search queries based on the query strategy from reflection analysis.
</task_overview>

<key_principles>
1. PRIORITIZE RED FLAGS: Focus on high-severity risks mentioned in strategy
2. EXPLORE NEW ENTITIES: Target entities mentioned in strategy
3. FOLLOW STRATEGY: Use the provided query strategy as your guide
4. AVOID REPETITION: Do not repeat or closely paraphrase previous queries
5. BE SPECIFIC: Target concrete facts, not general information
</key_principles>

<objective>
Generate queries that will uncover deeper intelligence based on the strategy.
</objective>"""


# ============================================================================
# Prompt Builder Functions
# ============================================================================

def build_initial_query_prompt(
    subject: str,
    context: Optional[str],
    max_queries: int
) -> str:
    """
    Build prompt for initial query generation.
    
    Args:
        subject: Research subject
        context: Additional context about subject
        max_queries: Maximum number of queries to generate
        
    Returns:
        Formatted prompt string for initial query generation
    """
    return f"""# Initial Query Generation

Subject: {subject}
Context: {context or 'No additional context'}

Generate {max_queries} initial search queries for comprehensive due diligence research on this subject.

Queries should be:
- Specific and targeted (not generic)
- Diverse in coverage (different aspects of subject)
- Optimized for web search (natural language, specific terms)
- Focused on factual information (not opinion)

Return queries as a JSON list."""


def build_refined_query_prompt(
    subject: str,
    query_strategy: str,
    queries_executed: List[str],
    discovered_entities_count: int,
    current_depth: int,
    max_queries: int
) -> str:
    """
    Build prompt for refined query generation based on reflection.
    
    Args:
        subject: Research subject
        query_strategy: Query strategy from latest reflection
        queries_executed: Previously executed queries (for deduplication)
        discovered_entities_count: Number of entities discovered
        current_depth: Current search depth
        max_queries: Maximum number of queries to generate
        
    Returns:
        Formatted prompt string for refined query generation
    """
    # Get recent queries to avoid duplication
    recent_queries = "\n".join(f"- {q}" for q in queries_executed[-10:])
    
    return f"""# Refined Query Generation (Depth {current_depth})

Subject: {subject}

## Query Strategy from Reflection
{query_strategy}

## Context
Total Queries Executed: {len(queries_executed)}
Entities Discovered: {discovered_entities_count}

## Recent Queries (AVOID DUPLICATING)
{recent_queries}

## Your Task

Generate {max_queries} NEW search queries based on the query strategy above.

Requirements:
1. Follow the priority topics and angles from the strategy
2. Target specific entities, events, or relationships mentioned
3. DO NOT repeat or closely paraphrase previous queries
4. Make queries specific and targeted (not generic)

Return as JSON list."""

