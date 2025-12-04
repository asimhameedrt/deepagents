"""
Prompts for final report synthesis using OpenAI.

This module provides prompt builders for synthesizing comprehensive
due diligence reports from all collected research findings.

Used by:
- `agents/nodes/synthesize.py` → `synthesize_report`
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models.state import AgentState


# ============================================================================
# Synthesis Instructions
# ============================================================================

SYNTHESIS_INSTRUCTIONS = """You are an expert due diligence analyst preparing comprehensive investigation reports.

Your reports are:
- Professional and objective
- Well-structured and detailed
- Evidence-based with specific facts
- Clear about risks and uncertainties
- Actionable with concrete recommendations

Synthesize all research findings into a cohesive, comprehensive report."""


# ============================================================================
# Prompt Builder Functions
# ============================================================================

def build_synthesis_prompt(state: "AgentState") -> str:
    """
    Build comprehensive prompt for report synthesis.
    
    This prompt includes:
    - Subject information and context
    - Research metrics and statistics
    - All reflection analysis summaries
    - Entity graph and relationships
    - Risk indicators summary
    - Source quality assessment
    - Task instructions
    
    Args:
        state: Current agent state with all research findings
        
    Returns:
        Formatted prompt string for report synthesis
    """
    # Gather all data
    reflection_memory = state.get("reflection_memory", [])
    entity_graph = state.get("entity_graph", {})
    risk_indicators = state.get("risk_indicators", {})
    search_iterations = state.get("search_iterations", [])
    
    prompt = f"""# Due Diligence Report Synthesis

## Subject Information
Subject: {state['subject']}
Context: {state.get('subject_context', 'N/A')}
Session ID: {state['session_id']}

## Research Metrics
Search Depth: {state['current_depth']} iterations
Total Queries: {len(state.get('queries_executed', []))}
Total Sources: {sum(s.get('sources_found', 0) for s in search_iterations)}
Confidence Score: {state.get('confidence_score', 0.0):.2f}
Termination Reason: {state.get('termination_reason', 'N/A')}

"""
    
    # Add reflection summaries
    prompt += "\n## Research Findings (All Iterations)\n\n"
    for i, reflection in enumerate(reflection_memory):
        prompt += f"### Iteration {i}\n"
        prompt += f"**Analysis Summary:**\n{reflection.get('analysis_summary', 'No analysis available')}\n\n"
        prompt += f"**Decision:** {'Continue' if reflection.get('should_continue') else 'Stop'}\n"
        prompt += f"**Reasoning:** {reflection.get('reasoning', 'N/A')}\n\n"
    
    # Add entity graph summary
    if entity_graph.get("nodes"):
        prompt += f"\n## Entity Graph\n"
        prompt += f"Total Entities: {len(entity_graph.get('nodes', []))}\n"
        prompt += f"Total Relationships: {len(entity_graph.get('edges', []))}\n\n"
        
        prompt += "**Key Entities:**\n"
        for node in entity_graph.get("nodes", [])[:10]:
            prompt += f"- {node.get('name', 'Unknown')} ({node.get('type', 'unknown')})\n"
        
        prompt += "\n**Key Relationships:**\n"
        for edge in entity_graph.get("edges", [])[:15]:
            source = edge.get("source", "?")
            target = edge.get("target", "?")
            rel = edge.get("relationship", "?")
            prompt += f"- {source} → {rel} → {target}\n"
    
    # Add risk indicators summary
    prompt += "\n## Risk Indicators Summary\n"
    prompt += f"Red Flags: {len(risk_indicators.get('red_flags', []))}\n"
    prompt += f"Neutral Facts: {len(risk_indicators.get('neutral', []))}\n"
    prompt += f"Positive Indicators: {len(risk_indicators.get('positive', []))}\n"
    
    # Add source quality info
    total_sources = sum(s.get("sources_found", 0) for s in search_iterations)
    prompt += f"\n## Source Quality\n"
    prompt += f"Total Sources Referenced: {total_sources}\n"
    
    # Task instructions
    prompt += """

## Your Task: Synthesize Comprehensive Due Diligence Report

Create a detailed, professional due diligence report with the following sections:

1. **Executive Summary**: Concise overview (3-5 sentences) of who the subject is and key risk assessment

2. **Risk Level**: Overall assessment (CRITICAL/HIGH/MEDIUM/LOW) based on findings

3. **Key Findings**: Top 5-10 most important discoveries (prioritize red flags)

4. **Biographical Overview**: Personal background, education, family, early life

5. **Professional History**: Employment timeline, positions held, career trajectory

6. **Financial Analysis**: Assets, investments, financial dealings, net worth information

7. **Legal & Regulatory**: Lawsuits, investigations, regulatory actions, compliance issues

8. **Behavioral Patterns**: Decision-making style, associations, ethical conduct, reputation

9. **Red Flags**: All concerning findings with severity and evidence

10. **Neutral Facts**: Important factual information without risk implications

11. **Positive Indicators**: Achievements, credentials, positive associations

12. **Key Relationships**: Most important entity connections

13. **Suspicious Connections**: Concerning patterns or hidden relationships

14. **Source Summary**: Assessment of source quality and credibility

15. **Evidence Strength**: How strong is the evidence for key findings?

16. **Information Gaps**: What remains unknown or unclear?

17. **Research Limitations**: Constraints on completeness (time, access, data availability)

18. **Recommendations**: Next steps or further investigation needs

Write in professional, objective tone. Be specific with facts and evidence. Cite severity levels for red flags.
"""
    
    return prompt

