"""Claude service for risk analysis and report synthesis."""

import json
import time
from typing import List, Optional, Type

from anthropic import AsyncAnthropic, transform_schema
from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel

from ...config.settings import settings

class ClaudeService:
    """Service for interacting with Claude for analysis tasks."""
    
    def __init__(self, api_key: Optional[str] = None, session_id: Optional[str] = None):
        """Initialize the Claude service.
        
        Args:
            api_key: Anthropic API key (defaults to settings)
            session_id: Session ID for logging
        """
        self.client = AsyncAnthropic(api_key=api_key or settings.anthropic_api_key)
        self.model = settings.claude_model
        self.session_id = session_id
        
        # Lazy import to avoid circular dependency
        self._logger = None
    
    def _get_logger(self):
        """Get logger instance (lazy loaded)."""
        if self._logger is None and self.session_id:
            from ...observability.detailed_logger import DetailedLogger
            self._logger = DetailedLogger(self.session_id)
        return self._logger
    
    async def extract_structured(
        self,
        text: str,
        schema: Type[BaseModel],
        instruction: Optional[str] = None,
        system_prompt: Optional[str] = None
    ) -> BaseModel:
        """
        Extract structured data from text using Claude's structured outputs.
        Args:
            text: Text to extract from
            schema: Pydantic model schema to extract into
            instruction: Optional additional instructions
            system_prompt: Optional system prompt (defaults to extraction instructions)
            
        Returns:
            Instance of schema filled with extracted data
        """
        print("1.😄################################################################################")
        
        start_time = time.time()
        model = ChatAnthropic(
            model=self.model,
            temperature=0.1,
            max_tokens=16384,
            max_retries=2,
        )
        
        messages = [
            ("system", system_prompt),
            ("human", text + "\n\n" + (instruction or "")),
        ]
        
        structured_model = model.with_structured_output(schema, method="json_schema")
        result: schema = structured_model.invoke(messages)
        duration_ms = (time.time() - start_time) * 1000
        
        # log the result
        self._logger.log_llm_call(
            operation="extract_structured",
            model=self.model,
            input_data={"text": text, "schema": schema, "instruction": instruction, "system_prompt": system_prompt},
            output_data=result.model_dump(),
            duration_ms=duration_ms,
        )
        
        # use red emoji to indicate that the response is structured
        print("2.😄################################################################################")
        print(json.dumps(result.model_dump(), indent=2, ensure_ascii=False))
        print("😄################################################################################")
        return result.model_dump()
