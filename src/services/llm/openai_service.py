"""OpenAI service for web search and structured output using the Agents SDK."""

import os
import time
from typing import List, Optional

from agents import Agent, ModelSettings, Runner, RunConfig, WebSearchTool
from openai import AsyncOpenAI
from openai.types.responses.web_search_tool_param import UserLocation
from openai.types.shared.reasoning import Reasoning

from ...config.settings import settings
from ...models.search_result import (
    WebSearchOutput,
    WebSearchSource,
    SearchQueriesList,
)
from ...observability.detailed_logger import DetailedLogger
from ...prompts import (
    build_web_search_instructions,
    build_query_generation_instructions,
    build_query_generation_prompt,
)
from ...utils.helpers import extract_tokens


class OpenAIService:
    """Service for interacting with OpenAI models using the Agents SDK."""
    
    def __init__(self, api_key: Optional[str] = None, session_id: Optional[str] = None):
        """Initialize the OpenAI service.
        
        Args:
            api_key: OpenAI API key (defaults to settings)
            session_id: Session ID for logging
        """        
        self.client = AsyncOpenAI()
        self.search_model = settings.openai_search_model
        self.extraction_model = settings.openai_extraction_model
        self.session_id = session_id
        
        # Lazy import to avoid circular dependency
        self._logger = DetailedLogger(self.session_id)
    
    async def web_search(self, query: str, context: Optional[str] = None) -> WebSearchOutput:
        """Execute web search using OpenAI Agents SDK with structured output.
        
        Args:
            query: Search query
            context: Additional context for the search
            
        Returns:
            WebSearchOutput with findings and sources
        """
        agent = Agent(
            name="DueDiligenceResearcher",
            model=self.search_model,
            instructions=build_web_search_instructions(context, include_context=True),
            tools=[WebSearchTool(search_context_size="low", user_location=UserLocation(country="US", type="approximate"))],
            output_type=WebSearchOutput,
            model_settings=ModelSettings(verbosity="medium"),
        )
        
        start_time = time.time()
        result = await Runner.run(agent, query, run_config=RunConfig(tracing_disabled=True))
        extracted_tokens = await extract_tokens(result)
        duration_ms = (time.time() - start_time) * 1000
        
        output: WebSearchOutput = result.final_output
        
        print(f"Output: {output}")
        print("--------------------------------")
        print("\n"*10)
        
        # Convert structured output sources to Source objects
        sources = [WebSearchSource(url=src.url, title=src.title) for src in output.sources]
        
        self._logger.log_llm_call(
            operation="web_search",
            model=self.search_model,
            input_data={"query": query, "context": context},
            output_data={
                "search_result": output.search_result,
                "search_result_length": len(output.search_result),
                "sources_count": len(sources)
            },
            duration_ms=duration_ms,
            tokens=extracted_tokens
        )
        
        if not output.search_result:
            print(f"⚠️  Warning: Incomplete output for query: {query}")
        
        return output
    
    async def generate_search_queries(
        self,
        subject: str,
        context: Optional[str] = None,
        discovered_info: Optional[List[str]] = None,
        depth: int = 0,
        strategic_context: Optional[str] = None
    ) -> SearchQueriesList:
        """Generate search queries using OpenAI Agents SDK with structured output.
        
        Args:
            subject: Research subject
            context: Additional context
            discovered_info: Previously discovered information
            depth: Current search depth
            strategic_context: Strategic context from analysis
            
        Returns:
            SearchQueriesList with list of search queries
        """
        
        print(f"Building query generation agent with model: {self.search_model}")
        print("--------------------------------")
        
        agent = Agent(
            name="QueryStrategist",
            model=self.search_model,
            instructions=build_query_generation_instructions(settings.max_queries_per_depth),
            output_type=SearchQueriesList,
            # model_settings=ModelSettings(reasoning=Reasoning(effort="low"), verbosity="low"),
            model_settings=ModelSettings(verbosity="medium"),
        )
        
        try:
            start_time = time.time()
            user_prompt = build_query_generation_prompt(
                subject=subject,
                context=context,
                depth=depth,
                strategic_context=strategic_context,
                discovered_info=discovered_info
            )
            result = await Runner.run(agent, user_prompt, run_config=RunConfig(tracing_disabled=True))
            extracted_tokens = await extract_tokens(result)
            print(f"Extracted tokens: {extracted_tokens}")
            print("--------------------------------")
            
            duration_ms = (time.time() - start_time) * 1000
            
            output: SearchQueriesList = result.final_output
            print(f"Output: {output}")
            print(f"Output type: {type(output)}")
            print("--------------------------------")

            log_tokens = {
                "prompt": extracted_tokens.get("input_tokens", 0),
                "completion": extracted_tokens.get("output_tokens", 0),
                "total": extracted_tokens.get("total_tokens", 0),
                "cached": extracted_tokens.get("cached_tokens", 0),
                "reasoning": extracted_tokens.get("reasoning_tokens", 0),
            }
            
            self._logger.log_llm_call(
                operation="query_generation",
                model=self.search_model,
                input_data={"subject": subject, "depth": depth, "context": context},
                output_data={"queries": output.queries},
                duration_ms=duration_ms,
                tokens=log_tokens
            )
            
            return output
            
        except Exception as e:
            raise ValueError(f"Query generation failed: {str(e)}")

