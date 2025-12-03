"""Web search execution service."""

import asyncio
from typing import List, Optional

from ...models.search_result import WebSearchOutput
from ...services.llm.openai_service import OpenAIService


class SearchExecutor:
    """Executes web searches using OpenAI."""
    
    def __init__(self, session_id: Optional[str] = None):
        """Initialize the search executor.
        
        Args:
            session_id: Session ID for logging
        """
        self.openai = OpenAIService(session_id=session_id)
    
    async def search(
        self, 
        query: str,
        search_context: Optional[str] = None,
    ) -> WebSearchOutput:
        """
        Execute a web search with OpenAI's web search tool.
        
        Args:
            query: Search query
            search_context: Additional context for the search
            
        Returns:
            WebSearchOutput with search memory
        """
        # Execute search with OpenAI web search tool
        result = await self.openai.web_search(
            query=query,
            context=search_context,
        )
        
        return result
    
    async def parallel_search(
        self,
        queries: List[str],
        search_context: Optional[str] = None,
        max_concurrent: int = 5,
    ) -> List[WebSearchOutput]:
        """
        Execute multiple searches in parallel with concurrency limit.
        
        Args:
            queries: List of search queries
            search_context: Context for all searches
            max_concurrent: Maximum concurrent searches
            
        Returns:
            List of WebSearchOutputs
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def limited_search(query: str) -> WebSearchOutput:
            async with semaphore:
                return await self.search(
                    query=query,
                    search_context=search_context,
                )
        
        tasks = [limited_search(q) for q in queries]
        results = await asyncio.gather(*tasks)
        
        return results

