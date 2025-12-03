"""Analysis node for LangGraph workflow."""

import json
from typing import List, Dict, Any, Optional

from ...models.state import AgentState
from ...models.search_result import ReflectionOutput
from ...services.llm.claude_service import ClaudeService
from ...observability.detailed_logger import log_node_execution, DetailedLogger
from ...utils.research_utils import merge_entities_with_llm


def _build_reflection_prompt(state: AgentState) -> str:
    """
    Build comprehensive prompt for reflection analysis.
    
    Args:
        state: Current agent state
        
    Returns:
        Formatted prompt string
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


@log_node_execution
async def analyze_and_reflect(state: AgentState) -> AgentState:
    """
    Analyze and reflect on search results using Claude.
    
    This node:
    1. Compresses research findings into structured categories
    2. Assesses source credibility using LLM
    3. Extracts new entities and relationships
    4. Categorizes findings as red_flags/neutral/positive
    5. Performs gap analysis
    6. Calculates confidence score
    7. Decides whether to continue research
    8. Suggests priority topics and angles for next iteration
    
    Args:
        state: Current agent state
        
    Returns:
        Updated agent state with reflection results
    """
    # print("\n"*12)
    # print("################################################################################")
    # print("Agent State: ", json.dumps(state, indent=2, default=str))
    # print("################################################################################")
    
    logger = DetailedLogger(state["session_id"])
    logger.log_info("Starting reflection and analysis", {
        "current_depth": state["current_depth"],
        "search_iterations": len(state.get("search_memory", []))
    })
    
    # Check if we have search results to analyze
    if not state.get("search_memory"):
        logger.log_warning("No search memory to analyze, skipping reflection")
        return state
    
    # Initialize Claude service
    claude = ClaudeService(session_id=state["session_id"])
    
    # Build reflection prompt
    prompt = _build_reflection_prompt(state)
    print("\n"*12)
    print("################################################################################")
    print("_build_reflection_prompt: ", prompt)
    print("################################################################################")
    
    
    
    system_prompt = """You are an expert research analyst specializing in Enhanced Due Diligence (EDD) investigations. 
Your role is to analyze search results, identify risks, and guide investigation strategy.

Focus on:
- Risk identification (fraud, misconduct, conflicts of interest, legal issues)
- Pattern recognition (behavioral patterns, suspicious connections, timeline anomalies)
- Evidence quality (source credibility, corroboration, specificity)
- Investigation completeness (gaps, unexplored angles, need for deeper research)

Be thorough, objective, and strategic in your analysis."""
    
    # Execute reflection analysis
    logger.log_info("Executing Claude reflection analysis")

    reflection_result = await claude.extract_structured(
        text=prompt,
        schema=ReflectionOutput,
        system_prompt=system_prompt
    )
    
    logger.log_info("Reflection analysis complete", {
        "analysis_length": len(reflection_result.get("analysis_summary", "")),
        "should_continue": reflection_result.get("should_continue", False)
    })
    
    # Merge entities using OpenAI (handles entity extraction from text + deduplication)
    logger.log_info("Merging entities with OpenAI (extracts from analysis_summary)")
    merged_entities = await merge_entities_with_llm(
        existing_entities=state.get("discovered_entities", {}),
        analysis_summary=reflection_result.get("analysis_summary", ""),
        session_id=state["session_id"]
    )
    
    # Update state with reflection results
    state["reflection_memory"].append(reflection_result)
    state["discovered_entities"] = merged_entities
    
    # Update control flow based on reflection decision
    state["should_continue"] = reflection_result.get("should_continue", True)
    
    logger.log_info("Reflection complete", {
        "total_entities": len(merged_entities),
        "should_continue": state["should_continue"]
    })
    
    # Increment depth after completing current iteration
    # This ensures the next iteration uses the correct depth for query generation
    state["current_depth"] += 1
    logger.log_info("Depth incremented after analysis", {
        "new_depth": state["current_depth"]
    })
    
    return state