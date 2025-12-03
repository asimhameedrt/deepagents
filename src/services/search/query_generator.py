"""Search query generation service using Claude for intelligent query refinement."""

from typing import List, Optional, Set, Dict, Any
from pydantic import BaseModel, Field

from ...config.settings import settings
from ...services.llm.claude_service import ClaudeService
from ...models.search_result import SearchQueriesList


class QueryGenerator:
    """Generates search queries using Claude with reflection-based consecutive search strategy."""
    
    def __init__(self, session_id: Optional[str] = None):
        """Initialize the query generator.
        
        Args:
            session_id: Session ID for logging
        """
        self.claude = ClaudeService(session_id=session_id)
        self.session_id = session_id
        self.max_queries = settings.max_queries_per_depth
    
    async def generate_initial_queries(
        self,
        subject: str,
        context: Optional[str] = None
    ) -> List[str]:
        """
        Generate initial broad queries for depth 0 research.
        
        Uses Claude to generate comprehensive initial queries covering:
        - Biographical basics
        - Professional history
        - Financial information
        - Legal/regulatory issues
        - Behavioral patterns
        
        Args:
            subject: Research subject
            context: Additional context about subject
            
        Returns:
            List of initial search queries
        """
        system_prompt = """You are an expert research strategist for Enhanced Due Diligence investigations.

Your task is to generate initial search queries that provide broad coverage of a subject.

For initial queries (Depth 0), focus on:
1. Biographical basics (background, education, early career)
2. Professional history (employment, roles, companies)
3. Financial information (net worth, investments, major transactions)
4. Legal/regulatory issues (lawsuits, investigations, compliance)
5. Behavioral patterns (associations, decision-making, public statements)

Generate specific, targeted queries that will retrieve high-quality information."""
        
        prompt = f"""# Initial Query Generation

Subject: {subject}
Context: {context or 'No additional context'}

Generate {self.max_queries} initial search queries for comprehensive due diligence research on this subject.

Queries should be:
- Specific and targeted (not generic)
- Diverse in coverage (different aspects of subject)
- Optimized for web search (natural language, specific terms)
- Focused on factual information (not opinion)

Return queries as a JSON list."""
        
        result = await self.claude.extract_structured(
            text=prompt,
            schema=SearchQueriesList,
            system_prompt=system_prompt
        )
        
        return result.get("queries", [f"{subject} background information"])
    
    async def generate_refined_queries(
        self,
        subject: str,
        reflection_memory: List[Dict[str, Any]],
        queries_executed: List[str],
        discovered_entities: Dict[str, Any],
        current_depth: int
    ) -> List[str]:
        """
        Generate refined queries based on reflection analysis.
        
        Uses latest reflection to:
        - Prioritize red flag topics
        - Explore suggested angles
        - Target new entities
        - Fill identified gaps
        - Avoid repeating previous queries
        
        Args:
            subject: Research subject
            reflection_memory: All reflection outputs
            queries_executed: Previously executed queries (for deduplication)
            discovered_entities: All discovered entities
            current_depth: Current search depth
            
        Returns:
            List of refined search queries
        """
        # Get latest reflection
        if not reflection_memory:
            # Fallback to initial queries
            return await self.generate_initial_queries(subject)
        
        latest_reflection = reflection_memory[-1]
        
        system_prompt = """You are an expert research strategist for Enhanced Due Diligence investigations.

Your task is to generate refined search queries based on previous findings and reflection analysis.

Key principles:
1. PRIORITIZE RED FLAGS: Focus on high-severity risks and concerning findings
2. EXPLORE NEW ENTITIES: Target newly discovered persons, organizations, events
3. FILL GAPS: Address identified information gaps
4. FOLLOW SUGGESTED ANGLES: Use strategic directions from reflection
5. AVOID REPETITION: Do not repeat or closely paraphrase previous queries
6. BE SPECIFIC: Target concrete facts, not general information

Generate queries that will uncover deeper intelligence and validate/refute red flags."""
        
        # Build context from reflection
        priority_topics = latest_reflection.get("priority_topics", [])
        suggested_angles = latest_reflection.get("suggested_angles", [])
        new_entities = latest_reflection.get("new_entities", [])
        identified_gaps = latest_reflection.get("identified_gaps", [])
        red_flags = latest_reflection.get("red_flags", [])
        
        prompt = f"""# Refined Query Generation (Depth {current_depth})

Subject: {subject}

## Previous Findings Summary
Total Queries Executed: {len(queries_executed)}
Entities Discovered: {len(discovered_entities)}
Red Flags: {len(red_flags)}

## Latest Reflection Analysis

### Priority Topics (Red Flags Prioritized)
{chr(10).join(f"- {topic}" for topic in priority_topics[:10])}

### Suggested Search Angles
{chr(10).join(f"- {angle}" for angle in suggested_angles[:5])}

### New Entities to Explore
{chr(10).join(f"- {entity}" for entity in new_entities[:10])}

### Identified Information Gaps
{chr(10).join(f"- {gap}" for gap in identified_gaps[:5])}

### Recent Queries (AVOID DUPLICATING)
{chr(10).join(f"- {q}" for q in queries_executed[-10:])}

## Your Task

Generate {self.max_queries} NEW search queries that:
1. Prioritize red flag topics and high-severity issues
2. Explore newly discovered entities in depth
3. Fill critical information gaps
4. Follow suggested angles
5. DO NOT repeat or closely paraphrase previous queries

Return as JSON list."""
        
        result = await self.claude.extract_structured(
            text=prompt,
            schema=SearchQueriesList,
            system_prompt=system_prompt
        )
        
        return result.get("queries", [])