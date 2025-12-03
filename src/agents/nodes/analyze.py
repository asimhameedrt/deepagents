"""Analysis node for LangGraph workflow."""

import json
from typing import List, Dict, Any, Optional

from ...models.state import AgentState
from ...models.search_result import ReflectionOutput
from ...services.llm.claude_service import ClaudeService
from ...observability.detailed_logger import log_node_execution, DetailedLogger
from ...utils.research_utils import merge_entities_with_llm, calculate_confidence_score


def _build_reflection_prompt(state: AgentState) -> str:
    """
    Build comprehensive prompt for reflection analysis.
    
    Args:
        state: Current agent state
        
    Returns:
        Formatted prompt string
    """
    # Get latest search memory
    latest_search = state["search_memory"][-1] if state["search_memory"] else {}
    
    # Get previous reflections for progression context
    previous_reflections = state.get("reflection_memory", [])
    
    # Build prompt
    prompt = f"""# Research Subject
Subject: {state['subject']}
Context: {state.get('subject_context', 'N/A')}
Current Research Depth: {state['current_depth']}

# Latest Search Results
"""
    
    # Add search summaries from latest iteration
    if latest_search:
        summaries = latest_search.get("summaries", [])
        for i, summary in enumerate(summaries, 1):
            prompt += f"\n## Search {i}: {summary.get('query', 'N/A')}\n"
            prompt += f"Summary: {summary.get('summary', 'No summary available')}\n"
            prompt += f"Key Entities Mentioned: {', '.join(summary.get('key_entities', []))}\n"
    
    # Add previous reflection context (show progression)
    if previous_reflections:
        prompt += f"\n# Previous Reflection Summary (Iteration {len(previous_reflections)-1})\n"
        last_reflection = previous_reflections[-1]
        prompt += f"Previous Findings: {len(last_reflection.get('new_findings', []))} findings\n"
        prompt += f"Entities Discovered So Far: {len(last_reflection.get('new_entities', []))} entities\n"
        prompt += f"Red Flags Identified: {len(last_reflection.get('red_flags', []))} red flags\n"
        prompt += f"Previous Confidence: {last_reflection.get('confidence_score', 0.0):.2f}\n"
        prompt += f"Previous Decision: {'Continue' if last_reflection.get('should_continue') else 'Stop'}\n"
    
    # Add current state context
    prompt += f"\n# Current Research State\n"
    prompt += f"Total Queries Executed: {len(state.get('queries_executed', []))}\n"
    prompt += f"Total Search Iterations: {len(state.get('search_memory', []))}\n"
    prompt += f"Known Entities: {len(state.get('discovered_entities', {}))}\n"
    prompt += f"Current Red Flags: {len(state.get('risk_indicators', {}).get('red_flags', []))}\n"
    
    # Add task instructions
    prompt += """

# Your Task: Analyze and Reflect

Please perform a comprehensive analysis of the latest search results:

1. **Compress Findings**: Extract key facts by category
   - Biographical (personal details, education, background)
   - Professional (employment history, roles, positions)
   - Financial (assets, investments, transactions, net worth)
   - Legal (lawsuits, investigations, regulatory actions)
   - Behavioral (patterns, associations, decision-making)
   - Other relevant categories based on findings

2. **Source Credibility Assessment**: Evaluate each source's credibility (0-1 scale)
   - High credibility (0.8-1.0): Government sites, verified databases, major news outlets
   - Medium credibility (0.5-0.8): Established blogs, company websites, trade publications
   - Low credibility (0.2-0.5): Social media, forums, unverified sources
   - Provide specific credibility scores for sources used

3. **Entity Extraction**: Identify all new entities discovered
   - Persons (names, roles, relationships to subject)
   - Organizations (companies, institutions, agencies)
   - Events (significant occurrences, transactions, meetings)
   - Locations (places of residence, business operations)

4. **Relationship Mapping**: Describe connections found
   - Format: "Entity1 → relationship → Entity2"
   - Include timeframes and context where available

5. **Risk Categorization**: Classify all findings
   - **Red Flags**: Concerning findings with severity (critical/high/medium/low) and confidence (0-1)
   - **Neutral Facts**: Factual information without risk implications
   - **Positive Indicators**: Achievements, credentials, positive associations

6. **Gap Analysis**:
   - Identify information gaps (what's still unknown or unclear)
   - Note which gaps were searched in this iteration
   - Mark gaps as unfillable if no data found after searching

7. **Research Decision**:
   - Should research continue or is sufficient information gathered?
   - Provide clear reasoning for your decision
   - Consider: depth of coverage, red flag severity, information completeness

8. **Next Steps Strategy** (if continuing):
   - Priority topics for next searches (prioritize red flags and high-severity issues)
   - Suggested search angles or directions
   - Focus areas based on gaps and new entities

Provide your analysis in structured JSON format matching the ReflectionOutput schema.
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
        "new_findings": len(reflection_result.get("new_findings", [])),
        "new_entities": len(reflection_result.get("new_entities", [])),
        "red_flags": len(reflection_result.get("red_flags", [])),
        "should_continue": reflection_result.get("should_continue", False)
    })
    
    # Merge entities with existing ones (LLM-based deduplication)
    logger.log_info("Merging entities with LLM deduplication")
    merged_entities = await merge_entities_with_llm(
        existing_entities=state.get("discovered_entities", {}),
        new_entities=reflection_result.get("new_entities", []),
        session_id=state["session_id"]
    )
    
    # Calculate overall confidence score
    confidence_score = calculate_confidence_score(
        reflection_output=reflection_result,
        search_memory=state.get("search_memory", []),
        current_depth=state["current_depth"]
    )
    
    logger.log_info(f"Calculated confidence score: {confidence_score:.3f}")
    
    # Update state with reflection results
    state["reflection_memory"].append(reflection_result)
    state["discovered_entities"] = merged_entities
    state["confidence_score"] = confidence_score
    
    # Update risk indicators (append new findings)
    red_flags_text = [rf.get("finding") for rf in reflection_result.get("red_flags", [])]
    state["risk_indicators"]["red_flags"].extend(red_flags_text)
    state["risk_indicators"]["neutral"].extend(reflection_result.get("neutral_facts", []))
    state["risk_indicators"]["positive"].extend(reflection_result.get("positive_indicators", []))
    
    # Update control flow based on reflection decision
    state["should_continue"] = reflection_result.get("should_continue", True)
    
    logger.log_info("Reflection complete", {
        "total_entities": len(merged_entities),
        "total_red_flags": len(state["risk_indicators"]["red_flags"]),
        "confidence_score": confidence_score,
        "should_continue": state["should_continue"]
    })
    
    return state