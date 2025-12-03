"""Claude service for risk analysis and report synthesis."""

import json
import time
from typing import List, Optional, Type

from anthropic import AsyncAnthropic, transform_schema
from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel
from ...observability.detailed_logger import DetailedLogger

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
        print("1.😄################################################################################")
        
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
        
        print("🚀 1")
        
        try:
            structured_model = model.with_structured_output(schema, method="json_schema")
            result: schema = structured_model.invoke(messages)
            duration_ms = (time.time() - start_time) * 1000
        except Exception as e:
            print(f"🚀 [Claude] Exception in extract_structured: {e}")
            raise e
        
        print(f"🚀 2 {result}")
        
        # print log values before logging for extra visibility
        print("🔍 Claude Extract Structured Log Information:")
        print(f"  - operation: extract_structured")
        print(f"  - model: {self.model}")
        print(f"  - input_data:")
        print(f"      text: {text}")
        print(f"      schema: {schema}")
        print(f"      instruction: {instruction}")
        # Truncate system_prompt for display if too long
        max_prompt_chars = 50
        sys_prompt_display = (system_prompt[:max_prompt_chars] + "...") if system_prompt and len(system_prompt) > max_prompt_chars else system_prompt
        print(f"      system_prompt: {sys_prompt_display}")
        print(f"  - output_data: {result.model_dump()}")
        print(f"  - duration_ms: {duration_ms}")

        # Log LLM call if logger is available
        if self._logger:
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
