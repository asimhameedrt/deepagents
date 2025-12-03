"""Search query generation service with enhanced dynamic refinement."""

from typing import List, Optional, Set, Dict, Any
from collections import Counter

from ...config.settings import settings
from ...services.llm.openai_service import OpenAIService
from ...models.search_result import SearchQueriesList


class QueryGenerator:
    """Generates search queries using intelligent consecutive search strategy."""
    
    def __init__(self, session_id: Optional[str] = None):
        """Initialize the query generator.
        
        Args:
            session_id: Session ID for logging
        """
        self.openai = OpenAIService(session_id=session_id)
        self.generated_queries: Set[str] = set()
        self.max_queries = settings.max_queries_per_depth
    
    async def generate_initial_queries(
        self,
        subject: str,
        context: Optional[str] = None
    ) -> List[str]:
        """
        Generate initial search queries for a subject.
        
        Args:
            subject: Research subject
            context: Additional context
            
        Returns:
            List of search queries
        """        
        if context:
            queries = [f"{subject} {context}"]
        else:
            queries = [f"{subject} background"]
        
        return queries