"""Synthesis node for LangGraph workflow using OpenAI."""

import json
from datetime import datetime
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from ...models.state import AgentState
from ...config.settings import settings
from ...services.llm.openai_service import OpenAIService
from ...observability.detailed_logger import log_node_execution, DetailedLogger
from agents import Agent, ModelSettings, Runner, RunConfig


class DueDiligenceReport(BaseModel):
    """Comprehensive due diligence report schema."""
    
    executive_summary: str = Field(description="High-level overview of key findings and risk assessment")
    risk_level: str = Field(description="Overall risk level: CRITICAL, HIGH, MEDIUM, LOW")
    key_findings: List[str] = Field(description="Top 5-10 most important findings")
    
    # Detailed sections
    biographical_overview: str = Field(description="Personal background, education, family")
    professional_history: str = Field(description="Employment history, roles, career progression")
    financial_analysis: str = Field(description="Assets, investments, transactions, net worth")
    legal_regulatory: str = Field(description="Lawsuits, investigations, compliance issues")
    behavioral_patterns: str = Field(description="Decision-making patterns, associations, conduct")
    
    # Risk assessment
    red_flags: List[Dict[str, Any]] = Field(description="Critical red flags with details")
    neutral_facts: List[str] = Field(description="Neutral factual findings")
    positive_indicators: List[str] = Field(description="Positive achievements and indicators")
    
    # Entity analysis
    key_relationships: List[str] = Field(description="Most important entity relationships")
    suspicious_connections: List[str] = Field(description="Concerning patterns or connections")
    
    # Evidence and sources
    source_summary: str = Field(description="Summary of source quality and credibility")
    evidence_strength: str = Field(description="Assessment of evidence quality")
    
    # Gaps and limitations
    information_gaps: List[str] = Field(description="Remaining unknowns or unclear areas")
    research_limitations: str = Field(description="Constraints on research completeness")
    
    # Recommendations
    recommendations: List[str] = Field(description="Recommended actions or further investigation")


def _build_synthesis_prompt(state: AgentState) -> str:
    """Build comprehensive prompt for report synthesis."""
    
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
        
        new_findings = reflection.get("new_findings", [])
        if new_findings:
            prompt += "**New Findings:**\n"
            for finding in new_findings[:10]:  # Limit for prompt size
                prompt += f"- {finding}\n"
        
        red_flags = reflection.get("red_flags", [])
        if red_flags:
            prompt += "\n**Red Flags:**\n"
            for rf in red_flags[:5]:
                if isinstance(rf, dict):
                    prompt += f"- [{rf.get('severity', 'unknown').upper()}] {rf.get('finding', 'N/A')} (confidence: {rf.get('confidence', 0):.2f})\n"
                else:
                    prompt += f"- {rf}\n"
        
        prompt += "\n"
    
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


@log_node_execution
async def synthesize_report(state: AgentState) -> AgentState:
    """
    Synthesize comprehensive final report using OpenAI.
    
    Creates a detailed due diligence report with:
    - Executive summary and risk assessment
    - Detailed findings by category
    - Entity relationship analysis
    - Source and evidence evaluation
    - Recommendations
    
    Args:
        state: Current agent state
        
    Returns:
        Updated agent state with final_report
    """
    logger = DetailedLogger(state.get("session_id", "unknown"))
    logger.log_info("Starting report synthesis")
    
    try:
        # Build synthesis prompt
        prompt = _build_synthesis_prompt(state)
        
        # Use OpenAI Agents SDK for report generation
        instructions = """You are an expert due diligence analyst preparing comprehensive investigation reports.

Your reports are:
- Professional and objective
- Well-structured and detailed
- Evidence-based with specific facts
- Clear about risks and uncertainties
- Actionable with concrete recommendations

Synthesize all research findings into a cohesive, comprehensive report."""
        
        agent = Agent(
            name="ReportSynthesizer",
            model=settings.openai_search_model,
            instructions=instructions,
            output_type=DueDiligenceReport,
            model_settings=ModelSettings(verbosity="medium"),
        )
        
        logger.log_info("Executing OpenAI report synthesis")
        result = await Runner.run(agent, prompt, run_config=RunConfig(tracing_disabled=True))
        
        report: DueDiligenceReport = result.final_output
        
        # Convert to dict and add metadata
        final_report = report.model_dump()
        
        # Add metadata
        start_time = state.get("start_time", datetime.utcnow())
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        final_report["metadata"] = {
            "subject": state["subject"],
            "session_id": state["session_id"],
            "research_depth": state["current_depth"],
            "total_queries": len(state.get("queries_executed", [])),
            "total_sources": sum(s.get("sources_found", 0) for s in state.get("search_iterations", [])),
            "confidence_score": state.get("confidence_score", 0.0),
            "processing_time_seconds": processing_time,
            "termination_reason": state.get("termination_reason"),
            "generated_at": datetime.utcnow().isoformat(),
            "models_used": {
                "search": settings.openai_search_model,
                "analysis": settings.claude_model,
                "synthesis": settings.openai_search_model
            }
        }
        
        # Add entity graph
        final_report["entity_graph"] = state.get("entity_graph", {})
        
        # Store in state
        state["final_report"] = final_report
        
        logger.log_info("Report synthesis complete", {
            "risk_level": report.risk_level,
            "key_findings_count": len(report.key_findings),
            "red_flags_count": len(report.red_flags)
        })
        
        # Save report to file
        report_path = settings.reports_dir / f"{state['session_id']}_report.json"
        settings.reports_dir.mkdir(exist_ok=True)
        
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(final_report, f, indent=2, ensure_ascii=False)
        
        logger.log_info(f"Report saved to {report_path}")
        
        # Mark as complete
        state["should_continue"] = False
        if not state.get("termination_reason"):
            state["termination_reason"] = "report_synthesized"
        
    except Exception as e:
        logger.log_error("synthesize_report", e, {"state_keys": list(state.keys())})
        state["error_count"] = state.get("error_count", 0) + 1
        state["should_continue"] = False
        state["termination_reason"] = f"report_generation_error: {str(e)}"
        print(f"Synthesis error: {e}")
        raise
    
    return state

