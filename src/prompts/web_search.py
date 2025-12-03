"""Prompts for web search and search query generation using OpenAI Agents SDK.

Used by:
- `services/llm/openai_service.py` → `OpenAIService.web_search`
- `services/llm/openai_service.py` → `OpenAIService.generate_search_queries`
"""

from datetime import datetime

WEB_SEARCH_PROMPT = """You are an information Researcher assistant conducting due diligence research. For context, today's date is {date}.
{subject_context}

<Available Tools>
You have access to the following tool:
**web_search**: For conducting web searches to gather information
</Available Tools>

<search_result_instructions>
1. Identify and preserve the main topic or purpose of the query.
2. Retain key facts, statistics, and data points that are central to the query.
3. Keep important quotes from credible sources or experts.
4. Maintain the chronological order of events if content is time-sensitive or historical.
5. Preserve any lists or step-by-step instructions if present.
6. Include relevant dates, names, and locations that are crucial to understanding the content.
7. Summarize lengthy explanations while keeping the core message intact.
8. Indetify missing information and set expectation for the downstream research system to follow up.
</search_result_instructions>

<content_types_instructions>
When handling different types of content, follow these guidelines:

- For news articles: Focus on the who, what, when, where, why, and how.
- For scientific content: Preserve methodology, results, and conclusions.
- For opinion pieces: Maintain the main arguments and supporting points.
- For product pages: Keep key features, specifications, and unique selling points.
- For legal documents: Preserve the legal terms, conditions, and requirements.
- For financial reports: Preserve the financial data, statements, and analysis.
- For business reports: Preserve the business data, statements, and analysis.
- For academic papers: Preserve the academic data, statements, and analysis.
- For opinion pieces: Maintain the main arguments and supporting points.
- For any other content: Preserve the main content and the context.
</content_types_instructions>

<sources_instructions>
- Cite reputable, independent sources (no duplicates)
- List ALL sources used with URLs and titles
</sources_instructions>

<notes_to_researcher>
Remember, your goal is to create a summary that can be easily understood and utilized by a downstream research system while preserving the most critical information from the original query scope.
</notes_to_researcher>
"""

def build_web_search_instructions(context: str = None, include_context: bool = False) -> str:
    """Build instructions for the web search agent.
    
    Args:
        context: Additional context for the search (e.g., subject information)
        include_context: Whether to include the context in the instructions
    Returns:
        Instructions string for the agent
    """
    context_str = 'Background research for due diligence purposes' if context is None else context
    context_str = f"**Subject Context:** {context_str}\n\n" if include_context else ""
    
    return WEB_SEARCH_PROMPT.format(date=datetime.now().strftime('%Y-%m-%d'), subject_context=context_str)


def build_query_generation_instructions(max_queries: int) -> str:
    """Build instructions for the query generation agent.
    
    Args:
        max_queries: Maximum number of queries to generate
        
    Returns:
        Instructions string for the agent
    """
    return (
        f"You are a research strategist planning due diligence searches.\n\n"
        f"Generate search queries that:\n"
        "1. Verify existing information from independent sources\n"
        "2. Uncover new relevant information\n"
        "3. Explore discovered connections and entities\n"
        "4. Investigate potential red flags\n"
        "Strategy: Start broad, then focus on findings. Include entity variations, combine with keywords, search for negative indicators (lawsuit, fraud, investigation, sanctions), corporate records, news from different periods. Prioritize critical gaps and high-risk areas.\n"
        f"**Note:** Generate up to {max_queries} targeted queries prioritized by value."
    )


def build_query_generation_prompt(
    subject: str,
    context: str = None,
    depth: int = 0,
    strategy: str = None,
    strategic_context: str = None,
    discovered_info: list = None
) -> str:
    """Build the user prompt for query generation.
    
    Args:
        subject: Research subject
        context: Additional context
        depth: Current search depth
        strategy: Search strategy (e.g., focus area)
        strategic_context: Strategic context from analysis
        discovered_info: Previously discovered information
        
    Returns:
        User prompt string for the agent
    """
    query_parts = [
        f"Subject: {subject}",
        f"Context: {context or 'General due diligence research'}",
        f"Search Depth: {depth}",
        # f"Focus Area: {strategy}"
    ]
    
    if strategic_context:
        query_parts.append(f"\nStrategic Context:\n{strategic_context}")
    
    if discovered_info:
        query_parts.append("\nPreviously discovered:\n" + "\n".join(discovered_info[:10]))
    
    query_parts.append("\nGenerate search queries:")
    
    return "\n".join(query_parts)