"""
Claude service for risk analysis and structured extraction.

This module provides a high-level interface to Claude (Anthropic)
for analysis tasks that benefit from Claude's reasoning capabilities:
- Reflection and analysis
- Query generation and refinement
- Structured data extraction
"""

import time
from typing import Optional, Type

from anthropic import AsyncAnthropic
from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel

from ...config.settings import settings
from ...observability.detailed_logger import DetailedLogger


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
        
        # Initialize logger if session_id is provided
        self._logger = DetailedLogger(session_id) if session_id else None
    
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
        start_time = time.time()
        model = ChatAnthropic(
            model=self.model,
            temperature=0.1,
            max_tokens=16384,
            max_retries=2,
            timeout=10000,
        )
        
        messages = [
            ("system", system_prompt),
            ("human", text + "\n\n" + (instruction or "")),
        ]
                
        try:
            structured_model = model.with_structured_output(schema, method="json_schema")
            result: schema = structured_model.invoke(messages)
            duration_ms = (time.time() - start_time) * 1000
        except Exception as e:
            if self._logger:
                self._logger.log_error("extract_structured", e, {
                    "schema": schema.__name__,
                    "text_length": len(text)
                })
            raise e

        # Log LLM call if logger is available
        if self._logger:
            self._logger.log_llm_call(
                operation="extract_structured",
                model=self.model,
                input_data={"text": text, "schema": schema, "instruction": instruction, "system_prompt": system_prompt},
                output_data=result.model_dump(),
                duration_ms=duration_ms,
            )
        return result.model_dump()
