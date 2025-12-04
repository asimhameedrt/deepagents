"""
Prompts for reflection and analysis using Claude.

This module provides prompt builders for analyzing search results,
identifying risks, extracting entities, and planning next steps.

Used by:
- `agents/nodes/analyze.py` → `analyze_and_reflect`
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models.state import AgentState


# ============================================================================
# Analysis System Prompt
# ============================================================================

ANALYSIS_SYSTEM_PROMPT = """You are an expert research analyst specializing in Enhanced Due Diligence (EDD) investigations. 

<role_description>
Your role is to analyze search results, identify risks, and guide investigation strategy.
</role_description>

<analysis_focus_areas>
Focus on:
- Risk identification (fraud, misconduct, conflicts of interest, legal issues)
- Pattern recognition (behavioral patterns, suspicious connections, timeline anomalies)
- Evidence quality (source credibility, corroboration, specificity)
- Investigation completeness (gaps, unexplored angles, need for deeper research)
</analysis_focus_areas>

<analysis_standards>
Be thorough, objective, and strategic in your analysis.
</analysis_standards>"""


# ============================================================================
# Prompt Builder Functions
# ============================================================================

def build_reflection_prompt(state: "AgentState") -> str:
    """
    Build comprehensive prompt for reflection analysis.
    
    This prompt includes:
    - Subject information and context
    - Latest search results from current depth
    - Previous reflection summary (if available)
    - Current research state metrics
    - Task instructions for structured analysis
    
    Args:
        state: Current agent state
        
    Returns:
        Formatted prompt string for reflection analysis
    """
    # Get previous reflections for progression context
    previous_reflections = state.get("reflection_memory", [])
    
    # Build prompt
    prompt = f"""# Research Subject
Subject: {state['subject']}
Context: {state.get('subject_context', 'N/A')}
Current Research Depth: {state['current_depth']}

# Latest Search Results
"""
    
    # Add search results from latest iteration
    # Note: search_memory is a list of search results, not grouped by iteration
    # Get all search results from current depth
    if state.get("search_memory"):
        current_depth_searches = [
            s for s in state["search_memory"] 
            if s.get("depth") == state["current_depth"]
        ]
        
        for i, search in enumerate(current_depth_searches, 1):
            prompt += f"\n## Search {i}: {search.get('query', 'N/A')}\n"
            prompt += f"Search Result: {search.get('search_result', 'No results available')}\n"
            prompt += f"Sources Found: {search.get('sources_count', 0)}\n"
    
    # Add previous reflection context (show progression)
    if previous_reflections:
        prompt += f"\n# Previous Reflection Summary (Iteration {len(previous_reflections)-1})\n"
        last_reflection = previous_reflections[-1]
        
        # Display previous analysis summary (truncated if too long)
        prev_analysis = last_reflection.get('analysis_summary', '')
        prompt += f"Previous Analysis:\n{prev_analysis}\n\n"
        
        # Show decision and reasoning
        prompt += f"Previous Decision: {'Continue' if last_reflection.get('should_continue') else 'Stop'}\n"
        prompt += f"Reasoning: {last_reflection.get('reasoning', 'N/A')}\n"
        prompt += f"Query Strategy Suggested: {last_reflection.get('query_strategy', 'N/A')}\n"
    
    # Add current state context
    prompt += f"\n# Current Research State\n"
    prompt += f"Total Queries Executed: {len(state.get('queries_executed', []))}\n"
    prompt += f"Total Search Iterations: {len(state.get('search_memory', []))}\n"
    prompt += f"Known Entities: {len(state.get('discovered_entities', {}))}\n"
    prompt += f"Current Red Flags: {len(state.get('risk_indicators', {}).get('red_flags', []))}\n"
    
    # Add task instructions
    prompt += """

# Your Task: Analyze and Reflect

Perform comprehensive analysis of search results and provide output in the following format:

## Analysis Summary Structure

### Key Findings
List new facts discovered (biographical, professional, financial, legal, behavioral)

### Entities Discovered
List all new entities:
- Persons (names, roles)
- Organizations (companies, institutions)
- Events (significant occurrences)
- Locations (relevant places)

### Relationships
Describe connections using format: (subject) --relation--> (object)
Examples:
- (Sam Bankman-Fried) --founded--> (FTX)
- (FTX) --sister-company--> (Alameda Research)
- (SBF) --romantic-relationship--> (Caroline Ellison)

### Risk Assessment

RED FLAGS:
List concerning findings with severity in brackets
- [CRITICAL] Description of critical red flag
- [HIGH] Description of high severity issue
- [MEDIUM] Description of medium concern

NEUTRAL:
- Factual findings without risk implications

POSITIVE:
- Positive indicators, achievements, credentials

### Gaps
Identified: What information is still missing?
Searched: Which gaps did we try to fill this iteration?
Unfillable: Which gaps have no available data?

### Source Credibility
Notes on source quality:
- High credibility: Government, verified databases, major news
- Medium credibility: Established sites, company websites
- Low credibility: Social media, unverified sources

## Decision Making
Decide if research should continue based on:
- Depth of coverage achieved
- Severity of red flags found
- Completeness of information
- Remaining unknowns

## Query Strategy (if continuing)
Describe priority topics and search angles for next iteration:
- Prioritize red flags and high-severity issues
- Target newly discovered entities
- Address critical information gaps
"""
    
    return prompt

